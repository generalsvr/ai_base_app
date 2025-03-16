from typing import Dict, Any, List
import re
from base_agent import Service

class CustomerSupportService(Service):
    """Service for handling customer support inquiries."""
    
    @property
    def instructions(self) -> str:
        return """
        You are a helpful customer support agent. Your goal is to assist customers with their inquiries
        and resolve their issues efficiently and professionally.
        
        When responding to customers:
        1. Greet them politely
        2. Show empathy for their problem
        3. Provide clear, concise answers
        4. Offer solutions whenever possible
        5. Use the knowledge base to find relevant information
        6. If you need to look up customer data, use the data retrieval tool
        7. For complex issues, offer to escalate to a human agent
        
        Common customer issues:
        - Product information inquiries
        - Billing and payment issues
        - Technical support
        - Return and refund requests
        - Account management
        """
    
    @property
    def required_tools(self) -> List[str]:
        return ["KnowledgeBaseTool", "DataRetrievalTool", "EmailTool"]
    
    async def process_request(self, request: Dict[str, Any], agent: 'Agent') -> Dict[str, Any]:
        """Process a customer support request."""
        if 'message' not in request:
            return {
                "success": False,
                "message": "Request must include a 'message' field."
            }
        
        message = request['message']
        customer_id = request.get('customer_id')
        
        # Check if this is a request we can handle
        if not self._is_customer_support_request(message):
            raise NotImplementedError("Not a customer support request")
        
        # Get customer information if ID is provided
        customer_info = None
        if customer_id:
            customer_data_result = await agent.execute_tool(
                "DataRetrievalTool", 
                source="customers", 
                filters={"id": customer_id}
            )
            if customer_data_result['success'] and customer_data_result['count'] > 0:
                customer_info = customer_data_result['data'][0]
        
        # Check if we need to search the knowledge base
        kb_results = None
        if self._needs_knowledge_lookup(message):
            kb_query = self._extract_query_terms(message)
            kb_results = await agent.execute_tool("KnowledgeBaseTool", query=kb_query)
        
        # Prepare response data
        response_data = {
            "success": True,
            "customer_info": customer_info,
            "knowledge_results": kb_results['data'] if kb_results else None,
            "query": message,
            "requires_human": self._needs_human_escalation(message)
        }
        
        # Send confirmation email for specific request types
        if self._is_ticket_creation_request(message) and customer_info and 'email' in customer_info:
            await agent.execute_tool(
                "EmailTool",
                to=customer_info['email'],
                subject="Your Support Request Has Been Received",
                body=f"Dear {customer_info.get('name', 'Customer')},\n\nThank you for contacting our support team. Your request has been received and a support agent will respond to you shortly.\n\nRegards,\nCustomer Support Team"
            )
            response_data["email_sent"] = True
        
        return response_data
    
    def _is_customer_support_request(self, message: str) -> bool:
        """Determine if a message is a customer support request."""
        # Simple heuristic - in a real system this would be more sophisticated
        support_keywords = [
            "help", "support", "issue", "problem", "question", "refund",
            "broken", "doesn't work", "how do I", "can't", "error"
        ]
        return any(keyword in message.lower() for keyword in support_keywords)
    
    def _needs_knowledge_lookup(self, message: str) -> bool:
        """Determine if we should look up information in the knowledge base."""
        question_patterns = [
            r"how (do|can|to)",
            r"what (is|are)",
            r"where (is|are)",
            r"when (is|are)",
            r"\?$"
        ]
        return any(re.search(pattern, message.lower()) for pattern in question_patterns)
    
    def _extract_query_terms(self, message: str) -> str:
        """Extract search terms from the message for knowledge base lookup."""
        # Remove common filler words - in a real system this would use NLP
        filler_words = ["i", "the", "a", "an", "of", "is", "are", "was", "were", "be", "been"]
        words = message.lower().split()
        query_terms = [word for word in words if word not in filler_words and len(word) > 2]
        return " ".join(query_terms[:5])  # Use top 5 terms
    
    def _needs_human_escalation(self, message: str) -> bool:
        """Determine if the request needs to be escalated to a human agent."""
        escalation_triggers = [
            "speak to a human",
            "speak to an agent",
            "talk to a person",
            "talk to a representative",
            "real person",
            "supervisor",
            "manager",
            "frustrated",
            "angry",
            "immediately"
        ]
        return any(trigger in message.lower() for trigger in escalation_triggers)
    
    def _is_ticket_creation_request(self, message: str) -> bool:
        """Determine if this request should create a support ticket."""
        # Typically most requests would create tickets, except very simple inquiries
        return len(message.split()) > 10  # Simple heuristic 