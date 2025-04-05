"""
Main module for the Upsonic agent framework.
"""

import sys
sys.path.append(".")

from src.agent_base import BaseAgent, Task, KnowledgeBase
from src.mcp_tools import MCPToolManager, MCPToolAgent
from src.parallel_tasks import ParallelTaskExecutor
from src.knowledge_manager import KnowledgeManager
from src.persistence import AgentStore
from src.browser_agent import BrowserAgent

from config.llm_config import get_model_config
from config.mcp_config import get_mcp_server_config

class AgentFramework:
    """Main class for the Upsonic agent framework."""
    
    def __init__(self):
        """Initialize the agent framework."""
        # Initialize managers and tools
        self.knowledge_manager = KnowledgeManager()
        self.mcp_manager = MCPToolManager()
        self.parallel_executor = ParallelTaskExecutor()
        self.agent_store = AgentStore()
        
        # Load agents from storage
        self.agents = {}
        self._load_agents()
        
    def _load_agents(self):
        """Load agents from storage."""
        # Get the list of agent IDs from storage
        agent_infos = self.agent_store.list_agents()
        
        # Load each agent
        for agent_id in agent_infos:
            agent = self.agent_store.load_agent(agent_id)
            if agent:
                self.agents[agent_id] = agent
        
    def create_agent(
        self,
        name,
        description=None,
        model_name=None,
        enable_memory=True,
        agent_id=None,
        knowledge_base=None
    ):
        """Create a new agent.
        
        Args:
            name (str): The name of the agent.
            description (str, optional): Description of the agent's role. Defaults to None.
            model_name (str, optional): Name of the LLM model to use. Defaults to None.
            enable_memory (bool, optional): Whether to enable agent memory. Defaults to True.
            agent_id (str, optional): Unique ID for the agent. If not provided, a random UUID will be generated.
            knowledge_base (KnowledgeBase, optional): Knowledge base for the agent. Defaults to None.
            
        Returns:
            BaseAgent: The created agent.
        """
        # Get the model configuration
        model = None
        if model_name:
            model_config = get_model_config(model_name)
            model = model_config.get("model")
            
        # Create the agent
        agent = BaseAgent(
            name=name,
            description=description,
            model=model,
            enable_memory=enable_memory,
            agent_id=agent_id,
            knowledge_base=knowledge_base
        )
        
        # Register the agent
        self.agents[agent.agent_id] = agent
        
        # Save the agent to storage
        self.agent_store.save_agent(agent.agent_id, agent)
        
        return agent
        
    def create_mcp_agent(
        self,
        name,
        description=None,
        model_name=None,
        mcp_server_name=None,
        enable_memory=True,
        agent_id=None,
        knowledge_base=None
    ):
        """Create a new agent that can use MCP tools.
        
        Args:
            name (str): The name of the agent.
            description (str, optional): Description of the agent's role. Defaults to None.
            model_name (str, optional): Name of the LLM model to use. Defaults to None.
            mcp_server_name (str, optional): Name of the MCP server to use. Defaults to None.
            enable_memory (bool, optional): Whether to enable agent memory. Defaults to True.
            agent_id (str, optional): Unique ID for the agent. If not provided, a random UUID will be generated.
            knowledge_base (KnowledgeBase, optional): Knowledge base for the agent. Defaults to None.
            
        Returns:
            MCPToolAgent: The created MCP tool agent.
        """
        # Create the base agent
        base_agent = self.create_agent(
            name=name,
            description=description,
            model_name=model_name,
            enable_memory=enable_memory,
            agent_id=agent_id,
            knowledge_base=knowledge_base
        )
        
        # Create an MCP manager for the agent
        mcp_manager = MCPToolManager(mcp_server_name)
        
        # Create the MCP tool agent
        mcp_agent = MCPToolAgent(base_agent, mcp_manager)
        
        return mcp_agent
        
    def create_browser_agent(
        self,
        name,
        description=None,
        model_name=None,
        enable_memory=True,
        agent_id=None,
        knowledge_base=None,
        headless=False
    ):
        """Create a new agent that can browse the web using Playwright.
        
        Args:
            name (str): The name of the agent.
            description (str, optional): Description of the agent's role. Defaults to None.
            model_name (str, optional): Name of the LLM model to use. Defaults to None.
            enable_memory (bool, optional): Whether to enable agent memory. Defaults to True.
            agent_id (str, optional): Unique ID for the agent. If not provided, a random UUID will be generated.
            knowledge_base (KnowledgeBase, optional): Knowledge base for the agent. Defaults to None.
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to False.
            
        Returns:
            BrowserAgent: The created browser agent.
        """
        # Get the model configuration
        model = None
        if model_name:
            model_config = get_model_config(model_name)
            model = model_config.get("model")
            
        # Create the browser agent
        agent = BrowserAgent(
            name=name,
            description=description,
            model=model,
            enable_memory=enable_memory,
            agent_id=agent_id,
            knowledge_base=knowledge_base,
            headless=headless
        )
        
        # Register the agent
        self.agents[agent.agent_id] = agent
        
        # Save the agent to storage
        self.agent_store.save_agent(agent.agent_id, agent)
        
        return agent
        
    def run_parallel_tasks(self, agent_tasks):
        """Run multiple agent tasks in parallel.
        
        Args:
            agent_tasks (List[Dict]): List of dictionaries containing agent and task information.
                Each dictionary should have the following keys:
                - 'agent': The agent to use for the task.
                - 'task': The task description or Task object.
                - 'context' (optional): Additional context for the task.
                
        Returns:
            List[Any]: List of results from the tasks.
        """
        return self.parallel_executor.execute_tasks(agent_tasks)
        
    async def run_parallel_tasks_async(self, agent_tasks):
        """Run multiple agent tasks in parallel using asyncio.
        
        Args:
            agent_tasks (List[Dict]): List of dictionaries containing agent and task information.
                Each dictionary should have the following keys:
                - 'agent': The agent to use for the task.
                - 'task': The task description or Task object.
                - 'context' (optional): Additional context for the task.
                
        Returns:
            List[Any]: List of results from the tasks.
        """
        return await self.parallel_executor.execute_tasks_async(agent_tasks)
        
    def get_agent(self, agent_id):
        """Get an agent by ID.
        
        Args:
            agent_id (str): ID of the agent to get.
            
        Returns:
            BaseAgent: The agent with the given ID, or None if not found.
        """
        # Check if the agent is already loaded
        if agent_id in self.agents:
            return self.agents[agent_id]
            
        # Try to load the agent from storage
        agent = self.agent_store.load_agent(agent_id)
        if agent:
            # Register the agent
            self.agents[agent_id] = agent
            
        return agent
        
    def delete_agent(self, agent_id):
        """Delete an agent.
        
        Args:
            agent_id (str): ID of the agent to delete.
            
        Returns:
            bool: True if the agent was deleted, False otherwise.
        """
        # Check if the agent exists
        if agent_id not in self.agents:
            # Try to load the agent from storage
            agent = self.agent_store.load_agent(agent_id)
            if not agent:
                return False
                
        # Remove the agent from the registry
        if agent_id in self.agents:
            del self.agents[agent_id]
            
        # Delete the agent from storage
        return self.agent_store.delete_agent(agent_id)
        
# Create a singleton instance
framework = AgentFramework() 