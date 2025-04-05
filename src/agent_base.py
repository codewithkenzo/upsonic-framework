"""
Base agent class for our framework.
"""

import uuid
from typing import List, Optional, Any, Dict, Union
import sys
sys.path.append(".")

# Define our own classes for now
class Task:
    """Simple task class."""
    
    def __init__(self, description, context=None):
        """Initialize a new task.
        
        Args:
            description (str): Description of the task.
            context (list, optional): Additional context for the task. Defaults to None.
        """
        self.description = description
        self.context = context or []
        
class KnowledgeBase:
    """Simple knowledge base class."""
    
    def __init__(self, sources):
        """Initialize a new knowledge base.
        
        Args:
            sources (list): List of source files or content dictionaries.
        """
        self.sources = sources

class Agent:
    """Agent class that uses LLMs."""
    
    def __init__(self, name, agent_id_=None, memory=False):
        """Initialize a new agent.
        
        Args:
            name (str): Name of the agent.
            agent_id_ (str, optional): ID of the agent. Defaults to None.
            memory (bool, optional): Whether to enable memory. Defaults to False.
        """
        self.name = name
        self.agent_id = agent_id_
        self.memory = memory
        self.conversation_history = []
        
        # Import here to avoid circular imports
        from src.llm_integration import LLMClient
        self.llm_client = LLMClient()
        
    def do(self, task, model=None):
        """Execute a task.
        
        Args:
            task (Task): The task to execute.
            model (str, optional): Model to use. Defaults to None.
            
        Returns:
            str: Result of the task execution.
        """
        # Add memory context if enabled
        if self.memory and self.conversation_history:
            memory_context = f"Previous conversation:\n{''.join(self.conversation_history)}"
            task.context.append(memory_context)
        
        # Process the task with the LLM
        try:
            result = self.llm_client.process_task(task, model_name=model)
            
            # Save to memory if enabled
            if self.memory:
                self.conversation_history.append(f"User: {task.description}\nAssistant: {result}\n\n")
                
            return result
        except Exception as e:
            # Fallback to simulation if LLM call fails
            error_msg = f"Error in LLM processing: {str(e)}"
            print(error_msg)
            return f"Simulated agent {self.name} executing task: {task.description} (LLM error)"

class BaseAgent:
    """Base agent class that will be extended by all other agents."""
    
    def __init__(
        self,
        name,
        description=None,
        model=None,
        enable_memory=True,
        agent_id=None,
        knowledge_base=None
    ):
        """Initialize a new agent.
        
        Args:
            name (str): The name of the agent.
            description (str, optional): Description of the agent's role. Defaults to None.
            model (str, optional): LLM model to use. Defaults to None (uses system default).
            enable_memory (bool, optional): Whether to enable agent memory. Defaults to True.
            agent_id (str, optional): Unique ID for the agent. If not provided, a random UUID will be generated.
            knowledge_base (KnowledgeBase, optional): Knowledge base for the agent. Defaults to None.
        """
        self.name = name
        self.description = description
        self.model = model
        
        # Generate a random agent_id if not provided
        self.agent_id = agent_id or f"{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        
        # Initialize the agent
        self.agent = Agent(
            self.name,
            agent_id_=self.agent_id,
            memory=enable_memory
        )
        
        # Store the knowledge base if provided
        self.knowledge_base = knowledge_base
        
    def execute_task(self, task_description, context=None):
        """Execute a task using this agent.
        
        Args:
            task_description (str): Description of the task to execute.
            context (list, optional): Additional context for the task. Defaults to None.
            
        Returns:
            str: Result of the task execution.
        """
        # Prepare context
        task_context = []
        
        # Add description as system prompt if available
        if self.description:
            task_context.append(f"You are {self.name}. {self.description}")
        
        # Add knowledge base to context if available
        if self.knowledge_base:
            task_context.append(self.knowledge_base)
            
        # Add additional context if provided
        if context:
            if isinstance(context, list):
                task_context.extend(context)
            else:
                task_context.append(context)
                
        # Create the task
        task = Task(
            task_description,
            context=task_context
        )
        
        # Execute the task with the agent
        if self.model:
            result = self.agent.do(task, model=self.model)
        else:
            result = self.agent.do(task)
            
        return result
        
    def direct_llm_call(self, task_description, context=None):
        """Make a direct LLM call without agent reasoning.
        
        Args:
            task_description (str): Description of the task for the LLM.
            context (list, optional): Additional context for the task. Defaults to None.
            
        Returns:
            str: Result of the direct LLM call.
        """
        # Import here to avoid circular imports
        from src.llm_integration import LLMClient
        llm_client = LLMClient()
        
        # Prepare context
        task_context = []
        
        # Add knowledge base to context if available
        if self.knowledge_base:
            task_context.append(self.knowledge_base)
            
        # Add additional context if provided
        if context:
            if isinstance(context, list):
                task_context.extend(context)
            else:
                task_context.append(context)
                
        # Create the task
        task = Task(
            task_description,
            context=task_context
        )
        
        # Make the direct LLM call
        try:
            return llm_client.process_task(task, model_name=self.model)
        except Exception as e:
            # Fallback to simulation if LLM call fails
            error_msg = f"Error in direct LLM call: {str(e)}"
            print(error_msg)
            return f"Simulated direct LLM call for task: {task_description} (LLM error)" 