import asyncio
import logging
from typing import Dict, Any, Optional, List

from base_agent import Agent, Tool, Service
from tools import SearchTool, KnowledgeBaseTool, EmailTool, DataRetrievalTool
from services.customer_support import CustomerSupportService
from services.coding_assistant import CodingAssistantService
from services.romantic_chat import RomanticChatService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentService:
    """Main service for creating and managing agents."""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.available_tools: Dict[str, Tool] = self._register_available_tools()
        self.available_services: Dict[str, type] = self._register_available_services()
        
    def _register_available_tools(self) -> Dict[str, Tool]:
        """Register all available tools."""
        # Initialize mock data for tools
        kb_data = {
            "product_features": "Our product offers advanced AI capabilities, integration with various platforms, and 24/7 support.",
            "pricing": "We offer three pricing tiers: Basic ($10/month), Pro ($25/month), and Enterprise (custom pricing).",
            "refund_policy": "We offer a 30-day money-back guarantee on all our plans.",
            "technical_requirements": "Our software requires Windows 10+ or macOS 10.15+, 4GB RAM, and 1GB free disk space.",
            "api_documentation": "API documentation is available at https://api.example.com/docs",
        }
        
        customer_data = [
            {"id": 1, "name": "John Doe", "email": "john@example.com", "plan": "Pro", "signup_date": "2023-01-15"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "plan": "Enterprise", "signup_date": "2023-02-20"},
            {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "plan": "Basic", "signup_date": "2023-03-10"}
        ]
        
        data_sources = {
            "customers": customer_data,
            "products": [
                {"id": 1, "name": "Basic Plan", "price": 10, "features": ["Core functionality", "Email support"]},
                {"id": 2, "name": "Pro Plan", "price": 25, "features": ["Advanced features", "Priority support", "API access"]},
                {"id": 3, "name": "Enterprise Plan", "price": "Custom", "features": ["All features", "Dedicated support", "Custom integration"]}
            ],
            "orders": [
                {"id": 101, "customer_id": 1, "product_id": 2, "date": "2023-01-15", "status": "completed"},
                {"id": 102, "customer_id": 2, "product_id": 3, "date": "2023-02-20", "status": "completed"},
                {"id": 103, "customer_id": 3, "product_id": 1, "date": "2023-03-10", "status": "completed"}
            ]
        }
        
        return {
            "SearchTool": SearchTool(),
            "KnowledgeBaseTool": KnowledgeBaseTool(kb_data),
            "EmailTool": EmailTool(),
            "DataRetrievalTool": DataRetrievalTool(data_sources)
        }
    
    def _register_available_services(self) -> Dict[str, type]:
        """Register all available service classes."""
        return {
            "CustomerSupport": CustomerSupportService,
            "CodingAssistant": CodingAssistantService,
            "RomanticChat": RomanticChatService,
            # Add more services here as they are implemented
        }
    
    def create_agent(self, name: str, service_names: List[str]) -> str:
        """Create a new agent with specified services."""
        if name in self.agents:
            raise ValueError(f"Agent with name '{name}' already exists")
        
        agent = Agent(name)
        
        # Add all tools to the agent
        for tool_name, tool in self.available_tools.items():
            agent.add_tool(tool)
        
        # Add requested services
        for service_name in service_names:
            if service_name not in self.available_services:
                raise ValueError(f"Unknown service: {service_name}")
            
            service_class = self.available_services[service_name]
            service = service_class()
            agent.add_service(service)
        
        self.agents[name] = agent
        logger.info(f"Created agent '{name}' with services: {service_names}")
        return name
    
    async def process_request(self, agent_name: str, request: Dict[str, Any], 
                              service_name: Optional[str] = None) -> Dict[str, Any]:
        """Process a request using the specified agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        agent = self.agents[agent_name]
        
        try:
            return await agent.process_request(request, service_name)
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_agent_instructions(self, agent_name: str) -> str:
        """Get the instructions for a specific agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        return self.agents[agent_name].get_instructions()


async def main():
    """Example usage of the agent service."""
    # Create the agent service
    service = AgentService()
    
    # Create a customer support agent
    support_agent = service.create_agent("SupportBot", ["CustomerSupport"])
    
    # Create a coding assistant agent
    coding_agent = service.create_agent("CodeHelper", ["CodingAssistant"])
    
    # Create a romantic chat agent
    romantic_agent = service.create_agent("RomanceBot", ["RomanticChat"])
    
    # Create a multi-service agent
    multi_agent = service.create_agent("MultiAssistant", ["CustomerSupport", "CodingAssistant"])
    
    # Print agent instructions
    print(f"\nAgent '{support_agent}' instructions:")
    print(service.get_agent_instructions(support_agent))
    
    print(f"\nAgent '{coding_agent}' instructions:")
    print(service.get_agent_instructions(coding_agent))
    
    print(f"\nAgent '{romantic_agent}' instructions:")
    print(service.get_agent_instructions(romantic_agent))
    
    print(f"\nAgent '{multi_agent}' instructions:")
    print(service.get_agent_instructions(multi_agent))
    
    # Example customer support request
    support_request = {
        "message": "I'm having trouble logging in to my account. Can you help?",
        "customer_id": 1
    }
    
    print(f"\nProcessing support request: {support_request}")
    support_response = await service.process_request(support_agent, support_request)
    print(f"\nSupport Response: {support_response}")
    
    # Example coding request
    coding_request = {
        "message": "How do I create a simple HTTP server in Python?"
    }
    
    print(f"\nProcessing coding request: {coding_request}")
    coding_response = await service.process_request(coding_agent, coding_request)
    print(f"\nCoding Response: {coding_response}")
    
    # Example romantic chat request
    romantic_request = {
        "message": "Hi there! How are you today? I'm feeling happy today!",
        "user_state": {
            "name": "Alex",
            "interests": ["music", "hiking", "movies"]
        }
    }
    
    print(f"\nProcessing romantic chat request: {romantic_request}")
    romantic_response = await service.process_request(romantic_agent, romantic_request)
    print(f"\nRomantic Chat Response: {romantic_response}")
    
    # Test multi-service agent with a coding request
    print(f"\nProcessing coding request with multi-service agent: {coding_request}")
    multi_coding_response = await service.process_request(multi_agent, coding_request)
    print(f"\nMulti-service Coding Response: {multi_coding_response}")


if __name__ == "__main__":
    asyncio.run(main()) 