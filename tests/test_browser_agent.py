"""
Tests for the browser agent functionality.
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.append(".")

from src.browser_agent import BrowserTool, BrowserAgent
from src.agent_base import Task

@pytest.fixture
def mock_browser_tool():
    """Create a mock browser tool with predefined responses."""
    with patch('src.browser_agent.BrowserTool') as MockBrowserTool:
        # Configure the mock to return success responses
        mock_tool = MockBrowserTool.return_value
        
        # Set up async mock methods
        mock_tool.start = AsyncMock(return_value={"status": "success"})
        
        mock_tool.go_to = AsyncMock(return_value={
            "status": "success", 
            "title": "Test Page", 
            "url": "https://example.com"
        })
        
        mock_tool.get_text = AsyncMock(return_value={
            "status": "success",
            "text": "Test content",
            "title": "Test Page"
        })
        
        mock_tool.screenshot = AsyncMock(return_value={
            "status": "success",
            "path": "/path/to/screenshot.png"
        })
        
        mock_tool.click = AsyncMock(return_value={
            "status": "success",
            "selector": "#test-button"
        })
        
        mock_tool.wait_for_selector = AsyncMock(return_value={
            "status": "success",
            "selector": "h1"
        })
        
        mock_tool.stop = AsyncMock(return_value={"status": "success"})
        
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