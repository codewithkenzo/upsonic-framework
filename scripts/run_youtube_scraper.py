#!/usr/bin/env python
import asyncio
import sys
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters

async def run_youtube_scraper():
    # Start the YouTube scraper server
    server_params = StdioServerParameters(
        command="python",
        args=["scripts/youtube_scraper_mcp.py"],
    )
    
    try:
        # Connect to the YouTube scraper server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                print("Available tools:")
                if hasattr(tools, 'tools'):
                    for tool in tools.tools:
                        print(f"- {tool.name}: {tool.description}")
                else:
                    for tool in tools:
                        print(f"- {tool.name}: {tool.description}")
                
                # Navigate to YouTube
                print("\nNavigating to YouTube...")
                result = await session.call_tool("navigate_to_youtube", {})
                print(f"Result: {result.content}")
                
                # Search for Python programming tutorial
                query = "Python programming tutorial"
                print(f"\nSearching for: {query}")
                result = await session.call_tool("search_youtube", {"query": query})
                print(f"Result: {result.content}")
                
                # Scrape video results
                print("\nScraping video results...")
                result = await session.call_tool("scrape_video_results", {})
                print(f"Result: {result.content}")
                
                # Click on the first video
                print("\nClicking on the first video...")
                result = await session.call_tool("click_video", {"position": 1})
                print(f"Result: {result.content}")
                
                # Scrape comments
                print("\nScraping comments...")
                result = await session.call_tool("scrape_video_comments", {})
                print(f"Result: {result.content}")
                
                # Close the browser
                print("\nClosing browser...")
                result = await session.call_tool("close_browser", {})
                print(f"Result: {result.content}")
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(run_youtube_scraper())) 