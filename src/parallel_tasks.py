"""
Module for parallel task execution.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Any, Dict, Union

from src.agent_base import Task

class ParallelTaskExecutor:
    """Executor for running tasks in parallel."""
    
    def __init__(self, max_workers=None):
        """Initialize a new parallel task executor.
        
        Args:
            max_workers (int, optional): Maximum number of worker threads.
                If not provided, the default ThreadPoolExecutor behavior is used.
        """
        self.max_workers = max_workers
        
    def execute_tasks(self, agent_tasks: List[Dict]) -> List[Any]:
        """Execute multiple agent tasks in parallel.
        
        Args:
            agent_tasks (List[Dict]): List of dictionaries containing agent and task information.
                Each dictionary should have the following keys:
                - 'agent': The agent to use for the task.
                - 'task': The task description or Task object.
                - 'context' (optional): Additional context for the task.
                
        Returns:
            List[Any]: List of results from the tasks.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create a list of future objects for each task
            futures = []
            
            for task_info in agent_tasks:
                agent = task_info['agent']
                task_desc = task_info['task']
                context = task_info.get('context')
                
                # Create a Task object if a string was provided
                if isinstance(task_desc, str):
                    task = Task(task_desc, context=context)
                else:
                    task = task_desc
                    
                # Submit the task to the executor
                future = executor.submit(self._execute_single_task, agent, task)
                futures.append(future)
                
            # Wait for all futures to complete and get results
            results = [future.result() for future in futures]
            
        return results
        
    def _execute_single_task(self, agent, task):
        """Execute a single task with the given agent.
        
        Args:
            agent: The agent to use for the task.
            task: The Task object to execute.
            
        Returns:
            Any: Result of the task execution.
        """
        return agent.agent.do(task)
        
    async def execute_tasks_async(self, agent_tasks: List[Dict]) -> List[Any]:
        """Execute multiple agent tasks in parallel using asyncio.
        
        Args:
            agent_tasks (List[Dict]): List of dictionaries containing agent and task information.
                Each dictionary should have the following keys:
                - 'agent': The agent to use for the task.
                - 'task': The task description or Task object.
                - 'context' (optional): Additional context for the task.
                
        Returns:
            List[Any]: List of results from the tasks.
        """
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create tasks for each agent_task
            tasks = []
            
            for task_info in agent_tasks:
                agent = task_info['agent']
                task_desc = task_info['task']
                context = task_info.get('context')
                
                # Create a Task object if a string was provided
                if isinstance(task_desc, str):
                    task = Task(task_desc, context=context)
                else:
                    task = task_desc
                    
                # Create an asyncio task
                async_task = loop.run_in_executor(
                    executor, 
                    self._execute_single_task, 
                    agent, 
                    task
                )
                tasks.append(async_task)
                
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)
            
        return results 