from typing import Dict, Any, List
import re
from base_agent import Service

class CodingAssistantService(Service):
    """Service for providing coding assistance."""
    
    @property
    def instructions(self) -> str:
        return """
        You are a helpful coding assistant. Your goal is to help users with programming tasks,
        answer coding questions, and provide code examples.
        
        When responding to coding questions:
        1. Understand the user's programming language and context
        2. Provide clean, efficient, and well-commented code examples
        3. Explain your reasoning and approach
        4. If relevant, suggest best practices and potential improvements
        5. For complex questions, break down the problem into smaller steps
        6. When appropriate, search for relevant documentation and examples
        
        You can provide assistance with:
        - Debugging code issues
        - Writing new code or functions
        - Explaining programming concepts
        - Optimizing existing code
        - Suggesting libraries or tools
        - Providing code examples
        """
    
    @property
    def required_tools(self) -> List[str]:
        return ["SearchTool"]
    
    async def process_request(self, request: Dict[str, Any], agent: 'Agent') -> Dict[str, Any]:
        """Process a coding assistance request."""
        if 'message' not in request:
            return {
                "success": False,
                "message": "Request must include a 'message' field."
            }
        
        message = request['message']
        
        # Check if this is a request we can handle
        if not self._is_coding_request(message):
            raise NotImplementedError("Not a coding assistance request")
        
        # Extract programming language if mentioned
        language = self._extract_programming_language(message)
        
        # Determine if we need to search for documentation
        search_results = None
        if self._needs_documentation_search(message):
            search_query = self._build_search_query(message, language)
            search_results = await agent.execute_tool("SearchTool", query=search_query)
        
        # Determine the type of coding request
        request_type = self._determine_request_type(message)
        
        # Prepare response data
        response_data = {
            "success": True,
            "query": message,
            "language": language,
            "request_type": request_type,
            "search_results": search_results['data'] if search_results else None,
            "requires_code_generation": self._needs_code_generation(message)
        }
        
        return response_data
    
    def _is_coding_request(self, message: str) -> bool:
        """Determine if a message is a coding request."""
        coding_keywords = [
            "code", "function", "class", "method", "program", "script",
            "error", "bug", "debug", "compile", "syntax", "algorithm",
            "library", "framework", "api", "function", "variable",
            "python", "javascript", "java", "c++", "ruby", "go", "rust",
            "html", "css", "sql", "git", "react", "node", "django"
        ]
        return any(keyword.lower() in message.lower() for keyword in coding_keywords)
    
    def _extract_programming_language(self, message: str) -> str:
        """Extract the programming language from the message."""
        common_languages = {
            "python": ["python", "py", "django", "flask", "pandas", "numpy", "pytorch", "tensorflow"],
            "javascript": ["javascript", "js", "node", "nodejs", "react", "vue", "angular", "typescript", "ts"],
            "java": ["java", "spring", "jsp", "servlet", "maven", "gradle"],
            "c++": ["c++", "cpp", "c plus plus"],
            "ruby": ["ruby", "rails", "rb"],
            "go": ["golang", "go"],
            "rust": ["rust", "rs"],
            "php": ["php", "laravel", "symfony"],
            "c#": ["c#", "csharp", "dotnet", ".net", "asp.net"],
            "swift": ["swift", "ios"],
            "kotlin": ["kotlin", "android"],
            "html": ["html", "markup"],
            "css": ["css", "stylesheet", "sass", "scss"],
            "sql": ["sql", "mysql", "postgresql", "postgres", "oracle", "database"]
        }
        
        for language, keywords in common_languages.items():
            if any(keyword.lower() in message.lower() for keyword in keywords):
                return language
        
        return "unknown"
    
    def _needs_documentation_search(self, message: str) -> bool:
        """Determine if we should search for documentation."""
        documentation_patterns = [
            r"how (do|can|to)",
            r"what (is|are)",
            r"example",
            r"documentation",
            r"library",
            r"framework",
            r"api",
            r"function",
            r"usage",
            r"syntax"
        ]
        return any(re.search(pattern, message.lower()) for pattern in documentation_patterns)
    
    def _build_search_query(self, message: str, language: str) -> str:
        """Build a search query for documentation lookup."""
        # Extract key terms from the message
        words = message.lower().split()
        filler_words = ["i", "the", "a", "an", "of", "is", "are", "how", "what", "can"]
        query_terms = [word for word in words if word not in filler_words and len(word) > 2]
        
        # Add the programming language if known
        if language != "unknown":
            query_terms.insert(0, language)
        
        # Create the search query
        return " ".join(query_terms[:5])  # Use top 5 terms
    
    def _determine_request_type(self, message: str) -> str:
        """Determine the type of coding request."""
        if re.search(r"(fix|debug|error|bug|not working|doesn't work|issue)", message.lower()):
            return "debugging"
        elif re.search(r"(how to|how do|create|implement|build|make)", message.lower()):
            return "implementation"
        elif re.search(r"(explain|what is|what are|meaning|concept)", message.lower()):
            return "explanation"
        elif re.search(r"(optimize|improve|better|faster|efficient)", message.lower()):
            return "optimization"
        elif re.search(r"(recommend|suggest|best|library|tool|framework)", message.lower()):
            return "recommendation"
        else:
            return "general"
    
    def _needs_code_generation(self, message: str) -> bool:
        """Determine if the request requires generating code."""
        code_generation_patterns = [
            r"(write|generate|create|implement|code for)",
            r"(how (to|do) (implement|create|make))",
            r"(show me (the|some|an) (code|example))",
            r"(give me (a|an|the) (function|method|class))"
        ]
        return any(re.search(pattern, message.lower()) for pattern in code_generation_patterns) 