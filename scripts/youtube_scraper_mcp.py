#!/usr/bin/env python3
"""
YouTube scraper MCP server using FastMCP
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP, Context, Image
from pathlib import Path
from playwright.async_api import async_playwright

# Initialize the FastMCP server
mcp = FastMCP("YouTube Scraper")

class YoutubeScraperState:
    def __init__(self):
        self.browser = None
        self.page = None
        self.results = []
        self.comments = []

# Create a global state to store browser sessions
state = YoutubeScraperState()

@mcp.tool()
async def navigate_to_youtube(ctx: Context) -> str:
    """Navigate to YouTube homepage"""
    await ctx.info("Navigating to YouTube...")
    
    # Start Playwright and open browser if not already open
    if state.browser is None:
        playwright = await async_playwright().start()
        state.browser = await playwright.chromium.launch(headless=True)
        state.page = await state.browser.new_page()
    
    # Navigate to YouTube
    await state.page.goto("https://www.youtube.com")
    await state.page.wait_for_load_state("networkidle")
    
    # Take a screenshot
    screenshot = await state.page.screenshot()
    
    # Return with screenshot
    await ctx.info("Successfully navigated to YouTube")
    
    # Send screenshot as image
    image = Image(data=screenshot, format="png")
    return "Successfully navigated to YouTube homepage"

@mcp.tool()
async def search_youtube(query: str, ctx: Context) -> str:
    """Search for videos on YouTube"""
    await ctx.info(f"Searching for: {query}")
    
    if state.page is None:
        return "Browser not initialized. Please navigate to YouTube first."
    
    # Find and interact with the search box
    await state.page.click('input#search')
    await state.page.fill('input#search', query)
    await state.page.press('input#search', 'Enter')
    
    # Wait for results to load
    await state.page.wait_for_selector('ytd-video-renderer,ytd-grid-video-renderer', timeout=10000)
    await state.page.wait_for_load_state("networkidle")
    
    # Take a screenshot of search results
    screenshot = await state.page.screenshot()
    
    # Return with screenshot
    await ctx.info(f"Search results loaded for: {query}")
    
    # Send screenshot as image
    image = Image(data=screenshot, format="png")
    return f"Successfully searched for '{query}' on YouTube"

@mcp.tool()
async def scrape_video_results(ctx: Context) -> str:
    """Scrape visible video results from the current YouTube page"""
    await ctx.info("Scraping video results...")
    
    if state.page is None:
        return "Browser not initialized. Please navigate to YouTube first."
    
    # Execute JavaScript to extract video data
    results = await state.page.evaluate("""() => {
        const videos = Array.from(document.querySelectorAll('ytd-video-renderer,ytd-grid-video-renderer'));
        return videos.map((video, index) => {
            const titleElement = video.querySelector('#video-title, #title-wrapper');
            const channelElement = video.querySelector('#channel-name a, #text.ytd-channel-name a');
            const viewsElement = video.querySelector('#metadata-line span:first-child, #metadata span:first-child');
            const timeElement = video.querySelector('#metadata-line span:nth-child(2), #metadata span:nth-child(2)');
            
            return {
                position: index + 1,
                title: titleElement ? titleElement.textContent.trim() : 'Unknown',
                channel: channelElement ? channelElement.textContent.trim() : 'Unknown',
                views: viewsElement ? viewsElement.textContent.trim() : 'Unknown',
                published: timeElement ? timeElement.textContent.trim() : 'Unknown',
                url: titleElement && titleElement.href ? titleElement.href : 'Unknown'
            };
        });
    }""")
    
    # Store results in state
    state.results = results
    
    # Take a screenshot
    screenshot = await state.page.screenshot()
    
    # Format results as a string
    results_text = json.dumps(results, indent=2)
    
    # Return with screenshot
    await ctx.info(f"Found {len(results)} videos")
    
    # Send screenshot as image
    image = Image(data=screenshot, format="png")
    return f"Scraped {len(results)} videos from YouTube results page:\n\n{results_text}"

@mcp.tool()
async def click_video(position: int, ctx: Context) -> str:
    """Click on a video at the specified position in the results"""
    await ctx.info(f"Clicking on video at position {position}...")
    
    if state.page is None:
        return "Browser not initialized. Please navigate to YouTube first."
    
    if not state.results or position < 1 or position > len(state.results):
        return f"Invalid position. Available videos: 1-{len(state.results) if state.results else 0}"
    
    # Execute JavaScript to click on the video
    await state.page.evaluate(f"""(position) => {{
        const videos = Array.from(document.querySelectorAll('ytd-video-renderer,ytd-grid-video-renderer'));
        if (videos.length >= position) {{
            const videoElement = videos[position-1];
            const titleElement = videoElement.querySelector('#video-title, #title-wrapper');
            if (titleElement) {{
                titleElement.click();
            }}
        }}
    }}""", position)
    
    # Wait for video to load
    await state.page.wait_for_selector('#player', timeout=10000)
    await state.page.wait_for_load_state("networkidle")
    
    # Take a screenshot
    screenshot = await state.page.screenshot()
    
    # Return with screenshot
    await ctx.info(f"Successfully clicked on video at position {position}")
    
    # Send screenshot as image
    image = Image(data=screenshot, format="png")
    return f"Successfully opened video at position {position}"

@mcp.tool()
async def scrape_video_comments(ctx: Context) -> str:
    """Scrape comments from the current YouTube video"""
    await ctx.info("Scraping video comments...")
    
    if state.page is None:
        return "Browser not initialized. Please navigate to YouTube first."
    
    # Scroll to comments section
    await state.page.evaluate("""() => {
        const commentsSection = document.querySelector('#comments');
        if (commentsSection) {
            commentsSection.scrollIntoView();
        }
    }""")
    
    # Wait for comments to load
    try:
        await state.page.wait_for_selector('ytd-comment-thread-renderer', timeout=10000)
    except:
        return "No comments found or comments are disabled for this video."
    
    # Execute JavaScript to extract comment data
    comments = await state.page.evaluate("""() => {
        const comments = Array.from(document.querySelectorAll('ytd-comment-thread-renderer'));
        return comments.slice(0, 20).map((comment, index) => {
            const authorElement = comment.querySelector('#author-text');
            const textElement = comment.querySelector('#content-text');
            const likesElement = comment.querySelector('#vote-count-middle');
            
            return {
                position: index + 1,
                author: authorElement ? authorElement.textContent.trim() : 'Unknown',
                text: textElement ? textElement.textContent.trim() : 'Unknown',
                likes: likesElement ? likesElement.textContent.trim() : '0'
            };
        });
    }""")
    
    # Store comments in state
    state.comments = comments
    
    # Take a screenshot of comments section
    await state.page.evaluate("""() => {
        const commentsSection = document.querySelector('#comments');
        if (commentsSection) {
            commentsSection.scrollIntoView();
        }
    }""")
    
    screenshot = await state.page.screenshot()
    
    # Format comments as a string
    comments_text = json.dumps(comments, indent=2)
    
    # Return with screenshot
    await ctx.info(f"Found {len(comments)} comments")
    
    # Send screenshot as image
    image = Image(data=screenshot, format="png")
    return f"Scraped {len(comments)} comments from the video:\n\n{comments_text}"

@mcp.tool()
async def close_browser(ctx: Context) -> str:
    """Close the browser"""
    await ctx.info("Closing browser...")
    
    if state.browser:
        await state.browser.close()
        state.browser = None
        state.page = None
        await ctx.info("Browser closed successfully")
        return "Browser closed successfully"
    else:
        return "Browser was not open"

if __name__ == "__main__":
    mcp.run() 