"""
Tests for the browser agent functionality.
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock

sys.path.append(".")

from src.browser_agent import BrowserTool, BrowserAgent
from src.agent_base import Task

@pytest.fixture
def mock_browser_tool():
    """Create a mock browser tool with predefined responses."""
    with patch('src.browser_agent.BrowserTool') as MockBrowserTool:
        # Configure the mock to return success responses
        mock_tool = MockBrowserTool.return_value
        
        # Create futures with a running event loop to avoid warnings
        async def create_future_result(result):
            future = asyncio.get_running_loop().create_future()
            future.set_result(result)
            return future
        
        async def mock_start():
            return await create_future_result({"status": "success"})
        mock_tool.start = MagicMock(side_effect=mock_start)
        
        async def mock_go_to(url):
            return await create_future_result({
                "status": "success", 
                "title": "Test Page", 
                "url": url
            })
        mock_tool.go_to = MagicMock(side_effect=mock_go_to)
        
        async def mock_get_text():
            return await create_future_result({
                "status": "success",
                "text": "Test content",
                "title": "Test Page"
            })
        mock_tool.get_text = MagicMock(side_effect=mock_get_text)
        
        async def mock_screenshot(path=None):
            return await create_future_result({
                "status": "success",
                "path": path or "/path/to/screenshot.png"
            })
        mock_tool.screenshot = MagicMock(side_effect=mock_screenshot)
        
        async def mock_click(selector):
            return await create_future_result({
                "status": "success",
                "selector": selector
            })
        mock_tool.click = MagicMock(side_effect=mock_click)
        
        async def mock_wait_for_selector(selector, timeout=30000):
            return await create_future_result({
                "status": "success",
                "selector": selector
            })
        mock_tool.wait_for_selector = MagicMock(side_effect=mock_wait_for_selector)
        
        async def mock_stop():
            return await create_future_result({"status": "success"})
        mock_tool.stop = MagicMock(side_effect=mock_stop)
        
        yield mock_tool

@pytest.mark.asyncio
async def test_browser_agent_browse(mock_browser_tool):
    """Test browser agent browse method."""
    # Patch the BrowserTool to use our mock
    with patch('src.browser_agent.BrowserTool', return_value=mock_browser_tool):
        agent = BrowserAgent(
            name="Test Agent",
            description="Test browser agent",
            model="gpt-4o"
        )
        
        # Test browsing
        result = await agent.browse("https://example.com")
        assert result["status"] == "success"
        assert result["title"] == "Test Page"
        
        # Ensure that the go_to method was called with the correct URL
        mock_browser_tool.go_to.assert_called_once_with("https://example.com")

@pytest.mark.asyncio
async def test_wait_for_element(mock_browser_tool):
    """Test browser agent wait_for_element method."""
    # Patch the BrowserTool to use our mock
    with patch('src.browser_agent.BrowserTool', return_value=mock_browser_tool):
        agent = BrowserAgent(
            name="Test Agent",
            description="Test browser agent",
            model="gpt-4o"
        )
        
        # Test waiting for an element
        result = await agent.wait_for_element("h1", timeout=5000)
        assert result["status"] == "success"
        assert result["selector"] == "h1"
        
        # Ensure that the wait_for_selector method was called with the correct parameters
        mock_browser_tool.wait_for_selector.assert_called_once_with("h1", 5000) 