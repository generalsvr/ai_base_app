# Agent Service Framework

A modular Python framework for building AI agent systems with pluggable tools and business logic services.

## Architecture

The Agent Service Framework is built on a modular architecture with the following key components:

### 1. Base Classes

- **Agent**: The core agent class that can be extended with tools and services
- **Tool**: Base class for all tools that agents can use (external integrations)
- **Service**: Base class for all business logic services that define agent behavior

### 2. Tools

Tools are external capabilities that agents can use to interact with the world:

- **SearchTool**: Enables web searches for information
- **KnowledgeBaseTool**: Retrieves information from a company knowledge base
- **EmailTool**: Sends emails to users
- **DataRetrievalTool**: Retrieves data from databases or APIs

### 3. Services

Services encapsulate business logic for specific use cases:

- **CustomerSupportService**: Provides customer support functionality
- **CodingAssistantService**: Provides coding help and programming assistance

## Directory Structure

```
agent_service/
├── base_agent.py         # Core base classes (Agent, Tool, Service)
├── tools.py              # Tool implementations
├── main.py               # Main service and example usage
├── services/
│   ├── customer_support.py   # Customer support business logic
│   └── coding_assistant.py   # Coding assistance business logic
└── README.md             # Documentation
```

## Key Features

- **Modular Design**: Easily add new tools and services without changing the core framework
- **Service Composition**: Agents can use multiple services for different types of requests
- **Tool Management**: Services declare which tools they need, and the framework ensures they're available
- **Clear Separation of Concerns**: Business logic is separated from technical integrations

## Usage Example

```python
import asyncio
from main import AgentService

async def example():
    # Create the agent service
    service = AgentService()
    
    # Create different types of agents
    support_agent = service.create_agent("SupportBot", ["CustomerSupport"])
    coding_agent = service.create_agent("CodeHelper", ["CodingAssistant"])
    multi_agent = service.create_agent("MultiAssistant", ["CustomerSupport", "CodingAssistant"])
    
    # Process a request with the customer support agent
    support_request = {
        "message": "I'm having trouble logging in to my account",
        "customer_id": 1
    }
    support_response = await service.process_request(support_agent, support_request)
    
    # Process a request with the coding agent
    coding_request = {
        "message": "How do I create a simple HTTP server in Python?"
    }
    coding_response = await service.process_request(coding_agent, coding_request)

if __name__ == "__main__":
    asyncio.run(example())
```

## Creating a New Service

1. Create a new file in the `services/` directory
2. Extend the `Service` base class
3. Implement the required methods:
   - `instructions`: Provide system instructions for the agent
   - `required_tools`: List the tools this service needs
   - `process_request`: Implement the business logic

Example:

```python
from typing import Dict, Any, List
from base_agent import Service

class MyNewService(Service):
    @property
    def instructions(self) -> str:
        return """
        Instructions for the agent on how to use this service.
        """
    
    @property
    def required_tools(self) -> List[str]:
        return ["ToolOne", "ToolTwo"]
    
    async def process_request(self, request: Dict[str, Any], agent: 'Agent') -> Dict[str, Any]:
        # Implement your business logic here
        # Use agent.execute_tool() to access tools
        pass
```

4. Register your service in `main.py`:

```python
def _register_available_services(self) -> Dict[str, type]:
    return {
        "CustomerSupport": CustomerSupportService,
        "CodingAssistant": CodingAssistantService,
        "MyNewService": MyNewService,  # Add your new service here
    }
```

## Creating a New Tool

1. Create a new tool class in `tools.py` or a dedicated file
2. Extend the `Tool` base class
3. Implement the required methods:
   - `description`: Provide a description of what the tool does
   - `execute`: Implement the tool's functionality

Example:

```python
from typing import Dict, Any
from base_agent import Tool

class MyNewTool(Tool):
    @property
    def description(self) -> str:
        return "Description of what my tool does."
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        # Implement your tool functionality here
        return {"success": True, "data": {...}}
```

4. Register your tool in `main.py`:

```python
def _register_available_tools(self) -> Dict[str, Tool]:
    return {
        "SearchTool": SearchTool(),
        "KnowledgeBaseTool": KnowledgeBaseTool(),
        "MyNewTool": MyNewTool(),  # Add your new tool here
    }
```

## Next Steps and Improvements

- Add an API layer (FastAPI/Flask) for HTTP access
- Implement proper authentication and user management
- Add persistent storage for agent state
- Integrate with language models (OpenAI, Claude, etc.)
- Add logging and observability features
- Create a web interface for interacting with agents 