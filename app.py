#!/usr/bin/env python3
"""
Command line interface for the Upsonic agent framework.
"""

import os
import sys
import time
import argparse
import asyncio
from pathlib import Path
import psutil

sys.path.append(".")

# Load environment variables from .env file if it exists
env_file = Path(".env")
if env_file.exists():
    with open(env_file, "r") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

from src.main import AgentFramework
from src.llm_integration import LLMClient, get_model_config
from src.cli.tui_enhancements import (
    console, 
    print_banner, 
    create_progress_bar,
    run_with_spinner, 
    display_hierarchical_list,
    display_agent_info,
    display_code,
    Timer,
    select_from_list,
    display_image_selection,
    Panel,
    display_system_dashboard,
    update_agent_stats,
    update_task_stats,
    SYMBOLS,
    setup_interrupt_handler
)
from rich.table import Table
from rich.box import ROUNDED

# Import FastMCP module
try:
    from fastmcp import FastMCP, Context
except ImportError:
    pass

# Create the agent framework
framework = AgentFramework()

# Initialize global variables
system_stats = {
    "cpu_usage": 0,
    "memory_usage": 0,
    "memory_used": 0,
    "memory_total": 0,
    "disk_usage": 0,
    "disk_used": 0, 
    "disk_total": 0,
    "net_sent": 0,
    "net_recv": 0
}

state = {
    "start_time": time.time(),
    "system": {
        "cpu": 0,
        "memory": 0,
        "uptime": 0
    },
    "agents": {
        "active": 0,
        "inactive": 0,
        "total": 0
    },
    "tasks": {
        "running": 0,
        "completed": 0,
        "failed": 0,
        "total": 0
    }
}

# Unicode symbols for CLI display
SYMBOLS = {
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "loading": "⟳",
    "agent": "👤",
    "task": "🔄",
    "active": "🟢",
    "inactive": "🔴",
    "arrow_right": "▶",
    "cpu": "📊",
    "memory": "💾"
}

# Terminal colors

def format_agent_list(agents):
    """Format agent list for display."""
    formatted_agents = []
    active_count = 0
    inactive_count = 0
    
    for agent_id, info in agents.items():
        # Determine if agent is active (a simple simulation for now)
        # In a real implementation, we'd check if the agent is currently processing tasks
        agent = framework.get_agent(agent_id)
        is_active = hasattr(agent, 'browser') and agent.browser is not None
        
        status = "active" if is_active else "inactive"
        if is_active:
            active_count += 1
        else:
            inactive_count += 1
            
        formatted_agents.append({
            "name": info.get("name", "Unknown"),
            "description": info.get("description", "No description"),
            "agent_id": agent_id,
            "status": status,
            "model": getattr(agent, "model", "None"),
            "memory_enabled": getattr(agent, "enable_memory", False)
        })
    
    # Update global stats
    update_agent_stats(active_count, inactive_count)
    
    return formatted_agents

def create_agent_cmd(args):
    """Create a new agent."""
    with Timer("Agent creation"):
        agent = framework.create_agent(
            name=args.name,
            description=args.description,
            model_name=args.model,
            enable_memory=not args.disable_memory,
            knowledge_base=args.knowledge_base
        )
    
    agent_id = agent.agent_id
    console.print(f"[bold green]{SYMBOLS['success']} Agent created successfully![/bold green]")
    console.print(f"[bold]Agent ID:[/bold] [cyan]{agent_id}[/cyan]")
    
    if args.verbose:
        display_agent_info({
            "agent_id": agent_id, 
            "name": args.name, 
            "description": args.description,
            "model": args.model or "Default",
            "memory_enabled": not args.disable_memory,
            "status": "inactive"
        })
    
    return agent_id

def create_browser_agent_cmd(args):
    """Create a new browser agent."""
    with Timer("Browser agent creation"):
        agent = framework.create_browser_agent(
            name=args.name,
            description=args.description,
            model_name=args.model,
            enable_memory=not args.disable_memory,
            knowledge_base=args.knowledge_base,
            headless=not args.show_browser
        )
    
    agent_id = agent.agent_id
    console.print(f"[bold green]{SYMBOLS['success']} Browser agent created successfully![/bold green]")
    console.print(f"[bold]Agent ID:[/bold] [cyan]{agent_id}[/cyan]")
    
    if args.verbose:
        display_agent_info({
            "agent_id": agent_id, 
            "name": args.name, 
            "description": args.description,
            "model": args.model or "Default",
            "memory_enabled": not args.disable_memory,
            "headless": not args.show_browser,
            "status": "inactive"
        })
    
    return agent_id

def list_agents_cmd(args):
    """List all agents."""
    def get_agents():
        agents_dict = framework.agent_store.list_agents()
        return format_agent_list(agents_dict)
    
    result, elapsed = run_with_spinner(get_agents, "Loading agents")
    agents = result
    
    if not agents:
        console.print(f"[yellow]{SYMBOLS['warning']} No agents found.[/yellow]")
        return
    
    display_hierarchical_list(agents, f"{SYMBOLS['agent']} Available Agents")
    
    if args.verbose:
        for agent_data in agents:
            agent_id = agent_data.get("agent_id")
            display_agent_info(agent_data)
    
    # Add interactive navigation mode
    if len(agents) > 0 and not args.no_interactive:
        console.print("[bold cyan]Enter interactive mode? (y/n)[/bold cyan]")
        if console.input("[bold cyan]> [/bold cyan]").lower() == "y":
            interactive_agent_browser(agents)

    # Get current number of agents
    state["agents"]["total"] = len(agents)
    
    console.print(f"\n[bold]Found {len(agents)} agents:[/bold]")
    
    # No agents found
    if not agents:
        console.print("[yellow]No agents found. Create one with 'create-agent' command.[/yellow]")
        return 0
    
    # Create a formatted display of the agents
    table = Table(box=ROUNDED, show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Status")
    table.add_column("Model")
    table.add_column("Memory")
    
    for agent in agents:
        # Status indicator
        status_symbol = SYMBOLS["active"] if agent["status"] == "active" else SYMBOLS["inactive"]
        status_color = "green" if agent["status"] == "active" else "red"
        status = f"[{status_color}]{status_symbol} {agent['status']}[/{status_color}]"
        
        # Memory indicator
        memory = "Enabled" if agent["memory_enabled"] else "Disabled"
        memory_color = "green" if agent["memory_enabled"] else "red"
        
        table.add_row(
            agent["agent_id"],
            agent["name"],
            agent["description"] or "No description",
            status,
            agent["model"] or "Default",
            f"[{memory_color}]{memory}[/{memory_color}]"
        )
    
    console.print(table)
    return 0

def interactive_agent_browser(agents):
    """
    Interactive browser for agents with vim-like navigation.
    
    Args:
        agents: List of agent data dictionaries
    """
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.align import Align
    from rich.text import Text
    
    # State variables
    current_index = 0
    search_mode = False
    search_query = ""
    search_results = []
    filtered_agents = agents.copy()
    
    def render_layout():
        """Render the layout with agent list and details."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Header
        header_text = Text("Agent Manager - Interactive Mode", style="bold cyan")
        header_panel = Panel(Align.center(header_text), border_style="blue")
        layout["header"].update(header_panel)
        
        # Body - Split into list and details
        body_layout = Layout()
        body_layout.split_row(
            Layout(name="agent_list", ratio=1),
            Layout(name="agent_details", ratio=2)
        )
        
        # Agent list
        agent_list = Table(box=ROUNDED, title="Available Agents", show_header=True, expand=True)
        agent_list.add_column("Agent")
        agent_list.add_column("Status")
        
        for idx, agent in enumerate(filtered_agents):
            name = agent.get("name", "Unknown")
            status = agent.get("status", "unknown")
            status_symbol = SYMBOLS["active"] if status == "active" else SYMBOLS["inactive"]
            
            # Highlight the selected agent
            if idx == current_index:
                row_style = "bold cyan"
                prefix = SYMBOLS["arrow_right"]
            else:
                row_style = ""
                prefix = "  "
                
            agent_list.add_row(
                Text(f"{prefix}{name}", style=row_style),
                Text(f"{status_symbol}{status}", style="green" if status == "active" else "yellow")
            )
        
        body_layout["agent_list"].update(Panel(agent_list, border_style="blue"))
        
        # Agent details
        if filtered_agents:
            selected_agent = filtered_agents[current_index]
            agent_table = Table(box=ROUNDED, show_header=False)
            agent_table.add_column("Property", style="bright_blue")
            agent_table.add_column("Value")
            
            for key, value in selected_agent.items():
                # Format the key nicely
                formatted_key = key.replace('_', ' ').title()
                
                # Format the value based on its type
                if isinstance(value, bool):
                    formatted_value = SYMBOLS['success'] if value else SYMBOLS['error']
                    style = "green" if value else "red"
                    agent_table.add_row(formatted_key, Text(formatted_value, style=style))
                elif key == 'agent_id':
                    agent_table.add_row(formatted_key, Text(str(value), style="cyan"))
                elif key == 'status':
                    if value.lower() == 'active':
                        agent_table.add_row(formatted_key, Text(f"{SYMBOLS['active']} {value}", style="green"))
                    elif value.lower() == 'inactive':
                        agent_table.add_row(formatted_key, Text(f"{SYMBOLS['inactive']} {value}", style="yellow"))
                    else:
                        agent_table.add_row(formatted_key, Text(value))
                elif key == 'memory_enabled':
                    symbol = SYMBOLS['success'] if value else SYMBOLS['error']
                    style = "green" if value else "red"
                    agent_table.add_row(formatted_key, Text(f"{symbol}", style=style))
                else:
                    agent_table.add_row(formatted_key, str(value))
            
            detail_panel = Panel(agent_table, title=f"Agent Details - {selected_agent.get('name', 'Unknown')}", border_style="green")
            body_layout["agent_details"].update(detail_panel)
        
        layout["body"].update(body_layout)
        
        # Footer - keybindings and search
        if search_mode:
            search_text = Text(f"Search: {search_query}█", style="bold yellow")
            footer_content = Panel(search_text, border_style="yellow")
        else:
            key_text = Text()
            key_text.append("j/k", style="bold blue")
            key_text.append(": Up/Down  ")
            key_text.append("s", style="bold blue")
            key_text.append(": Search  ")
            key_text.append("e", style="bold blue")
            key_text.append(": Execute Task  ")
            key_text.append("d", style="bold blue")
            key_text.append(": Delete  ")
            key_text.append("q", style="bold blue")
            key_text.append(": Quit  ")
            
            footer_content = Panel(Align.center(key_text), border_style="blue")
        
        layout["footer"].update(footer_content)
        
        return layout
    
    def filter_agents_by_search():
        """Filter agents based on search query."""
        nonlocal filtered_agents, current_index
        if not search_query:
            filtered_agents = agents.copy()
        else:
            filtered_agents = [
                agent for agent in agents
                if search_query.lower() in agent.get("name", "").lower() or
                   search_query.lower() in agent.get("description", "").lower() or
                   search_query.lower() in agent.get("agent_id", "").lower()
            ]
        current_index = 0  # Reset selection after filtering
    
    def handle_key_press(key):
        """Handle key presses for navigation and actions."""
        nonlocal current_index, search_mode, search_query, filtered_agents
        
        # Search mode handling
        if search_mode:
            if key == "\x1b":  # Escape key
                search_mode = False
                search_query = ""
                filtered_agents = agents.copy()
                current_index = 0
            elif key == "\r":  # Enter key
                search_mode = False
                filter_agents_by_search()
            elif key == "\x7f":  # Backspace key
                search_query = search_query[:-1]
                filter_agents_by_search()
            else:
                search_query += key
                filter_agents_by_search()
            return True
        
        # Normal mode handling
        if key.lower() == "q":
            return False  # Exit the loop
        elif key == "j" or key == "down":
            current_index = min(current_index + 1, len(filtered_agents) - 1)
        elif key == "k" or key == "up":
            current_index = max(current_index - 1, 0)
        elif key == "g":
            current_index = 0  # Top
        elif key == "G":
            current_index = len(filtered_agents) - 1  # Bottom
        elif key == "s":
            search_mode = True
            search_query = ""
        elif key == "e" and filtered_agents:
            # Execute a task with the selected agent
            selected_agent = filtered_agents[current_index]
            agent_id = selected_agent.get("agent_id")
            
            # Exit the Live mode temporarily to get input
            task = console.input(f"\nEnter task for {selected_agent.get('name')}: ")
            if task:
                # Create task arguments
                class TaskArgs:
                    pass
                task_args = TaskArgs()
                task_args.agent_id = agent_id
                task_args.task = task
                
                # Execute the task
                execute_task_cmd(task_args)
        elif key == "d" and filtered_agents:
            # Delete the selected agent
            selected_agent = filtered_agents[current_index]
            agent_id = selected_agent.get("agent_id")
            
            # Exit the Live mode temporarily to confirm
            confirm = console.input(f"\nDelete agent {selected_agent.get('name')}? (y/n): ")
            if confirm.lower() == "y":
                # Create delete arguments
                class DeleteArgs:
                    pass
                delete_args = DeleteArgs()
                delete_args.agent_id = agent_id
                
                # Delete the agent
                delete_agent_cmd(delete_args)
                
                # Refresh agent list
                def get_agents():
                    agents_dict = framework.agent_store.list_agents()
                    return format_agent_list(agents_dict)
                
                result, _ = run_with_spinner(get_agents, "Refreshing agents")
                new_agents = result
                filtered_agents = new_agents.copy()
                current_index = min(current_index, len(filtered_agents) - 1) if filtered_agents else 0
        
        return True
    
    # Main interactive loop
    import sys
    import termios
    import tty
    
    # Set up terminal for raw input
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        
        with Live(render_layout(), refresh_per_second=10, screen=True) as live:
            while True:
                key = sys.stdin.read(1)
                
                # Continue loop if the key handler returns True, otherwise break
                if not handle_key_press(key):
                    break
                
                # Update the display
                live.update(render_layout())
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def delete_agent_cmd(args):
    """Delete an agent."""
    agent_id = args.agent_id
    
    def delete_operation():
        return framework.delete_agent(agent_id)
    
    result, elapsed = run_with_spinner(delete_operation, f"Deleting agent {agent_id}")
    
    if result:
        console.print(f"[bold green]{SYMBOLS['success']} Agent {agent_id} deleted successfully![/bold green]")
    else:
        console.print(f"[bold red]{SYMBOLS['error']} Agent {agent_id} not found or could not be deleted.[/bold red]")

def execute_task_cmd(args):
    """Execute a task with an agent."""
    agent_id = args.agent_id
    agent = framework.get_agent(agent_id)
    
    if not agent:
        console.print(f"[bold red]{SYMBOLS['error']} Agent {agent_id} not found.[/bold red]")
        return
    
    task = args.task
    
    # Check if environment variables are set based on agent's model
    model = getattr(agent, "model", None)
    if model:
        if model.startswith("gpt-") and not os.environ.get("OPENAI_API_KEY"):
            console.print(f"[bold red]{SYMBOLS['error']} OpenAI API key not found in environment variables.[/bold red]")
            console.print(f"[yellow]{SYMBOLS['info']} Please set OPENAI_API_KEY environment variable.[/yellow]")
            return
        elif model.startswith("claude-") and not os.environ.get("ANTHROPIC_API_KEY"):
            console.print(f"[bold red]{SYMBOLS['error']} Anthropic API key not found in environment variables.[/bold red]")
            console.print(f"[yellow]{SYMBOLS['info']} Please set ANTHROPIC_API_KEY environment variable.[/yellow]")
            return
        elif model.startswith("llama") and not os.environ.get("OPENROUTER_API_KEY"):
            console.print(f"[bold red]{SYMBOLS['error']} OpenRouter API key not found in environment variables.[/bold red]")
            console.print(f"[yellow]{SYMBOLS['info']} Please set OPENROUTER_API_KEY environment variable.[/yellow]")
            return
    
    # Update task stats - increment running tasks
    update_task_stats(1, 0, 0)
    
    with create_progress_bar(f"Executing task with {agent.name}", time_remaining=True) as progress:
        task_progress = progress.add_task("Thinking...", total=None)
        
        # Execute the task
        start_time = time.time()
        try:
            result = agent.execute_task(task)
            # Update task stats - decrement running, increment completed
            update_task_stats(0, 1, 0)
        except Exception as e:
            # Update task stats - decrement running, increment failed
            update_task_stats(0, 0, 1)
            console.print(f"[bold red]{SYMBOLS['error']} Task execution failed: {str(e)}[/bold red]")
            return
            
        elapsed = time.time() - start_time
        
        # Complete the progress
        progress.update(task_progress, completed=True)
    
    # Check if result is an error message
    if result and isinstance(result, str) and result.startswith("Error"):
        console.print(f"\n[bold red]{SYMBOLS['error']} Error:[/bold red]")
        console.print(Panel(result, border_style="red"))
    else:
        console.print("\n[bold]Result:[/bold]")
        console.print(Panel(result, border_style="green"))
    
    # Display timing information
    if elapsed < 1:
        time_str = f"{elapsed * 1000:.2f} ms"
    elif elapsed < 60:
        time_str = f"{elapsed:.2f} seconds"
    else:
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        time_str = f"{minutes} min {seconds:.2f} sec"
    
    console.print(f"[dim]Task completed in {time_str}[/dim]")

def direct_llm_cmd(args):
    """Make a direct call to the LLM."""
    prompt = args.prompt
    model = args.model
    
    # Check if environment variables are set
    if model:
        if model.startswith("gpt-") and not os.environ.get("OPENAI_API_KEY"):
            console.print(f"[bold red]{SYMBOLS['error']} OpenAI API key not found in environment variables.[/bold red]")
            console.print(f"[yellow]{SYMBOLS['info']} Please set OPENAI_API_KEY environment variable.[/yellow]")
            return
        elif model.startswith("claude-") and not os.environ.get("ANTHROPIC_API_KEY"):
            console.print(f"[bold red]{SYMBOLS['error']} Anthropic API key not found in environment variables.[/bold red]")
            console.print(f"[yellow]{SYMBOLS['info']} Please set ANTHROPIC_API_KEY environment variable.[/yellow]")
            return
        elif model.startswith("llama") and not os.environ.get("OPENROUTER_API_KEY"):
            console.print(f"[bold red]{SYMBOLS['error']} OpenRouter API key not found in environment variables.[/bold red]")
            console.print(f"[yellow]{SYMBOLS['info']} Please set OPENROUTER_API_KEY environment variable.[/yellow]")
            return
    
    # Create a task
    from src.agent_base import Task
    from src.direct import Direct
    
    task = Task(prompt)
    
    with create_progress_bar("Processing with Direct LLM", time_remaining=True) as progress:
        llm_progress = progress.add_task("Generating response...", total=None)
        
        # Execute the task
        start_time = time.time()
        result = Direct.do(task, model=model)
        elapsed = time.time() - start_time
        
        # Complete the progress
        progress.update(llm_progress, completed=True)
    
    # Check if result is an error message
    if result and isinstance(result, str) and result.startswith("Error"):
        console.print(f"\n[bold red]{SYMBOLS['error']} Error:[/bold red]")
        console.print(Panel(result, border_style="red"))
    else:
        console.print("\n[bold]Result:[/bold]")
        console.print(Panel(result, border_style="green"))
    
    # Display timing information
    if elapsed < 1:
        time_str = f"{elapsed * 1000:.2f} ms"
    elif elapsed < 60:
        time_str = f"{elapsed:.2f} seconds"
    else:
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        time_str = f"{minutes} min {seconds:.2f} sec"
    
    console.print(f"[dim]Response generated in {time_str}[/dim]")

def scrape_docs_cmd(args):
    """Scrape documentation."""
    source = args.source.lower()
    
    if source == "upsonic":
        cmd = "python scripts/scrape_docs_sync.py"
        title = "Upsonic Documentation"
        url = "https://docs.upsonic.ai"
    elif source == "playwright":
        cmd = "python scripts/scrape_playwright_docs_sync.py"
        title = "Playwright Documentation"
        url = "https://playwright.dev"
    else:
        console.print(f"[bold red]{SYMBOLS['error']} Unknown source: {source}[/bold red]")
        console.print(f"[yellow]{SYMBOLS['info']} Available sources: upsonic, playwright[/yellow]")
        return
    
    console.print(f"[bold]{SYMBOLS['task']} Scraping {title} from {url}[/bold]")
    console.print(f"[yellow]{SYMBOLS['info']} This operation may take several minutes...[/yellow]")
    
    if args.yes or console.input(f"[bold]{SYMBOLS['info']} Proceed? [Y/n]: [/bold]").lower() != "n":
        import subprocess
        
        with create_progress_bar(f"Starting {source} scraper") as progress:
            task = progress.add_task("Initializing...", total=None)
            process = subprocess.Popen(
                cmd, 
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Allow some time for the scraper to start
            time.sleep(2)
            progress.update(task, completed=True)
        
        console.print(f"[bold green]{SYMBOLS['success']} Scraper started![/bold green]")
        console.print("[dim]Output:[/dim]")
        
        # Stream the output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                console.print(output.strip())
        
        # Check for errors
        rc = process.poll()
        if rc != 0:
            console.print(f"[bold red]{SYMBOLS['error']} Error running scraper[/bold red]")
            for line in process.stderr.readlines():
                console.print(f"[red]{line.strip()}[/red]")
            
            # Update task stats - increment failed tasks
            update_task_stats(0, 0, 1)
        else:
            console.print(f"[bold green]{SYMBOLS['success']} Scraping completed successfully![/bold green]")
            
            # Update task stats - increment completed tasks
            update_task_stats(0, 1, 0)

def integrate_knowledge_cmd(args):
    """Integrate scraped knowledge."""
    console.print("[bold]Integrating scraped knowledge[/bold]")
    
    if args.yes or console.input("[bold]Proceed? [Y/n]: [/bold]").lower() != "n":
        import subprocess
        
        with create_progress_bar("Starting knowledge integration") as progress:
            task = progress.add_task("Initializing...", total=None)
            process = subprocess.Popen(
                "python scripts/integrate_knowledge.py", 
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Allow some time for the integration to start
            time.sleep(2)
            progress.update(task, completed=True)
        
        console.print("[bold green]Integration started![/bold green]")
        console.print("[dim]Output:[/dim]")
        
        # Stream the output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                console.print(output.strip())
        
        # Check for errors
        rc = process.poll()
        if rc != 0:
            console.print("[bold red]Error running integration[/bold red]")
            for line in process.stderr.readlines():
                console.print(f"[red]{line.strip()}[/red]")
        else:
            console.print("[bold green]Knowledge integration completed successfully![/bold green]")

def browse_cmd(args):
    """Browse a URL with a browser agent."""
    agent_id = args.agent_id
    agent = framework.get_agent(agent_id)
    
    if not agent:
        console.print(f"[bold red]{SYMBOLS['error']} Agent {agent_id} not found.[/bold red]")
        return
    
    if not hasattr(agent, "browse"):
        console.print(f"[bold red]{SYMBOLS['error']} Agent {agent_id} is not a browser agent.[/bold red]")
        return
    
    url = args.url
    
    console.print(f"[bold]{SYMBOLS['task']} Browsing {url} with agent {agent.name}[/bold]")
    
    # This is an async function, so we need to run it in an event loop
    async def browse_url():
        with create_progress_bar(f"Browsing with {agent.name}") as progress:
            browse_progress = progress.add_task("Opening browser...", total=100)
            progress.update(browse_progress, completed=10)
            
            # Browse to the URL
            result = await agent.browse(url)
            progress.update(browse_progress, completed=40)
            
            if result["status"] != "success":
                console.print(f"[bold red]{SYMBOLS['error']} Error browsing to {url}: {result.get('error', 'Unknown error')}[/bold red]")
                return False
            
            progress.update(browse_progress, completed=60)
            
            # Get page content if requested
            if args.get_content:
                content_result = await agent.get_page_text()
                if content_result["status"] == "success":
                    console.print("\n[bold]Page Content:[/bold]")
                    content = content_result.get("text", "")
                    if len(content) > 1000:
                        content = content[:1000] + "...(truncated)"
                    console.print(Panel(content, border_style="blue"))
            
            progress.update(browse_progress, completed=80)
            
            # Take a screenshot if requested
            if args.screenshot:
                screenshot_result = await agent.take_screenshot()
                if screenshot_result["status"] == "success":
                    console.print(f"[bold green]{SYMBOLS['success']} Screenshot saved to: {screenshot_result['path']}[/bold green]")
            
            progress.update(browse_progress, completed=100)
            return True
    
    # Run the async function
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(browse_url())
    
    if success:
        console.print(f"[bold green]{SYMBOLS['success']} Browsing completed successfully![/bold green]")
    
    # Close the browser if requested
    if args.close:
        async def close_browser():
            await agent.stop()
        
        with create_progress_bar("Closing browser") as progress:
            close_progress = progress.add_task("Closing...", total=100)
            loop.run_until_complete(close_browser())
            progress.update(close_progress, completed=100)
        
        console.print("[bold]Browser closed.[/bold]")

def rag_web_scrape_cmd(args):
    """Scrape a website using the RAG web browser MCP."""
    url = args.url
    output_format = args.format
    view_result = args.view
    
    # Get the output directory
    output_dir = Path("knowledge/web_scrape")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a sanitized filename from the URL
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace("www.", "")
    path = parsed_url.path.strip("/").replace("/", "_")
    if not path:
        path = "index"
    filename = f"{domain}_{path}.{output_format}"
    output_path = output_dir / filename
    
    console.print(f"Scraping: [cyan]{url}[/cyan]")
    console.print(f"Output format: [cyan]{output_format}[/cyan]")
    console.print(f"Output path: [cyan]{output_path}[/cyan]")
    
    # Perform the scraping
    with Timer("Web scraping"):
        result = framework.rag_web_scrape(url, str(output_path), output_format)
    
    if result.get("error"):
        console.print(f"[bold red]Error:[/bold red] {result['error']}")
        return 1
    
    console.print(f"[bold green]{SYMBOLS['success']} Content scraped successfully![/bold green]")
    console.print(f"Saved to: [cyan]{output_path}[/cyan]")
    
    # View the result if requested
    if view_result:
        console.print("\n[bold]Content preview:[/bold]")
        with open(output_path, "r") as f:
            content = f.read()
            
            if output_format == "md":
                from rich.markdown import Markdown
                console.print(Markdown(content))
            else:
                console.print(content)
    
    return 0

def mcp_chat_cmd(args):
    """Start a chat interface with an MCP server."""
    try:
        from src.cli.mcp_chat import MCPChatInterface
    except ImportError:
        console.print("[bold red]Error:[/bold red] Failed to import MCPChatInterface. Make sure the module exists.")
        return 1
    
    # Get full model name with provider
    model_config = get_model_config(args.model)
    display_model = model_config["name"]
    
    console.print(f"Starting chat with MCP server: [cyan]{args.server}[/cyan]")
    console.print(f"Using model: [cyan]{display_model}[/cyan]")
    
    try:
        chat_interface = MCPChatInterface(
            server_name=args.server,
            model_name=args.model
        )
        chat_interface.start_chat()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1
    
    return 0

def unified_mcp_chat_cmd(args):
    """Start the unified MCP chat interface that can orchestrate multiple servers."""
    try:
        from src.cli.unified_mcp_chat import UnifiedMCPChatInterface
    except ImportError:
        console.print("[bold red]Error:[/bold red] Failed to import UnifiedMCPChatInterface. Make sure the module exists.")
        return 1
    
    # Get full model name with provider
    from src.llm_integration import get_model_config
    model_config = get_model_config(args.model)
    display_model = model_config["name"]
    
    console.print(f"Starting unified MCP chat orchestration")
    console.print(f"Using model: [cyan]{display_model}[/cyan]")
    
    try:
        # Import asyncio to run the async chat interface
        import asyncio
        
        # Create and run the chat interface
        chat_interface = UnifiedMCPChatInterface(model_name=args.model)
        asyncio.run(chat_interface.start_chat())
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1
    
    return 0

def youtube_scraper_cmd(args):
    """Launch the YouTube scraper in browser mode"""
    try:
        import webbrowser
        import subprocess
        import time
        from pathlib import Path
        import os
        
        # Start the YouTube scraper server
        script_path = Path(__file__).parent / "scripts" / "youtube_scraper_mcp.py"
        
        if not script_path.exists():
            print(f"Error: YouTube scraper script not found at {script_path}")
            return
            
        print(f"Starting YouTube scraper server at {script_path}...")
        
        # Start the server in the background
        server_process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give the server a moment to start
        time.sleep(2)
        
        # Construct the URL for the MCP inspector with our server
        url = "https://inspector.modelcontextprotocol.io/?server=stdio&server-path=" + os.path.abspath(str(script_path))
        
        print(f"Opening YouTube scraper in MCP Inspector: {url}")
        webbrowser.open(url)
        
        print("\nYouTube Scraper is running. Press Ctrl+C to stop.")
        
        try:
            # Keep the server running until user interrupts
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping YouTube scraper...")
        finally:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                
        print("YouTube scraper stopped.")
        
    except Exception as e:
        print(f"Error launching YouTube scraper: {e}")

def desktop_commander_cmd(args):
    """Launch the Desktop Commander in browser mode"""
    try:
        import webbrowser
        import subprocess
        import time
        from pathlib import Path
        import os
        
        # Start the Desktop Commander server
        script_path = Path(__file__).parent / "scripts" / "desktop_commander_mcp.py"
        
        if not script_path.exists():
            print(f"Error: Desktop Commander script not found at {script_path}")
            return
            
        print(f"Starting Desktop Commander server at {script_path}...")
        
        # Ensure the script is executable
        os.chmod(str(script_path), 0o755)
        
        # Start the server in the background
        server_process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give the server a moment to start
        time.sleep(2)
        
        # Construct the URL for the MCP inspector with our server
        url = "https://inspector.modelcontextprotocol.io/?server=stdio&server-path=" + os.path.abspath(str(script_path))
        
        print(f"Opening Desktop Commander in MCP Inspector: {url}")
        webbrowser.open(url)
        
        print("\nDesktop Commander is running. Press Ctrl+C to stop.")
        
        try:
            # Keep the server running until user interrupts
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping Desktop Commander...")
        finally:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                
        print("Desktop Commander stopped.")
        
    except Exception as e:
        print(f"Error launching Desktop Commander: {e}")

def main():
    """Main entry point for the CLI."""
    # Set up the interrupt handler for graceful exits
    setup_interrupt_handler()
    
    parser = argparse.ArgumentParser(
        description="Upsonic Agent Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new agent
  ./app.py create-agent "My Agent" --description "A helpful assistant"

  # Create a browser agent
  ./app.py create-browser "Web Agent" --description "Web browsing agent"

  # List all agents
  ./app.py list-agents

  # Execute a task with an agent
  ./app.py execute <agent_id> "What is the capital of France?"

  # Make a direct LLM call
  ./app.py direct "What is the meaning of life?"

  # Scrape documentation
  ./app.py scrape upsonic

  # Browse a URL with a browser agent
  ./app.py browse <agent_id> https://example.com --screenshot
  
  # Show system dashboard
  ./app.py dashboard
  
  # Scrape web content with RAG MCP
  ./app.py rag-scrape https://example.com --view
  
  # Chat with an MCP server
  ./app.py mcp-chat <server_name>
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create agent command
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new agent"
    )
    create_parser.add_argument("name", help="Name of the agent")
    create_parser.add_argument("--description", "-d", help="Description of the agent")
    create_parser.add_argument("--model", "-m", help="Model to use")
    create_parser.add_argument("--disable-memory", action="store_true", help="Disable agent memory")
    create_parser.add_argument("--knowledge-base", "-kb", help="Knowledge base to use")
    create_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Create browser agent command
    browser_parser = subparsers.add_parser("create-browser", help="Create a browser agent")
    browser_parser.add_argument("name", help="Name of the agent")
    browser_parser.add_argument("--description", "-d", help="Description of the agent")
    browser_parser.add_argument("--model", "-m", help="Model to use")
    browser_parser.add_argument("--disable-memory", action="store_true", help="Disable agent memory")
    browser_parser.add_argument("--knowledge-base", "-kb", help="Knowledge base to use")
    browser_parser.add_argument("--show-browser", action="store_true", help="Show browser window")
    browser_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # List agents command
    list_parser = subparsers.add_parser("list-agents", help="List all agents")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    list_parser.add_argument("--no-interactive", "-n", action="store_true", help="Disable interactive mode")
    
    # Delete agent command
    delete_parser = subparsers.add_parser("delete-agent", help="Delete an agent")
    delete_parser.add_argument("agent_id", help="ID of the agent to delete")
    
    # Execute task command
    execute_parser = subparsers.add_parser("execute", help="Execute a task with an agent")
    execute_parser.add_argument("agent_id", help="ID of the agent to use")
    execute_parser.add_argument("task", help="Task to execute")
    
    # Direct LLM command
    direct_parser = subparsers.add_parser("direct", help="Make a direct call to the LLM")
    direct_parser.add_argument("prompt", help="Prompt to send to the LLM")
    direct_parser.add_argument("--model", "-m", help="Model to use")
    
    # Scrape docs command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape documentation")
    scrape_parser.add_argument("source", help="Source to scrape (upsonic, playwright)")
    scrape_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    
    # Integrate knowledge command
    integrate_parser = subparsers.add_parser("integrate", help="Integrate scraped knowledge")
    integrate_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    
    # Browse command
    browse_parser = subparsers.add_parser("browse", help="Browse a URL with a browser agent")
    browse_parser.add_argument("agent_id", help="ID of the browser agent")
    browse_parser.add_argument("url", help="URL to browse")
    browse_parser.add_argument("--get-content", "-c", action="store_true", help="Get page content")
    browse_parser.add_argument("--screenshot", "-s", action="store_true", help="Take a screenshot")
    browse_parser.add_argument("--close", action="store_true", help="Close the browser after browsing")
    
    # RAG Web Scrape command
    rag_scrape_parser = subparsers.add_parser("rag-scrape", help="Scrape web content with RAG MCP")
    rag_scrape_parser.add_argument("url", help="URL to scrape")
    rag_scrape_parser.add_argument("--format", "-f", default="md", choices=["md", "txt", "html"], help="Output format (md, txt, html)")
    rag_scrape_parser.add_argument("--view", "-v", action="store_true", help="View processed content after scraping")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Show system dashboard")
    dashboard_parser.add_argument("--refresh-rate", "-r", type=float, default=1.0, 
                                help="Dashboard refresh rate in seconds")
    dashboard_parser.add_argument("--interactive", "-i", action="store_true", help="Use interactive mode with keyboard controls")
    
    # MCP chat command
    mcp_chat_parser = subparsers.add_parser("mcp-chat", help="Start a chat interface with an MCP server")
    mcp_chat_parser.add_argument("server", help="Name of the MCP server to connect to")
    mcp_chat_parser.add_argument("--model", help="Name of the LLM model to use", default="claude-3.7-sonnet")
    mcp_chat_parser.set_defaults(func=mcp_chat_cmd)
    
    # Unified MCP chat command
    unified_mcp_chat_parser = subparsers.add_parser("unified-mcp-chat", help="Start the unified MCP chat interface")
    unified_mcp_chat_parser.add_argument("--model", help="Name of the LLM model to use", default="claude-3.7-sonnet")
    unified_mcp_chat_parser.set_defaults(func=unified_mcp_chat_cmd)
    
    # Add YouTube Scraper parser
    youtube_parser = subparsers.add_parser('youtube-scraper', help='Launch interactive YouTube scraper')
    youtube_parser.set_defaults(func=youtube_scraper_cmd)
    
    # Add Desktop Commander parser
    desktop_parser = subparsers.add_parser('desktop-commander', help='Launch interactive Desktop Commander')
    desktop_parser.set_defaults(func=desktop_commander_cmd)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Print banner
    print_banner("Upsonic Framework", "Intelligent Agent Framework")
    
    # Execute command
    if args.command == "create-agent":
        create_agent_cmd(args)
    elif args.command == "create-browser":
        create_browser_agent_cmd(args)
    elif args.command == "list-agents":
        list_agents_cmd(args)
    elif args.command == "delete-agent":
        delete_agent_cmd(args)
    elif args.command == "execute":
        execute_task_cmd(args)
    elif args.command == "direct":
        direct_llm_cmd(args)
    elif args.command == "scrape":
        scrape_docs_cmd(args)
    elif args.command == "integrate":
        integrate_knowledge_cmd(args)
    elif args.command == "browse":
        browse_cmd(args)
    elif args.command == "rag-scrape":
        rag_web_scrape_cmd(args)
    elif args.command == "dashboard":
        dashboard_cmd(args)
    elif args.command == "mcp-chat":
        mcp_chat_cmd(args)
    elif args.command == "unified-mcp-chat":
        unified_mcp_chat_cmd(args)
    elif args.command == "youtube-scraper":
        youtube_scraper_cmd(args)
    elif args.command == "desktop-commander":
        desktop_commander_cmd(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 