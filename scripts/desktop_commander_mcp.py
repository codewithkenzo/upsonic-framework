#!/usr/bin/env python
import asyncio
import json
import os
import sys
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastmcp import FastMCP, Context, Image
from playwright.async_api import async_playwright, Browser, Page

# Initialize the FastMCP server
mcp = FastMCP("Desktop Commander")

class DesktopCommanderState:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
        self.context = None
        self.screenshots_dir = Path.home() / "Desktop" / "desktop_commander_screenshots"

# Create a global state
state = DesktopCommanderState()

@mcp.tool()
async def start_browser(ctx: Context, browser_type: str = "chromium", headless: bool = False) -> str:
    """
    Start a browser session
    
    Args:
        ctx: MCP context
        browser_type: Type of browser to launch (chromium, firefox, webkit)
        headless: Whether to run in headless mode
    """
    await ctx.info(f"Starting {browser_type} browser (headless={headless})...")
    
    if state.browser:
        await ctx.info("Browser already running, closing existing session")
        await state.browser.close()
    
    # Initialize playwright if needed
    if not state.playwright:
        state.playwright = await async_playwright().start()
    
    # Launch browser based on type
    if browser_type.lower() == "firefox":
        state.browser = await state.playwright.firefox.launch(headless=headless)
    elif browser_type.lower() == "webkit":
        state.browser = await state.playwright.webkit.launch(headless=headless)
    else:
        state.browser = await state.playwright.chromium.launch(headless=headless)
    
    # Create a new context and page
    state.context = await state.browser.new_context()
    state.page = await state.context.new_page()
    
    # Take screenshot
    screenshot = await state.page.screenshot()
    
    # Send screenshot
    image = Image(data=screenshot, format="png")
    
    await ctx.info(f"Browser started successfully: {browser_type}")
    return f"Browser {browser_type} started successfully"

@mcp.tool()
async def navigate_to_url(ctx: Context, url: str) -> str:
    """
    Navigate to a specified URL
    
    Args:
        ctx: MCP context
        url: The URL to navigate to
    """
    if not state.page:
        return "Browser not started. Please run start_browser first."
    
    await ctx.info(f"Navigating to {url}...")
    
    # Ensure URL has protocol
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    # Navigate to the URL
    await state.page.goto(url)
    await state.page.wait_for_load_state("networkidle")
    
    # Take screenshot
    screenshot = await state.page.screenshot()
    
    # Send screenshot
    image = Image(data=screenshot, format="png")
    
    await ctx.info(f"Successfully navigated to {url}")
    return f"Successfully navigated to {url}"

@mcp.tool()
async def take_screenshot(ctx: Context, full_page: bool = False) -> str:
    """
    Take a screenshot of the current page
    
    Args:
        ctx: MCP context
        full_page: Whether to capture the full scrollable page
    """
    if not state.page:
        return "Browser not started. Please run start_browser first."
    
    await ctx.info(f"Taking {'full page' if full_page else 'viewport'} screenshot...")
    
    # Create screenshots directory if it doesn't exist
    os.makedirs(state.screenshots_dir, exist_ok=True)
    
    # Generate filename with timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = state.screenshots_dir / filename
    
    # Take screenshot
    await state.page.screenshot(path=str(filepath), full_page=full_page)
    screenshot = await state.page.screenshot(full_page=full_page)
    
    # Send screenshot
    image = Image(data=screenshot, format="png")
    
    await ctx.info(f"Screenshot saved to {filepath}")
    return f"Screenshot saved to {filepath}"

@mcp.tool()
async def click_element(ctx: Context, selector: str) -> str:
    """
    Click on an element matching the specified selector
    
    Args:
        ctx: MCP context
        selector: CSS selector for the element to click
    """
    if not state.page:
        return "Browser not started. Please run start_browser first."
    
    await ctx.info(f"Clicking element with selector: {selector}...")
    
    try:
        # Wait for the element to be visible
        await state.page.wait_for_selector(selector, state="visible", timeout=5000)
        
        # Click the element
        await state.page.click(selector)
        
        # Wait for any navigation or network activity
        await state.page.wait_for_load_state("networkidle")
        
        # Take screenshot
        screenshot = await state.page.screenshot()
        
        # Send screenshot
        image = Image(data=screenshot, format="png")
        
        await ctx.info(f"Successfully clicked element with selector: {selector}")
        return f"Successfully clicked element with selector: {selector}"
    except Exception as e:
        error_message = f"Error clicking element: {str(e)}"
        await ctx.info(error_message)
        return error_message

@mcp.tool()
async def type_text(ctx: Context, selector: str, text: str, press_enter: bool = False) -> str:
    """
    Type text into an input field
    
    Args:
        ctx: MCP context
        selector: CSS selector for the input field
        text: Text to type
        press_enter: Whether to press Enter after typing
    """
    if not state.page:
        return "Browser not started. Please run start_browser first."
    
    await ctx.info(f"Typing '{text}' into element with selector: {selector}...")
    
    try:
        # Wait for the element to be visible
        await state.page.wait_for_selector(selector, state="visible", timeout=5000)
        
        # Focus on the element
        await state.page.focus(selector)
        
        # Clear any existing text
        await state.page.fill(selector, "")
        
        # Type the text
        await state.page.type(selector, text)
        
        # Press Enter if requested
        if press_enter:
            await state.page.press(selector, "Enter")
            await state.page.wait_for_load_state("networkidle")
        
        # Take screenshot
        screenshot = await state.page.screenshot()
        
        # Send screenshot
        image = Image(data=screenshot, format="png")
        
        await ctx.info(f"Successfully typed text into element with selector: {selector}")
        return f"Successfully typed '{text}' into element with selector: {selector}" + (" and pressed Enter" if press_enter else "")
    except Exception as e:
        error_message = f"Error typing text: {str(e)}"
        await ctx.info(error_message)
        return error_message

@mcp.tool()
async def get_page_content(ctx: Context, selector: str = "body") -> str:
    """
    Get the text content of an element or the entire page
    
    Args:
        ctx: MCP context
        selector: CSS selector for the element (defaults to body for entire page)
    """
    if not state.page:
        return "Browser not started. Please run start_browser first."
    
    await ctx.info(f"Getting content from selector: {selector}...")
    
    try:
        # Wait for the element to be visible
        await state.page.wait_for_selector(selector, state="visible", timeout=5000)
        
        # Get the text content
        content = await state.page.text_content(selector)
        
        if not content:
            content = "Element found but it contains no text content."
        
        # Take screenshot
        screenshot = await state.page.screenshot()
        
        # Send screenshot
        image = Image(data=screenshot, format="png")
        
        await ctx.info(f"Successfully retrieved content from selector: {selector}")
        
        # Truncate content if it's too long
        if len(content) > 10000:
            content = content[:10000] + "... (content truncated due to length)"
            
        return content
    except Exception as e:
        error_message = f"Error getting content: {str(e)}"
        await ctx.info(error_message)
        return error_message

@mcp.tool()
async def execute_javascript(ctx: Context, script: str) -> str:
    """
    Execute JavaScript code on the page
    
    Args:
        ctx: MCP context
        script: JavaScript code to execute
    """
    if not state.page:
        return "Browser not started. Please run start_browser first."
    
    await ctx.info("Executing JavaScript...")
    
    try:
        # Execute the JavaScript
        result = await state.page.evaluate(script)
        
        # Convert result to string if it's not already
        if result is None:
            result_str = "JavaScript executed successfully (no return value)"
        else:
            try:
                result_str = json.dumps(result, indent=2)
            except:
                result_str = str(result)
        
        # Take screenshot
        screenshot = await state.page.screenshot()
        
        # Send screenshot
        image = Image(data=screenshot, format="png")
        
        await ctx.info("JavaScript executed successfully")
        return f"JavaScript executed successfully. Result:\n\n{result_str}"
    except Exception as e:
        error_message = f"Error executing JavaScript: {str(e)}"
        await ctx.info(error_message)
        return error_message

@mcp.tool()
async def scroll_page(ctx: Context, direction: str = "down", amount: int = 500) -> str:
    """
    Scroll the page in the specified direction
    
    Args:
        ctx: MCP context
        direction: Direction to scroll (up, down, left, right)
        amount: Number of pixels to scroll
    """
    if not state.page:
        return "Browser not started. Please run start_browser first."
    
    # Map direction to x and y values
    x = 0
    y = 0
    
    if direction.lower() == "up":
        y = -amount
    elif direction.lower() == "down":
        y = amount
    elif direction.lower() == "left":
        x = -amount
    elif direction.lower() == "right":
        x = amount
    else:
        return f"Invalid direction: {direction}. Use up, down, left, or right."
    
    await ctx.info(f"Scrolling {direction} by {amount} pixels...")
    
    # Execute JavaScript to scroll
    await state.page.evaluate(f"window.scrollBy({x}, {y})")
    
    # Wait briefly for any lazy-loaded content
    await asyncio.sleep(0.5)
    
    # Take screenshot
    screenshot = await state.page.screenshot()
    
    # Send screenshot
    image = Image(data=screenshot, format="png")
    
    await ctx.info(f"Scrolled {direction} by {amount} pixels")
    return f"Scrolled {direction} by {amount} pixels"

@mcp.tool()
async def wait_for_element(ctx: Context, selector: str, timeout: int = 10000) -> str:
    """
    Wait for an element to appear on the page
    
    Args:
        ctx: MCP context
        selector: CSS selector for the element
        timeout: Maximum time to wait in milliseconds
    """
    if not state.page:
        return "Browser not started. Please run start_browser first."
    
    await ctx.info(f"Waiting for element with selector: {selector} (timeout: {timeout}ms)...")
    
    try:
        # Wait for the element
        await state.page.wait_for_selector(selector, timeout=timeout)
        
        # Take screenshot
        screenshot = await state.page.screenshot()
        
        # Send screenshot
        image = Image(data=screenshot, format="png")
        
        await ctx.info(f"Element found: {selector}")
        return f"Successfully found element with selector: {selector}"
    except Exception as e:
        error_message = f"Error waiting for element: {str(e)}"
        await ctx.info(error_message)
        return error_message

@mcp.tool()
async def open_new_tab(ctx: Context, url: str = "") -> str:
    """
    Open a new browser tab, optionally navigating to a URL
    
    Args:
        ctx: MCP context
        url: Optional URL to navigate to in the new tab
    """
    if not state.context:
        return "Browser not started. Please run start_browser first."
    
    await ctx.info("Opening new tab...")
    
    # Create a new page (tab)
    state.page = await state.context.new_page()
    
    # Navigate to URL if provided
    if url:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        await ctx.info(f"Navigating to {url}...")
        await state.page.goto(url)
        await state.page.wait_for_load_state("networkidle")
    
    # Take screenshot
    screenshot = await state.page.screenshot()
    
    # Send screenshot
    image = Image(data=screenshot, format="png")
    
    if url:
        await ctx.info(f"New tab opened and navigated to {url}")
        return f"New tab opened and navigated to {url}"
    else:
        await ctx.info("New tab opened")
        return "New tab opened"

@mcp.tool()
async def close_tab(ctx: Context) -> str:
    """Close the current browser tab"""
    if not state.page:
        return "Browser not started. Please run start_browser first."
    
    await ctx.info("Closing current tab...")
    
    # Close the current page
    await state.page.close()
    
    # Get all pages and set the last one as active
    pages = state.context.pages
    if pages:
        state.page = pages[-1]
        
        # Take screenshot of the now-active tab
        screenshot = await state.page.screenshot()
        
        # Send screenshot
        image = Image(data=screenshot, format="png")
        
        await ctx.info("Tab closed, switched to previous tab")
        return "Tab closed, switched to previous tab"
    else:
        state.page = None
        await ctx.info("All tabs closed")
        return "All tabs closed"

@mcp.tool()
async def close_browser(ctx: Context) -> str:
    """Close the browser completely"""
    if not state.browser:
        return "Browser not running"
    
    await ctx.info("Closing browser...")
    
    # Close the browser
    await state.browser.close()
    
    # Reset state
    state.browser = None
    state.context = None
    state.page = None
    
    await ctx.info("Browser closed successfully")
    return "Browser closed successfully"

if __name__ == "__main__":
    mcp.run() 