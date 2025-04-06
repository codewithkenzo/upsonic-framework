#!/usr/bin/env python3
"""
Unified MCP Chat Interface for interacting with multiple MCP servers through a single interface.
"""

import os
import sys
import json
import time
import asyncio
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from mcp_client import MCPClient
from mcp_registry import mcp_registry
from mcp_orchestrator import mcp_orchestrator
from llm_integration import LLMClient, get_model_config
from config.api_keys import OPENROUTER_API_KEY

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.style import Style
from rich.theme import Theme
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.spinner import Spinner
from rich.table import Table
from rich.box import ROUNDED

# Custom theme for the console
custom_theme = Theme({
    "user": "bold cyan",
    "assistant": "bold green",
    "system": "dim",
    "tool": "bold yellow",
    "loading": "bold magenta",
    "error": "bold red",
    "highlight": "bold cyan on dark_cyan",
    "server_name": "bold blue",
    "model_name": "bold purple",
    "orchestrator": "bold magenta",
    "workflow": "bold yellow",
})

console = Console(theme=custom_theme)

class UnifiedMCPChatInterface:
    """
    Unified CLI Chat interface for interacting with multiple MCP servers through orchestration.
    """
    
    def __init__(self, model_name: str = "claude-3.7-sonnet"):
        """
        Initialize the Unified MCP Chat Interface.
        
        Args:
            model_name (str, optional): Name of the LLM model to use
        """
        self.model_name = model_name
        
        # Set API key in environment
        os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY
        
        # Initialize orchestrator
        self.orchestrator = mcp_orchestrator
        self.orchestrator.model_name = model_name
        
        # Initialize state
        self.chat_history = []
        self.active_workflow = None
    
    async def start_chat(self):
        """Start the unified MCP chat interface."""
        # Get full model name with provider
        model_config = get_model_config(self.model_name)
        display_model = model_config["name"]
        
        # Get available servers
        available_servers = self.orchestrator.registry.get_all_servers()
        
        # Display welcome information
        console.print(Panel(f"[orchestrator]Connected to Unified MCP Orchestration System[/orchestrator]"))
        console.print(f"Using LLM model: [model_name]{display_model}[/model_name]")
        
        # Display available servers
        server_table = Table(title="Available MCP Servers", box=ROUNDED)
        server_table.add_column("Server", style="server_name")
        server_table.add_column("Description")
        server_table.add_column("Categories")
        server_table.add_column("Auto-start")
        
        for name, info in available_servers.items():
            server_table.add_row(
                name,
                info.get("description", "No description"),
                ", ".join(info.get("categories", [])),
                "Yes" if info.get("auto_start", False) else "No"
            )
        
        console.print(server_table)
        
        console.print("\n[highlight]Unified MCP Chat[/highlight]")
        console.print("This interface allows you to interact with multiple MCP servers through a single chat.")
        console.print("The system will intelligently route your queries to the appropriate server(s).")
        console.print("\nAvailable commands:")
        console.print("  [highlight]servers[/highlight] - List all available servers and their status")
        console.print("  [highlight]use server_name: query[/highlight] - Direct a query to a specific server")
        console.print("  [highlight]clear[/highlight] - Clear chat history")
        console.print("  [highlight]exit/quit[/highlight] - End the chat session")
        
        # Start the chat loop
        while True:
            # Get user input
            user_input = console.input("\n[user]You:[/user] ")
            
            # Handle exit commands
            if user_input.lower() in ["exit", "quit"]:
                console.print("[system]Exiting chat...[/system]")
                break
            
            # Handle clear command
            if user_input.lower() == "clear":
                self.chat_history = []
                console.print("[system]Chat history cleared.[/system]")
                continue
            
            # Handle servers command
            if user_input.lower() == "servers":
                active_servers = await self.orchestrator.list_active_servers()
                
                server_table = Table(title="MCP Servers Status", box=ROUNDED)
                server_table.add_column("Server", style="server_name")
                server_table.add_column("Status")
                server_table.add_column("Description")
                server_table.add_column("Tools/Capabilities")
                
                for name, info in available_servers.items():
                    status = "[green]Active[/green]" if name in active_servers else "[dim]Inactive[/dim]"
                    capabilities = ", ".join(info.get("capabilities", [])[:3])
                    if len(info.get("capabilities", [])) > 3:
                        capabilities += "..."
                    
                    server_table.add_row(
                        name,
                        status,
                        info.get("description", "No description"),
                        capabilities
                    )
                
                console.print(server_table)
                continue
            
            # Add user message to history
            self.chat_history.append({"role": "user", "content": user_input})
            
            # Process the message with progress spinner
            with Progress(
                SpinnerColumn(spinner_name="dots"),
                TextColumn("[loading]Processing query...[/loading]"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("", total=None)
                try:
                    response = await self.process_message(user_input)
                except Exception as e:
                    console.print(f"[error]Error processing query:[/error] {str(e)}")
                    continue
            
            # Extract information about servers used
            servers_used = response.get("servers_used", [])
            response_type = response.get("type", "single")
            response_content = response.get("response", "")
            
            # Handle failed responses
            if response.get("status") == "error":
                console.print(f"\n[error]Error:[/error]")
                try:
                    console.print(Panel(Markdown(response_content), border_style="red"))
                except:
                    console.print(Panel(response_content, border_style="red"))
                continue
            
            # Create header based on response type
            if response_type == "meta":
                header = "[orchestrator]System Response:[/orchestrator]"
                border_style = "blue"
            elif response_type == "orchestration":
                servers_str = ", ".join(f"[server_name]{s}[/server_name]" for s in servers_used)
                header = f"[orchestrator]Orchestrated Response (using {servers_str}):[/orchestrator]"
                border_style = "yellow"
            elif response_type == "direct":
                header = f"[server_name]Response from {servers_used[0]}:[/server_name]"
                border_style = "green"
            else:
                if servers_used and len(servers_used) > 0:
                    header = f"[server_name]Response from {servers_used[0]}:[/server_name]"
                    border_style = "green"
                else:
                    header = "[assistant]Assistant:[/assistant]"
                    border_style = "green"
            
            # Display the response with appropriate formatting
            console.print(f"\n{header}")
            
            # Check for tool usage in the response
            tool_usage = False
            for server in servers_used:
                server_info = available_servers.get(server, {})
                for capability in server_info.get("capabilities", []):
                    if capability.lower() in response_content.lower():
                        tool_usage = True
                        break
                if tool_usage:
                    break
            
            # Create response panel with appropriate styling
            try:
                # Try rendering as markdown
                response_panel = Panel(
                    Markdown(response_content),
                    border_style=border_style,
                    title="Tool-Enhanced Response" if tool_usage else None,
                    subtitle=f"Using {', '.join(servers_used)}" if servers_used else None
                )
                console.print(response_panel)
            except Exception as e:
                # Fallback to plain text
                console.print(Panel(
                    response_content,
                    border_style=border_style,
                    title="Tool-Enhanced Response" if tool_usage else None
                ))
            
            # Add assistant message to history
            self.chat_history.append({
                "role": "assistant", 
                "content": response_content,
                "metadata": {
                    "servers_used": servers_used,
                    "response_type": response_type
                }
            })
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process a user message through the orchestrator.
        
        Args:
            message (str): The user message
            
        Returns:
            Dict[str, Any]: The orchestrator response
        """
        # Process through the central chat interface of the orchestrator
        return await self.orchestrator.central_chat(message, self.chat_history)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Unified MCP chat interface")
    parser.add_argument("--model", help="Name of the LLM model to use", default="claude-3.7-sonnet")
    
    args = parser.parse_args()
    
    chat_interface = UnifiedMCPChatInterface(model_name=args.model)
    
    # Run the async chat interface
    asyncio.run(chat_interface.start_chat())

if __name__ == "__main__":
    main() 