#!/usr/bin/env python3
"""
Main entry point for the Upsonic agent framework.

This script provides a simple CLI interface to interact with the framework.
"""

import sys
import asyncio
import argparse
from src.main import framework
from src.agent_base import Task
from src.llm_integration import LLMClient

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Upsonic Agent Framework")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create agent command
    create_parser = subparsers.add_parser("create", help="Create a new agent")
    create_parser.add_argument("name", help="Name of the agent")
    create_parser.add_argument("--description", help="Description of the agent")
    create_parser.add_argument("--model", help="Model to use", default="llama3-70b")
    create_parser.add_argument("--memory", help="Enable memory", action="store_true")
    
    # Run task command
    task_parser = subparsers.add_parser("task", help="Run a task with an agent")
    task_parser.add_argument("agent_id", help="ID of the agent to use")
    task_parser.add_argument("task", help="Task description")
    
    # Direct LLM call command
    direct_parser = subparsers.add_parser("direct", help="Make a direct LLM call")
    direct_parser.add_argument("prompt", help="Prompt for the LLM")
    direct_parser.add_argument("--model", help="Model to use", default="llama3-70b")
    direct_parser.add_argument("--image", action="append", help="Path to an image file to analyze (can be specified multiple times)")
    
    # Browser command
    browser_parser = subparsers.add_parser("browser", help="Create a browser agent and browse a website")
    browser_parser.add_argument("url", help="URL to browse")
    browser_parser.add_argument("--task", help="Task to perform on the webpage")
    browser_parser.add_argument("--name", help="Name of the agent", default="Browser Agent")
    browser_parser.add_argument("--description", help="Description of the agent")
    browser_parser.add_argument("--model", help="Model to use", default="gpt-4o")
    browser_parser.add_argument("--headless", help="Run browser in headless mode", action="store_true")
    
    # List agents command
    subparsers.add_parser("list", help="List all agents")
    
    # Delete agent command
    delete_parser = subparsers.add_parser("delete", help="Delete an agent")
    delete_parser.add_argument("agent_id", help="ID of the agent to delete")
    
    return parser.parse_args()

async def browser_command(args):
    """Execute browser command."""
    # Create a browser agent
    browser_agent = framework.create_browser_agent(
        name=args.name,
        description=args.description or f"An agent that browses {args.url}",
        model_name=args.model,
        enable_memory=True,
        headless=args.headless
    )
    
    print(f"Created browser agent with ID: {browser_agent.agent_id}")
    
    # Browse to the URL
    print(f"Browsing to {args.url}...")
    result = await browser_agent.browse(args.url)
    
    if result["status"] == "success":
        print(f"Successfully loaded page: {result['title']}")
        
        # Extract text content
        content_result = await browser_agent.get_page_text()
        if content_result["status"] == "success":
            # Take a screenshot
            screenshot_result = await browser_agent.take_screenshot()
            print(f"Screenshot saved to: {screenshot_result['path']}")
            
            # If a task was specified, perform it
            if args.task:
                print("\nExecuting task...")
                summary = browser_agent.execute_browsing_task(args.task)
                print(f"\nResult: {summary}")
        else:
            print(f"Error extracting content: {content_result['error']}")
    else:
        print(f"Error browsing to {args.url}: {result['error']}")
    
    # Close the browser
    await browser_agent.stop()
    print("Browser closed.")

def main():
    """Main entry point."""
    args = parse_args()
    
    if args.command == "create":
        # Create a new agent
        agent = framework.create_agent(
            name=args.name,
            description=args.description,
            model_name=args.model,
            enable_memory=args.memory
        )
        print(f"Agent created with ID: {agent.agent_id}")
        
    elif args.command == "task":
        # Run a task with an agent
        agent = framework.get_agent(args.agent_id)
        if agent is None:
            print(f"Agent with ID {args.agent_id} not found")
            return
            
        result = agent.execute_task(args.task)
        print(f"\nResult: {result}")
        
    elif args.command == "direct":
        # Make a direct LLM call using the LLM client
        llm_client = LLMClient()
        
        # Create and process the task
        task = Task(args.prompt)
        result = llm_client.process_task(task, model_name=args.model, image_paths=args.image)
        print(f"\nResult: {result}")
        
    elif args.command == "browser":
        # Run the browser command asynchronously
        asyncio.run(browser_command(args))
        
    elif args.command == "list":
        # List all agents
        if not framework.agents:
            print("No agents created yet")
            return
            
        print("Agents:")
        for agent_id, agent in framework.agents.items():
            print(f"  - {agent.name} ({agent_id})")
            
    elif args.command == "delete":
        # Delete an agent
        success = framework.delete_agent(args.agent_id)
        if success:
            print(f"Agent with ID {args.agent_id} deleted")
        else:
            print(f"Agent with ID {args.agent_id} not found")
            
    else:
        print("No command specified. Use --help for usage information.")

if __name__ == "__main__":
    main() 