#!/usr/bin/env python3
"""
Script to directly run the YouTube scraper with a few commands
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Import the correct MCP client classes from the Python SDK
from mcp import ClientSession
from mcp import stdio_client
from mcp.client.stdio import StdioServerParameters

async def main():
    """Run the YouTube scraper and perform some operations"""
    print("Starting YouTube scraper client...")
    
    # Start the YouTube scraper server in a separate process
    script_path = Path(__file__).parent / "youtube_scraper_mcp.py"
    
    server_process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it a moment to start
    await asyncio.sleep(2)
    
    # Create server parameters for the YouTube scraper
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(script_path)]
    )
    
    try:
        # Connect to the server using stdio transport
        async with stdio_client(server_params) as (read, write):
            # Create a client session
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                print("\nAvailable tools:")
                if hasattr(tools, "tools"):
                    for tool in tools.tools:
                        print(f"- {tool.name}: {tool.description}")
                else:
                    # It might return a list of tuples or other structure
                    for tool in tools:
                        if isinstance(tool, tuple) and len(tool) >= 2:
                            print(f"- {tool[0]}: {tool[1]}")
                        elif hasattr(tool, "name") and hasattr(tool, "description"):
                            print(f"- {tool.name}: {tool.description}")
                        else:
                            print(f"- {tool}")
                
                # Start the workflow
                print("\n1. Navigating to YouTube...")
                navigate_result = await session.call_tool("navigate_to_youtube", {})
                print(f"Result: {navigate_result}")
                
                # Search for a topic
                search_query = "Python programming tutorial"
                print(f"\n2. Searching for '{search_query}'...")
                search_result = await session.call_tool("search_youtube", {"query": search_query})
                print(f"Result: {search_result}")
                
                # Scrape video results
                print("\n3. Scraping video results...")
                scrape_result = await session.call_tool("scrape_video_results", {"max_videos": 5})
                
                # Parse the result content
                if hasattr(scrape_result, "content") and len(scrape_result.content) > 0:
                    print(scrape_result.content[0].text)
                else:
                    print(f"Result: {scrape_result}")
                
                # Click on the first video
                print("\n4. Clicking on the first video...")
                click_result = await session.call_tool("click_video", {"position": 1})
                print(f"Result: {click_result}")
                
                # Scrape comments
                print("\n5. Scraping comments...")
                comments_result = await session.call_tool("scrape_video_comments", {"max_comments": 3})
                if hasattr(comments_result, "content") and len(comments_result.content) > 0:
                    print(comments_result.content[0].text)
                else:
                    print(f"Result: {comments_result}")
                
                # Close the browser
                print("\n6. Closing browser...")
                close_result = await session.call_tool("close_browser", {})
                print(f"Result: {close_result}")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop the server process
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

if __name__ == "__main__":
    asyncio.run(main()) 