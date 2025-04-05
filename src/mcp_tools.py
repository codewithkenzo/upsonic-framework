"""
Module for interacting with MCP (Model Context Protocol) tools and servers.
"""

import sys
import importlib
from typing import Dict, List, Any, Optional

# Import config
sys.path.append(".")
from config.mcp_config import get_mcp_server_config

class MCPToolManager:
    """Manager for MCP tools and servers."""
    
    def __init__(self, server_name=None):
        """Initialize the MCP tool manager.
        
        Args:
            server_name (str, optional): Name of the MCP server to use.
                If not provided, the default server will be used.
        """
        # Get the MCP server configuration
        self.server_config = get_mcp_server_config(server_name)
        self.server_name = self.server_config.get("name")
        self.tools_cache = {}
        
    def list_available_tools(self) -> List[str]:
        """List all available tools on the MCP server.
        
        Returns:
            List[str]: List of available tool names.
        """
        # In a real implementation, this would query the MCP server for available tools
        # For now, we'll return a placeholder list for the desktop commander
        if "desktop_commander" in self.server_config.get("url", ""):
            return [
                "execute_command",
                "read_output",
                "force_terminate",
                "list_sessions",
                "list_files",
                "read_file",
                "write_file",
                "delete_file",
                "move_file",
                "copy_file"
            ]
        return []
        
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute an MCP tool.
        
        Args:
            tool_name (str): Name of the tool to execute.
            **kwargs: Arguments to pass to the tool.
            
        Returns:
            Any: Result of the tool execution.
        """
        # In a real implementation, this would call the MCP server to execute the tool
        # For now, we'll just return a placeholder result
        return {
            "status": "success",
            "result": f"Executed {tool_name} with arguments: {kwargs}",
            "tool": tool_name
        }
        
    def get_tool_description(self, tool_name: str) -> Optional[str]:
        """Get the description of an MCP tool.
        
        Args:
            tool_name (str): Name of the tool to get description for.
            
        Returns:
            Optional[str]: Description of the tool, or None if not found.
        """
        # In a real implementation, this would query the MCP server for the tool description
        # For now, we'll return placeholder descriptions for the desktop commander tools
        descriptions = {
            "execute_command": "Execute a terminal command.",
            "read_output": "Read output from a running terminal session.",
            "force_terminate": "Force terminate a running terminal session.",
            "list_sessions": "List all active terminal sessions.",
            "list_files": "List files in a directory.",
            "read_file": "Read the contents of a file.",
            "write_file": "Write contents to a file.",
            "delete_file": "Delete a file.",
            "move_file": "Move a file from one location to another.",
            "copy_file": "Copy a file from one location to another."
        }
        return descriptions.get(tool_name)
        
class MCPToolAgent:
    """Agent for working with MCP tools."""
    
    def __init__(self, base_agent, mcp_manager=None):
        """Initialize the MCP tool agent.
        
        Args:
            base_agent: The base agent to use for tasks.
            mcp_manager (MCPToolManager, optional): MCP tool manager to use.
                If not provided, a new manager will be created.
        """
        self.base_agent = base_agent
        self.mcp_manager = mcp_manager or MCPToolManager()
        
    def execute_tool_task(self, tool_name, **kwargs):
        """Execute a task using an MCP tool.
        
        Args:
            tool_name (str): Name of the tool to use.
            **kwargs: Arguments to pass to the tool.
            
        Returns:
            Any: Result of the tool execution.
        """
        # Check if the tool exists
        if tool_name not in self.mcp_manager.list_available_tools():
            raise ValueError(f"Unknown tool: {tool_name}")
            
        # Execute the tool
        result = self.mcp_manager.execute_tool(tool_name, **kwargs)
        
        return result
        
    def execute_with_reasoning(self, task_description, tool_name, **kwargs):
        """Execute a task with the agent reasoning about how to use the MCP tool.
        
        Args:
            task_description (str): Description of the task to execute.
            tool_name (str): Name of the tool to use.
            **kwargs: Arguments to pass to the tool.
            
        Returns:
            dict: Result containing both the agent's reasoning and the tool execution result.
        """
        # Get the tool description
        tool_description = self.mcp_manager.get_tool_description(tool_name)
        
        # Create a reasoning task for the agent
        reasoning_task = f"""
        Task: {task_description}
        
        You need to use the '{tool_name}' tool to complete this task.
        Tool description: {tool_description}
        
        Available parameters for this tool:
        {kwargs}
        
        Explain your reasoning for how to use this tool effectively for the task.
        """
        
        # Get the agent's reasoning
        reasoning = self.base_agent.execute_task(reasoning_task)
        
        # Execute the tool
        tool_result = self.execute_tool_task(tool_name, **kwargs)
        
        return {
            "reasoning": reasoning,
            "tool_result": tool_result
        } 