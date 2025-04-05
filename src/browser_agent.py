"""
Browser agent using Playwright.
"""

import os
import asyncio
import time
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, ElementHandle
from datetime import datetime

from src.agent_base import BaseAgent, Task

class BrowserTool:
    """Tool for browser automation using Playwright."""
    
    def __init__(self, headless=False):
        """Initialize the browser tool.
        
        Args:
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to False.
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.screenshot_dir = os.path.join(os.getcwd(), "screenshots")
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
    async def start(self):
        """Start the browser."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
    async def stop(self):
        """Stop the browser."""
        if self.playwright:
            await self.context.close()
            await self.browser.close()
            await self.playwright.stop()
            self.playwright = None
            self.browser = None
            self.context = None
            self.page = None
            
    async def go_to(self, url):
        """Navigate to a URL.
        
        Args:
            url (str): URL to navigate to.
            
        Returns:
            dict: Result of the operation.
        """
        try:
            await self.start()
            await self.page.goto(url)
            title = await self.page.title()
            return {
                "status": "success",
                "title": title,
                "url": self.page.url
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def get_content(self):
        """Get the content of the current page.
        
        Returns:
            dict: Page content.
        """
        try:
            content = await self.page.content()
            title = await self.page.title()
            return {
                "status": "success",
                "title": title,
                "content": content,
                "url": self.page.url
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def get_text(self):
        """Get the text content of the current page.
        
        Returns:
            dict: Page text content.
        """
        try:
            # Extract the visible text using JavaScript
            text = await self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('body *'))
                    .filter(el => el.textContent.trim() && getComputedStyle(el).display !== 'none')
                    .map(el => el.textContent)
                    .join('\\n');
            }""")
            title = await self.page.title()
            return {
                "status": "success",
                "title": title,
                "text": text,
                "url": self.page.url
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def screenshot(self, path=None):
        """Take a screenshot of the current page.
        
        Args:
            path (str, optional): Path to save the screenshot. If not provided, a timestamped path will be used.
            
        Returns:
            dict: Result of the operation.
        """
        try:
            if path is None:
                # Generate a timestamped filename
                timestamp = int(time.time())
                path = os.path.join(self.screenshot_dir, f"screenshot_{timestamp}.png")
                
            await self.page.screenshot(path=path)
            return {
                "status": "success",
                "path": path
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def click(self, selector):
        """Click an element on the page.
        
        Args:
            selector (str): Selector for the element to click.
            
        Returns:
            dict: Result of the operation.
        """
        try:
            await self.page.click(selector)
            return {
                "status": "success",
                "selector": selector
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def type(self, selector, text):
        """Type text into an element.
        
        Args:
            selector (str): Selector for the element to type into.
            text (str): Text to type.
            
        Returns:
            dict: Result of the operation.
        """
        try:
            await self.page.fill(selector, text)
            return {
                "status": "success",
                "selector": selector,
                "text": text
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def evaluate(self, script):
        """Evaluate JavaScript on the page.
        
        Args:
            script (str): JavaScript to evaluate.
            
        Returns:
            dict: Result of the operation.
        """
        try:
            result = await self.page.evaluate(script)
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def wait_for_selector(self, selector, timeout=30000):
        """Wait for an element to appear on the page.
        
        Args:
            selector (str): Selector for the element to wait for.
            timeout (int, optional): Maximum time to wait in milliseconds. Defaults to 30000.
            
        Returns:
            dict: Result of the operation.
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {
                "status": "success",
                "selector": selector
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

class BrowserAgent(BaseAgent):
    """Agent for browser automation."""
    
    def __init__(
        self,
        name,
        description=None,
        model=None,
        enable_memory=True,
        agent_id=None,
        knowledge_base=None,
        headless=False
    ):
        """Initialize a new browser agent.
        
        Args:
            name (str): The name of the agent.
            description (str, optional): Description of the agent's role. Defaults to None.
            model (str, optional): LLM model to use. Defaults to None (uses system default).
            enable_memory (bool, optional): Whether to enable agent memory. Defaults to True.
            agent_id (str, optional): Unique ID for the agent. If not provided, a random UUID will be generated.
            knowledge_base (KnowledgeBase, optional): Knowledge base for the agent. Defaults to None.
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to False.
        """
        super().__init__(
            name=name,
            description=description,
            model=model,
            enable_memory=enable_memory,
            agent_id=agent_id,
            knowledge_base=knowledge_base
        )
        
        # Initialize the browser tool
        self.browser_tool = BrowserTool(headless=headless)
        self.current_page_text = None
        self.current_page_title = None
        
        # Import here to avoid circular imports
        from src.llm_integration import LLMClient
        self.llm_client = LLMClient()
        
    async def browse(self, url):
        """Browse to a URL.
        
        Args:
            url (str): URL to browse.
            
        Returns:
            dict: Result of the operation.
        """
        # Start the browser if it's not already started
        if not self.browser_tool.browser:
            await self.browser_tool.start()
            
        # Navigate to the URL
        result = await self.browser_tool.go_to(url)
        if result["status"] == "success":
            self.current_page_title = result["title"]
        return result
        
    async def get_page_content(self):
        """Get the content of the current page.
        
        Returns:
            dict: Page content.
        """
        return await self.browser_tool.get_content()
        
    async def get_page_text(self):
        """Get the text content of the current page.
        
        Returns:
            dict: Page text content.
        """
        result = await self.browser_tool.get_text()
        if result["status"] == "success":
            self.current_page_text = result["text"]
        return result
        
    async def take_screenshot(self, path=None):
        """Take a screenshot of the current page.
        
        Args:
            path (str, optional): Path to save the screenshot. If not provided, a timestamped path will be used.
            
        Returns:
            dict: Result of the operation.
        """
        return await self.browser_tool.screenshot(path)
        
    async def click_element(self, selector):
        """Click an element on the page.
        
        Args:
            selector (str): Selector for the element to click.
            
        Returns:
            dict: Result of the operation.
        """
        return await self.browser_tool.click(selector)
        
    async def type_text(self, selector, text):
        """Type text into an element.
        
        Args:
            selector (str): Selector for the element to type into.
            text (str): Text to type.
            
        Returns:
            dict: Result of the operation.
        """
        return await self.browser_tool.type(selector, text)
        
    async def run_script(self, script):
        """Run JavaScript on the page.
        
        Args:
            script (str): JavaScript to run.
            
        Returns:
            dict: Result of the operation.
        """
        return await self.browser_tool.evaluate(script)
        
    async def wait_for_element(self, selector, timeout=30000):
        """Wait for an element to appear on the page.
        
        Args:
            selector (str): CSS selector for the element to wait for.
            timeout (int, optional): Maximum time to wait in milliseconds. Defaults to 30000.
            
        Returns:
            dict: Result of the operation.
        """
        return await self.browser_tool.wait_for_selector(selector, timeout)
        
    async def stop(self):
        """Stop the browser."""
        return await self.browser_tool.stop()
        
    def execute_browsing_task(self, task_description, context=None):
        """Execute a browsing task.
        
        This method should be overridden by subclasses to implement specific browsing tasks.
        
        Args:
            task_description (str): Description of the task to execute.
            context (list, optional): Additional context for the task. Defaults to None.
            
        Returns:
            str: Result of the task execution.
        """
        if not self.current_page_text:
            return "Error: No page content available. Please browse to a page first."
        
        # Create a task with context from the current page
        page_context = f"Page title: {self.current_page_title}\nPage content:\n{self.current_page_text}\n\nTask: {task_description}"
        if context:
            page_context += f"\n\nAdditional context: {context}"
            
        task = Task(page_context)
        
        # Get model name from the stored model
        model_name = None
        if hasattr(self, 'model') and self.model:
            # Use just the model name without provider prefix if it contains a slash
            if '/' in self.model:
                model_name = self.model.split('/')[-1]
            else:
                model_name = self.model
        
        # Execute the task
        return self.llm_client.process_task(task, model_name=model_name) 