#!/usr/bin/env python3
"""
YouTube scraper MCP server using FastMCP
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional

from mcp.server.fastmcp import FastMCP, Context, Image
from playwright.async_api import async_playwright

# Create an MCP server
mcp = FastMCP("YouTube Scraper")

# Global browser and page for reuse
browser = None
page = None


@mcp.tool()
async def navigate_to_youtube(ctx: Context) -> str:
    """Navigate to YouTube homepage"""
    global browser, page
    
    await ctx.info("Starting browser and navigating to YouTube...")
    
    if browser is None:
        # Launch browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
    
    # Navigate to YouTube
    await page.goto("https://www.youtube.com/")
    await page.wait_for_load_state("networkidle")
    
    # Take a screenshot
    screenshot = await page.screenshot()
    await ctx.update_response_content(
        media_type="image/png",
        data=screenshot
    )
    
    return "Successfully navigated to YouTube homepage"


@mcp.tool()
async def search_youtube(ctx: Context, query: str) -> str:
    """
    Search for videos on YouTube
    
    Args:
        ctx: MCP context
        query: Search query
    """
    global page
    
    if page is None:
        return "Please navigate to YouTube first using navigate_to_youtube"
    
    await ctx.info(f"Searching YouTube for: {query}")
    
    # Navigate to search results
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    await page.goto(search_url)
    await page.wait_for_load_state("networkidle")
    
    # Take a screenshot
    screenshot = await page.screenshot()
    await ctx.update_response_content(
        media_type="image/png", 
        data=screenshot
    )
    
    return f"Successfully searched for '{query}' on YouTube"


@mcp.tool()
async def scrape_video_results(ctx: Context, max_videos: int = 10) -> str:
    """
    Scrape visible video results from the current YouTube page
    
    Args:
        ctx: MCP context
        max_videos: Maximum number of videos to scrape (default: 10)
    """
    global page
    
    if page is None:
        return "Please navigate to YouTube first using navigate_to_youtube"
    
    await ctx.info("Scraping video information...")
    
    # Scroll down a bit to load more videos
    for _ in range(3):
        await page.keyboard.press("End")
        await asyncio.sleep(1)
    
    # Scrape video information using JavaScript
    videos = await page.evaluate(f"""() => {{
        const videoElements = document.querySelectorAll('ytd-video-renderer, ytd-grid-video-renderer');
        const results = [];
        
        for (let i = 0; i < Math.min(videoElements.length, {max_videos}); i++) {{
            const el = videoElements[i];
            try {{
                // Title and URL
                const titleEl = el.querySelector('#video-title, #title-wrapper a');
                const title = titleEl ? titleEl.textContent.trim() : 'Unknown Title';
                const url = titleEl ? titleEl.href : '';
                
                // Channel
                const channelEl = el.querySelector('#channel-name a, #text a');
                const channel = channelEl ? channelEl.textContent.trim() : 'Unknown Channel';
                const channelUrl = channelEl ? channelEl.href : '';
                
                // Metadata - views, date
                const metadataEl = el.querySelector('#metadata-line, #metadata');
                let viewCount = 'Unknown';
                let publishedTime = 'Unknown';
                
                if (metadataEl) {{
                    const metaSpans = metadataEl.querySelectorAll('span');
                    if (metaSpans.length >= 1) viewCount = metaSpans[0].textContent.trim();
                    if (metaSpans.length >= 2) publishedTime = metaSpans[1].textContent.trim();
                }}
                
                // Video duration
                const durationEl = el.querySelector('#overlays #text, #overlays span.ytd-thumbnail-overlay-time-status-renderer');
                const duration = durationEl ? durationEl.textContent.trim() : 'Unknown';
                
                // Thumbnail
                const thumbnailEl = el.querySelector('#img, #thumbnail img');
                const thumbnailUrl = thumbnailEl ? thumbnailEl.src : '';
                
                results.push({{
                    title,
                    url,
                    channel,
                    channelUrl,
                    viewCount,
                    publishedTime,
                    duration,
                    thumbnailUrl
                }});
            }} catch (e) {{
                results.push({{ error: e.toString() }});
            }}
        }}
        return results;
    }}""")
    
    # Format results as markdown
    if not videos:
        return "No videos found on the current page"
    
    # Take a screenshot to show what was scraped
    screenshot = await page.screenshot()
    await ctx.update_response_content(
        media_type="image/png", 
        data=screenshot
    )
    
    # Save results to a file for easy access
    results_file = os.path.expanduser("~/Documents/youtube_results.json")
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, "w") as f:
        json.dump(videos, f, indent=2)
    
    # Create markdown response
    md_response = f"# Scraped {len(videos)} YouTube Videos\n\n"
    
    for i, video in enumerate(videos, 1):
        md_response += f"## {i}. {video.get('title', 'Unknown Title')}\n"
        md_response += f"- **URL**: [{video.get('url', 'No URL')}]({video.get('url', '#')})\n"
        md_response += f"- **Channel**: {video.get('channel', 'Unknown')}\n"
        md_response += f"- **Views**: {video.get('viewCount', 'Unknown')}\n"
        md_response += f"- **Published**: {video.get('publishedTime', 'Unknown')}\n"
        md_response += f"- **Duration**: {video.get('duration', 'Unknown')}\n\n"
    
    md_response += f"\nResults saved to: {results_file}"
    
    return md_response


@mcp.tool()
async def click_video(ctx: Context, position: int = 1) -> str:
    """
    Click on a video at the specified position in the results
    
    Args:
        ctx: MCP context
        position: Position of the video to click (1-based index)
    """
    global page
    
    if page is None:
        return "Please navigate to YouTube first using navigate_to_youtube"
    
    await ctx.info(f"Clicking on video at position {position}...")
    
    # Find and click the video
    success = await page.evaluate(f"""(position) => {{
        const videoElements = document.querySelectorAll('ytd-video-renderer, ytd-grid-video-renderer');
        if (videoElements.length >= position) {{
            const titleEl = videoElements[position-1].querySelector('#video-title, #title-wrapper a');
            if (titleEl) {{
                titleEl.click();
                return true;
            }}
        }}
        return false;
    }}, {position}""")
    
    if not success:
        return f"Could not find a video at position {position}"
    
    # Wait for video page to load
    await page.wait_for_load_state("networkidle")
    
    # Take a screenshot
    screenshot = await page.screenshot()
    await ctx.update_response_content(
        media_type="image/png", 
        data=screenshot
    )
    
    # Get video info
    video_info = await page.evaluate("""() => {
        const title = document.querySelector('h1.ytd-watch-metadata yt-formatted-string')?.textContent || 'Unknown';
        const channel = document.querySelector('#channel-name yt-formatted-string')?.textContent || 'Unknown';
        const views = document.querySelector('#info-container #info-text')?.textContent || 'Unknown';
        return { title, channel, views };
    }""")
    
    return f"Successfully opened video: {video_info.get('title', 'Unknown')}\nChannel: {video_info.get('channel', 'Unknown')}"


@mcp.tool()
async def scrape_video_comments(ctx: Context, max_comments: int = 5) -> str:
    """
    Scrape comments from the current YouTube video
    
    Args:
        ctx: MCP context
        max_comments: Maximum number of comments to scrape (default: 5)
    """
    global page
    
    if page is None:
        return "Please navigate to YouTube first using navigate_to_youtube"
    
    await ctx.info("Scraping video comments...")
    
    # Scroll down to load comments
    await page.evaluate("""() => {
        document.querySelector('#comments').scrollIntoView();
    }""")
    
    # Wait for comments to load
    await asyncio.sleep(3)
    
    # Scrape comments
    comments = await page.evaluate(f"""(maxComments) => {{
        const commentElements = document.querySelectorAll('ytd-comment-thread-renderer');
        const results = [];
        
        for (let i = 0; i < Math.min(commentElements.length, maxComments); i++) {{
            const el = commentElements[i];
            try {{
                const authorEl = el.querySelector('#author-text');
                const author = authorEl ? authorEl.textContent.trim() : 'Unknown';
                
                const contentEl = el.querySelector('#content');
                const content = contentEl ? contentEl.textContent.trim() : 'No content';
                
                const likesEl = el.querySelector('#vote-count-middle');
                const likes = likesEl ? likesEl.textContent.trim() : '0';
                
                const timeEl = el.querySelector('.published-time-text');
                const time = timeEl ? timeEl.textContent.trim() : 'Unknown time';
                
                results.push({{ author, content, likes, time }});
            }} catch (e) {{
                results.push({{ error: e.toString() }});
            }}
        }}
        return results;
    }}, {max_comments}""")
    
    # Format results as markdown
    if not comments:
        return "No comments found for this video"
    
    # Take a screenshot
    screenshot = await page.screenshot()
    await ctx.update_response_content(
        media_type="image/png", 
        data=screenshot
    )
    
    # Create markdown response
    md_response = f"# Scraped {len(comments)} Comments\n\n"
    
    for i, comment in enumerate(comments, 1):
        md_response += f"## Comment {i}\n"
        md_response += f"- **Author**: {comment.get('author', 'Unknown')}\n"
        md_response += f"- **Time**: {comment.get('time', 'Unknown')}\n"
        md_response += f"- **Likes**: {comment.get('likes', '0')}\n"
        md_response += f"- **Content**: {comment.get('content', 'No content')}\n\n"
    
    return md_response


@mcp.tool()
async def close_browser(ctx: Context) -> str:
    """Close the browser"""
    global browser, page
    
    if browser is None:
        return "Browser is not running"
    
    ctx.info("Closing browser...")
    
    await browser.close()
    browser = None
    page = None
    
    return "Browser closed successfully"


if __name__ == "__main__":
    mcp.run() 