#!/usr/bin/env python3
"""
MCP Orchestrator for coordinating multiple MCP servers and workflows.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from pathlib import Path

# Add current directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_client import MCPClient
from mcp_registry import mcp_registry
from llm_integration import LLMClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_orchestrator")

class MCPOrchestrator:
    """
    Orchestrates multiple MCP servers, intelligently routing requests and coordinating workflows.
    Acts as a central control point for all MCP interactions.
    """
    
    def __init__(self, model_name: str = "claude-3.7-sonnet"):
        """
        Initialize the MCP Orchestrator.
        
        Args:
            model_name (str, optional): Name of the LLM model to use for orchestration
        """
        self.model_name = model_name
        self.mcp_client = MCPClient()
        
        # Set API key in environment if needed
        if "OPENROUTER_API_KEY" in os.environ:
            self.llm_client = LLMClient()
        else:
            from config.api_keys import OPENROUTER_API_KEY
            os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
            self.llm_client = LLMClient()
        
        # Initialize workflow state
        self.current_workflow = None
        self.workflow_context = {}
        self.active_servers = set()
        
        # Load the MCP registry
        self.registry = mcp_registry
        logger.info(f"MCP Orchestrator initialized with {len(self.registry.get_all_servers())} available servers")
    
    async def start_server(self, server_name: str) -> Dict[str, Any]:
        """
        Start an MCP server.
        
        Args:
            server_name (str): Name of the server to start
            
        Returns:
            Dict[str, Any]: Status information
        """
        if server_name not in self.registry.get_all_servers():
            logger.warning(f"Unknown server: {server_name}")
            return {"status": "error", "message": f"Unknown server: {server_name}"}
        
        result = self.mcp_client.start_server(server_name)
        
        if result.get("status") == "started" or result.get("status") == "already_running":
            self.active_servers.add(server_name)
            logger.info(f"Started MCP server: {server_name}")
            return {"status": "success", "message": f"Server {server_name} started successfully"}
        else:
            logger.error(f"Failed to start server {server_name}: {result}")
            return {"status": "error", "message": f"Failed to start server: {result}"}
    
    async def stop_server(self, server_name: str) -> Dict[str, Any]:
        """
        Stop an MCP server.
        
        Args:
            server_name (str): Name of the server to stop
            
        Returns:
            Dict[str, Any]: Status information
        """
        if server_name not in self.active_servers:
            logger.warning(f"Server not active: {server_name}")
            return {"status": "error", "message": f"Server not active: {server_name}"}
        
        result = self.mcp_client.stop_server(server_name)
        
        if result.get("status") == "stopped":
            self.active_servers.remove(server_name)
            logger.info(f"Stopped MCP server: {server_name}")
            return {"status": "success", "message": f"Server {server_name} stopped successfully"}
        else:
            logger.error(f"Failed to stop server {server_name}: {result}")
            return {"status": "error", "message": f"Failed to stop server: {result}"}
    
    async def list_active_servers(self) -> List[str]:
        """
        List all currently active MCP servers.
        
        Returns:
            List[str]: List of active server names
        """
        return list(self.active_servers)
    
    async def route_query(self, query: str) -> Dict[str, Any]:
        """
        Intelligently route a natural language query to the appropriate MCP server(s).
        
        Args:
            query (str): The natural language query
            
        Returns:
            Dict[str, Any]: Result including server used and response
        """
        logger.info(f"Routing query: {query}")
        
        # First, check if any server names or capabilities are directly mentioned in the query
        query_lower = query.lower()
        direct_server_match = None
        server_scores = {}
        
        for name, info in self.registry.get_all_servers().items():
            score = 0
            
            # Check if server name is mentioned directly
            if name.lower() in query_lower:
                score += 5
            
            # Check for capability mentions
            for capability in info.get("capabilities", []):
                if capability.lower() in query_lower:
                    score += 2
            
            # Check for category mentions
            for category in info.get("categories", []):
                if category.lower() in query_lower:
                    score += 1
            
            # Store the score if positive
            if score > 0:
                server_scores[name] = score
        
        # If we found direct matches, use the highest scoring ones
        if server_scores:
            # Sort servers by score
            sorted_servers = sorted(server_scores.items(), key=lambda x: x[1], reverse=True)
            top_score = sorted_servers[0][1]
            
            # Get all servers with the top score
            top_servers = [name for name, score in sorted_servers if score == top_score]
            
            logger.info(f"Direct mention match found for servers: {top_servers}")
            
            # If multiple servers have the same top score, use all of them
            if len(top_servers) > 1:
                workflow_result = await self.execute_workflow(top_servers, query)
                
                return {
                    "status": "success",
                    "servers": top_servers,
                    "response": workflow_result,
                    "query": query,
                    "workflow": True
                }
            # Otherwise use the single top-scoring server
            else:
                server_name = top_servers[0]
                
                # Start the server if it's not active
                if server_name not in self.active_servers:
                    await self.start_server(server_name)
                
                result = await self.process_with_server(server_name, query)
                
                return {
                    "status": "success",
                    "server": server_name,
                    "response": result,
                    "query": query
                }
        
        # If no direct matches, use the LLM for more sophisticated routing
        # Prepare routing prompt
        servers_info = []
        for name, info in self.registry.get_all_servers().items():
            capabilities = ", ".join(info.get("capabilities", []))
            categories = ", ".join(info.get("categories", []))
            servers_info.append(f"- {name}: {info.get('description', '')}. Categories: {categories}. Capabilities: {capabilities}")
        
        servers_str = "\n".join(servers_info)
        
        routing_prompt = f"""I need to determine which MCP server(s) would be most appropriate for this user query:

USER QUERY: "{query}"

Available MCP servers and their capabilities:
{servers_str}

IMPORTANT INSTRUCTIONS:
1. Analyze the query to determine which server(s) would be best suited to handle it
2. Consider the purpose, capabilities, and categories of each server
3. Select the SINGLE most appropriate server if one clearly fits best
4. Only select MULTIPLE servers if the query truly requires coordination between them
5. Be precise and practical - only choose servers that will directly help with the query

Respond with ONLY the name of the single most appropriate server, or multiple server names separated by commas if coordination is essential.
DO NOT include any explanations or additional text.
"""

        # Get routing decision from LLM
        routing_response = self.llm_client.generate(routing_prompt, model_name=self.model_name)
        
        # Parse the response to get server name(s)
        # Clean up the response to handle any extra text the LLM might add
        cleaned_response = routing_response.strip().split('\n')[0].strip()
        server_names = [name.strip() for name in cleaned_response.split(",")]
        
        # Filter out any invalid server names or extra text
        valid_servers = [name for name in server_names if name in self.registry.get_all_servers()]
        
        if not valid_servers:
            logger.warning(f"No valid servers identified for query: {query}")
            return {
                "status": "error",
                "message": "No appropriate server found for this query",
                "query": query
            }
        
        logger.info(f"Selected servers for query: {valid_servers}")
        
        # For single server routing
        if len(valid_servers) == 1:
            server_name = valid_servers[0]
            
            # Start the server if it's not active
            if server_name not in self.active_servers:
                result = await self.start_server(server_name)
                if result.get("status") != "success":
                    return {
                        "status": "error",
                        "message": f"Failed to start server {server_name}",
                        "query": query
                    }
            
            # Process the query with the server
            try:
                result = await self.process_with_server(server_name, query)
                
                return {
                    "status": "success",
                    "server": server_name,
                    "response": result,
                    "query": query
                }
            except Exception as e:
                logger.error(f"Error processing query with server {server_name}: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Error processing query with server {server_name}: {str(e)}",
                    "query": query
                }
        
        # For multi-server orchestration
        else:
            try:
                workflow_result = await self.execute_workflow(valid_servers, query)
                
                return {
                    "status": "success",
                    "servers": valid_servers,
                    "response": workflow_result,
                    "query": query,
                    "workflow": True
                }
            except Exception as e:
                logger.error(f"Error executing workflow with servers {valid_servers}: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Error executing workflow: {str(e)}",
                    "query": query
                }
    
    async def process_with_server(self, server_name: str, query: str) -> str:
        """
        Process a query with a specific MCP server.
        
        Args:
            server_name (str): Name of the server to use
            query (str): The query to process
            
        Returns:
            str: The response from the server
        """
        # Ensure server is started
        if server_name not in self.active_servers:
            start_result = await self.start_server(server_name)
            if start_result.get("status") != "success":
                return f"Error: Failed to start the {server_name} server. Please try again or use a different server."
        
        # Get available tools
        try:
            available_tools = []
            
            # Different ways to retrieve available tools
            if hasattr(self.mcp_client, '_mcp_manager'):
                available_tools = self.mcp_client._mcp_manager.list_available_tools(server_name)
            else:
                # Try to get tools from server info
                server_info = self.registry.get_server_info(server_name)
                if server_info and "capabilities" in server_info:
                    available_tools = server_info["capabilities"]
            
            # If still no tools available, try direct server query
            if not available_tools:
                server_status = self.mcp_client.get_server_status(server_name)
                if "tools" in server_status:
                    available_tools = server_status["tools"]
        except Exception as e:
            logger.error(f"Error getting tools for {server_name}: {str(e)}")
            available_tools = []
        
        # Prepare system message with tools information
        tools_str = "\n".join([f"- {tool}" for tool in available_tools])
        
        server_context = self.registry.get_server_info(server_name) or {}
        server_description = server_context.get("description", f"MCP server for {server_name}")
        
        system_message = f"""You are an AI assistant that has access to the following tools from the {server_name} MCP server:

{tools_str}

Server description: {server_description}

IMPORTANT INSTRUCTIONS:
1. When using a tool, ALWAYS clearly indicate which tool you're using by saying "Using {server_name}:<tool_name>"
2. Format your responses with Markdown for better readability
3. Be direct and practical in your responses, focusing on providing useful information
4. Try to use the tools to accomplish the user's request directly rather than just explaining what you could do
5. If asked to perform a task and you have the tools to do it, use them immediately
"""
        
        # Process the query with the LLM
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ]
        
        response = self.llm_client.generate(json.dumps(messages), model_name=self.model_name)
        
        # Process the response to better highlight tool usage
        processed_response = response
        
        # Add server attribution if not present
        if server_name.lower() not in processed_response.lower():
            processed_response = f"## Response from {server_name} server\n\n{processed_response}"
        
        return processed_response
    
    async def execute_workflow(self, servers: List[str], query: str) -> str:
        """
        Execute a multi-server workflow for complex queries.
        
        Args:
            servers (List[str]): List of servers to use in the workflow
            query (str): The query to process
            
        Returns:
            str: The response from the workflow execution
        """
        # Start all required servers
        started_servers = []
        for server_name in servers:
            if server_name not in self.active_servers:
                start_result = await self.start_server(server_name)
                if start_result.get("status") == "success":
                    started_servers.append(server_name)
                else:
                    logger.warning(f"Failed to start server {server_name} for workflow")
        
        # If we couldn't start any servers, fall back to the first one
        if not started_servers and len(servers) > 0:
            logger.warning(f"Falling back to server {servers[0]} only")
            return await self.process_with_server(servers[0], query)
        
        # Prepare orchestration prompt with detailed tools information
        servers_info = []
        servers_tools = {}
        
        for name in servers:
            info = self.registry.get_server_info(name)
            if info:
                capabilities = ", ".join(info.get("capabilities", []))
                servers_info.append(f"- {name}: {info.get('description', '')}. Capabilities: {capabilities}")
                
                # Get available tools for this server
                try:
                    if hasattr(self.mcp_client, '_mcp_manager'):
                        tools = self.mcp_client._mcp_manager.list_available_tools(name)
                    else:
                        tools = info.get("capabilities", [])
                    
                    servers_tools[name] = tools
                except Exception as e:
                    logger.error(f"Error getting tools for {name}: {str(e)}")
                    servers_tools[name] = info.get("capabilities", [])
        
        servers_str = "\n".join(servers_info)
        
        # Create a detailed tools section
        tools_section = []
        for server_name, tools in servers_tools.items():
            tools_section.append(f"## {server_name} Server Tools:")
            for tool in tools:
                tools_section.append(f"- {tool}")
            tools_section.append("")
        
        tools_details = "\n".join(tools_section)
        
        # Create more practical workflow prompt
        orchestration_prompt = f"""I need to address this user query by coordinating multiple MCP servers:

USER QUERY: "{query}"

Available MCP servers:
{servers_str}

Available tools for each server:
{tools_details}

IMPORTANT INSTRUCTIONS:
1. Create a step-by-step plan that uses these servers to answer the query
2. For each step, specify which server to use and which tool to call
3. Be PRACTICAL and DIRECT - focus on actually solving the user's request
4. When referring to a tool, use the format "server_name:tool_name"
5. Include specific parameters for each tool call when known
6. For web searches and browsing, include exact URLs or search terms
7. Don't just create a theoretical workflow - incorporate actual results where possible

Your response should be formatted like this:
1. First explain briefly what you'll do to address the query
2. Then show each step with the server+tool being used and what it accomplishes
3. Where possible, show actual results from the first server in the workflow

Begin with the most important/relevant server for addressing the core of the query.
"""

        # Get workflow plan from LLM
        workflow_response = self.llm_client.generate(orchestration_prompt, model_name=self.model_name)
        
        # In a future implementation, we would parse this workflow and execute each step
        # For now, let's try to improve the response's practicality by adding the first server's direct response
        
        # Get the first server's response to the query to make it more practical
        if len(servers) > 0:
            try:
                first_server = servers[0]
                first_response = await self.process_with_server(first_server, query)
                
                # Only add the first server's response if it's not already included
                if first_server.lower() not in workflow_response.lower():
                    workflow_response += f"\n\n## Initial Results from {first_server}\n\n{first_response}"
            except Exception as e:
                logger.error(f"Error getting first server response: {str(e)}")
        
        return f"""# Multi-Server Workflow

{workflow_response}
"""
    
    async def central_chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process a message through the central chat interface that can orchestrate multiple servers.
        
        Args:
            message (str): The user message
            history (List[Dict[str, str]], optional): Chat history
            
        Returns:
            Dict[str, Any]: Response including orchestration information
        """
        if history is None:
            history = []
        
        # Check for direct server commands
        command_servers = {}
        
        for server_name in self.registry.get_all_servers().keys():
            if message.lower().startswith(f"use {server_name}:"):
                # Direct server command format: "use server_name: actual query"
                actual_message = message[len(f"use {server_name}:"):].strip()
                response = await self.process_with_server(server_name, actual_message)
                
                return {
                    "status": "success",
                    "type": "direct",
                    "response": response,
                    "servers_used": [server_name]
                }
        
        # Handle special commands
        if message.lower() in ["servers", "list servers", "show servers"]:
            servers_info = []
            for name, info in self.registry.get_all_servers().items():
                status = "Active" if name in self.active_servers else "Inactive"
                description = info.get("description", "No description")
                capabilities = ", ".join(info.get("capabilities", []))
                servers_info.append(f"- **{name}** ({status}): {description}\n  Capabilities: {capabilities}")
            
            response = f"""# Available MCP Servers

{chr(10).join(servers_info)}

To use a specific server directly, start your message with:
"use server_name: your query"
"""
            return {
                "status": "success",
                "type": "meta",
                "response": response,
                "servers_used": []
            }
        
        # Check if this message contains explicit tool references
        tool_pattern = r'\b(mcp_[a-z_]+|web_search|playwright|hackernews|github|browse|click|scrape)\b'
        import re
        potential_tools = re.findall(tool_pattern, message.lower())
        
        if potential_tools:
            # This appears to be a tool-oriented message, determine server by tools
            tool_servers = {}
            
            # Map tools to servers
            for server_name, info in self.registry.get_all_servers().items():
                for capability in info.get("capabilities", []):
                    for potential_tool in potential_tools:
                        if potential_tool.lower() in capability.lower():
                            if server_name not in tool_servers:
                                tool_servers[server_name] = 0
                            tool_servers[server_name] += 1
            
            # If we identified servers for the tools, use them
            if tool_servers:
                # Sort servers by relevance (number of tool matches)
                sorted_servers = sorted(tool_servers.items(), key=lambda x: x[1], reverse=True)
                selected_servers = [name for name, count in sorted_servers]
                
                # If multiple servers are equally relevant, use a workflow
                if len(selected_servers) > 1 and sorted_servers[0][1] == sorted_servers[1][1]:
                    workflow_result = await self.execute_workflow(selected_servers, message)
                    
                    return {
                        "status": "success",
                        "type": "orchestration",
                        "response": workflow_result,
                        "servers_used": selected_servers
                    }
                # Otherwise use the most relevant server
                else:
                    primary_server = selected_servers[0]
                    response = await self.process_with_server(primary_server, message)
                    
                    return {
                        "status": "success",
                        "type": "single",
                        "response": response,
                        "servers_used": [primary_server]
                    }
        
        # For messages without clear server/tool references, try to route intelligently
        logger.info("No direct server/tool references detected, routing intelligently")
        
        # Define categories of queries and sample prompts for each
        query_categories = {
            "web_browsing": ["browse", "navigate", "open website", "click", "scrape", "webpage"],
            "research": ["search", "find information", "look up", "research", "article"],
            "data_retrieval": ["get data", "retrieve", "fetch", "database", "records"],
            "coding": ["code", "github", "repository", "programming", "developer"]
        }
        
        # Determine query category by keyword matching
        category_scores = {}
        for category, keywords in query_categories.items():
            score = sum(1 for keyword in keywords if keyword.lower() in message.lower())
            category_scores[category] = score
        
        # Get the highest scoring category
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            
            # If we have a category with score > 0
            if best_category[1] > 0:
                category_name = best_category[0]
                
                # Get servers for this category
                category_servers = []
                
                # Check for direct category mapping
                if category_name in self.registry.server_categories:
                    category_servers = self.registry.get_servers_by_category(category_name)
                
                # If no direct mapping, try to find related servers
                if not category_servers:
                    for server_name, info in self.registry.get_all_servers().items():
                        server_categories = info.get("categories", [])
                        
                        # Check if any server category contains our category name
                        if any(category_name in cat.lower() for cat in server_categories):
                            category_servers.append(server_name)
                
                # If we found servers for this category
                if category_servers:
                    if len(category_servers) > 1:
                        # Multiple servers for this category, use a workflow
                        workflow_result = await self.execute_workflow(category_servers, message)
                        
                        return {
                            "status": "success",
                            "type": "orchestration",
                            "response": workflow_result,
                            "servers_used": category_servers
                        }
                    else:
                        # Single server for this category
                        response = await self.process_with_server(category_servers[0], message)
                        
                        return {
                            "status": "success",
                            "type": "single",
                            "response": response,
                            "servers_used": category_servers
                        }
        
        # If we couldn't route by category, fall back to LLM-based routing
        result = await self.route_query(message)
        
        if result.get("status") == "success":
            response_type = "orchestration" if result.get("workflow", False) else "single"
            servers_used = result.get("servers", [result.get("server")] if result.get("server") else [])
            
            return {
                "status": "success",
                "type": response_type,
                "response": result.get("response", ""),
                "servers_used": servers_used
            }
        else:
            # If routing failed, return a helpful error
            return {
                "status": "error",
                "type": "meta",
                "response": """# No Suitable Server Found

I couldn't determine which MCP server would be appropriate for your query. 

You can:
1. Try rephrasing your query to be more specific
2. Type "servers" to see a list of available servers
3. Directly specify a server with "use server_name: your query"
""",
                "servers_used": []
            }

# Create a singleton instance
mcp_orchestrator = MCPOrchestrator() 