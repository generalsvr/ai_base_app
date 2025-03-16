from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Tool(ABC):
    """Base class for all tools that agents can use."""
    
    @property
    def name(self) -> str:
        """Name of the tool."""
        return self.__class__.__name__
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with the given parameters."""
        pass


class Service(ABC):
    """Base class for all business logic services."""
    
    @property
    def name(self) -> str:
        """Name of the service."""
        return self.__class__.__name__
    
    @property
    @abstractmethod
    def instructions(self) -> str:
        """Instructions for the agent on how to use this service."""
        pass
    
    @property
    @abstractmethod
    def required_tools(self) -> List[str]:
        """List of tool names required by this service."""
        pass
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any], agent: 'Agent') -> Dict[str, Any]:
        """Process a request using this service."""
        pass


class Agent:
    """Base agent class that can be extended with different services."""
    
    def __init__(self, name: str):
        self.name = name
        self.tools: Dict[str, Tool] = {}
        self.services: Dict[str, Service] = {}
        self.system_instructions = f"You are {name}, an AI assistant."
    
    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent."""
        self.tools[tool.name] = tool
    
    def add_service(self, service: Service) -> None:
        """Add a service to the agent."""
        # Check if all required tools are available
        missing_tools = [tool for tool in service.required_tools if tool not in self.tools]
        if missing_tools:
            raise ValueError(f"Service {service.name} requires tools {missing_tools} which are not available")
        
        self.services[service.name] = service
        # Extend system instructions with service instructions
        self.system_instructions += f"\n\n{service.instructions}"
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        return await self.tools[tool_name].execute(**kwargs)
    
    async def process_request(self, request: Dict[str, Any], service_name: str = None) -> Dict[str, Any]:
        """Process a request using a specific service or all services."""
        if service_name:
            if service_name not in self.services:
                raise ValueError(f"Service {service_name} not found")
            return await self.services[service_name].process_request(request, self)
        
        # If no service specified, try each service until one handles it
        for service in self.services.values():
            try:
                return await service.process_request(request, self)
            except NotImplementedError:
                continue
        
        raise ValueError("No service could handle the request")
    
    def get_instructions(self) -> str:
        """Get the full system instructions for this agent."""
        return self.system_instructions 