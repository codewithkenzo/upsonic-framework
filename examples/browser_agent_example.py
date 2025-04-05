#!/usr/bin/env python3
"""
Example of using a browser agent to browse a website and analyze its content.
"""

import asyncio
import sys
sys.path.append(".")

from src.main import framework

async def main():
    """Run the browser agent example."""
    # Create a browser agent
    browser_agent = framework.create_browser_agent(
        name="Web Explorer",
        description="An agent that can browse the web and analyze content",
        model_name="gpt-4o",
        enable_memory=True,
        headless=False  # Set to True to run without UI
    )
    
    print(f"Created browser agent with ID: {browser_agent.agent_id}")
    
    try:
        # Browse to a website
        url = "https://docs.upsonic.ai/introduction"
        print(f"Browsing to {url}...")
        result = await browser_agent.browse(url)
        
        if result["status"] == "success":
            print(f"Successfully loaded page: {result['title']}")
            
            # Extract text content
            content_result = await browser_agent.get_page_text()
            if content_result["status"] == "success":
                print("Successfully extracted text content.")
                
                # Take a screenshot
                screenshot_result = await browser_agent.take_screenshot()
                print(f"Screenshot saved to: {screenshot_result['path']}")
                
                # Perform a task with the browser content
                task = "Summarize the key features of Upsonic based on this page content."
                print(f"\nExecuting task: {task}")
                summary = browser_agent.execute_browsing_task(task)
                print(f"\nSummary: {summary}")
            else:
                print(f"Error extracting content: {content_result['error']}")
        else:
            print(f"Error browsing to {url}: {result['error']}")
    finally:
        # Always make sure to close the browser
        await browser_agent.stop()
        print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main()) 