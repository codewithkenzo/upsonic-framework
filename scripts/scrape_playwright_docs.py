#!/usr/bin/env python3
"""
Script to scrape Playwright documentation, process it with LLM,
and store it as knowledge for the agent framework.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import AgentFramework
from src.llm_integration import LLMClient

# Configuration
DOCS_BASE_URL = "https://playwright.dev"
START_URLS = [
    "https://playwright.dev/docs/intro",
    "https://playwright.dev/docs/api/class-playwright",
    "https://playwright.dev/docs/api/class-browser",
    "https://playwright.dev/docs/api/class-page",
]
OUTPUT_DIR = Path("knowledge/playwright")
VISITED_URLS_FILE = OUTPUT_DIR / "visited_urls.json"
MAX_PAGES = 30  # Limit to avoid excessive scraping

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load previously visited URLs if available
visited_urls = set()
if VISITED_URLS_FILE.exists():
    with open(VISITED_URLS_FILE, 'r') as f:
        visited_urls = set(json.load(f))

async def main():
    # Initialize the framework
    framework = AgentFramework()
    
    # Create a browser agent for scraping
    print("Creating browser agent...")
    agent_id = framework.create_browser_agent(
        name="PlaywrightScraperAgent",
        description="Agent for scraping Playwright documentation",
        model_name="gpt-3.5-turbo",  # Use a faster model for summarization
        enable_memory=True,
        headless=True
    )
    
    browser_agent = framework.get_agent(agent_id)
    llm_client = LLMClient()
    
    # Queue of URLs to visit
    urls_to_visit = [url for url in START_URLS if url not in visited_urls]
    
    # Process URLs
    page_count = 0
    extracted_links = []
    
    while urls_to_visit and page_count < MAX_PAGES:
        current_url = urls_to_visit.pop(0)
        if current_url in visited_urls:
            continue
            
        print(f"\nScraping: {current_url}")
        page_count += 1
        
        # Browse to the URL
        success, error = browser_agent.browse(current_url)
        if not success:
            print(f"Error browsing to {current_url}: {error}")
            continue
        
        # Get page content
        content_success, content = browser_agent.get_page_text()
        if not content_success or not content:
            print(f"Failed to extract content from {current_url}")
            continue
        
        # Take a screenshot
        screenshot_success, screenshot_path = browser_agent.take_screenshot()
        if screenshot_success:
            print(f"Screenshot saved to: {screenshot_path}")
        
        # Process the content with LLM
        prompt = f"""
        Extract the key information from this Playwright documentation page.
        Focus on:
        1. API details and parameters
        2. Code examples
        3. Best practices
        4. Usage patterns
        
        Format your response as Markdown with proper sections.
        
        Here is the page content:
        
        {content[:8000]}  # Limit content to avoid token limits
        """
        
        try:
            print("Processing content with LLM...")
            processed_content = llm_client.generate_text(prompt)
            
            # Save processed content
            # Extract the last path component for the filename
            # Remove any query parameters
            page_path = current_url.split('/')[-1].split('?')[0]
            page_name = page_path or 'index'
            output_file = OUTPUT_DIR / f"{page_name}.md"
            
            with open(output_file, 'w') as f:
                f.write(f"# {page_name.replace('-', ' ').title()}\n\n")
                f.write(f"Source: {current_url}\n\n")
                f.write(processed_content)
            
            print(f"Saved processed content to {output_file}")
            
            # Extract links for further scraping
            extract_links_prompt = f"""
            Extract all links to other Playwright documentation pages from this content.
            Return them as a JSON array of URLs. Only include links that start with {DOCS_BASE_URL}.
            
            Content:
            {content[:5000]}
            """
            
            links_json = llm_client.generate_text(extract_links_prompt)
            
            try:
                # Try to parse JSON from the response
                links_start = links_json.find('[')
                links_end = links_json.rfind(']') + 1
                
                if links_start >= 0 and links_end > links_start:
                    links_text = links_json[links_start:links_end]
                    extracted_links = json.loads(links_text)
                    
                    # Add new links to the queue
                    for link in extracted_links:
                        if (link.startswith(DOCS_BASE_URL) and 
                            link not in visited_urls and 
                            link not in urls_to_visit):
                            urls_to_visit.append(link)
                            print(f"Added to queue: {link}")
            except json.JSONDecodeError:
                print("Failed to extract links from LLM response")
            
            # Mark current URL as visited
            visited_urls.add(current_url)
            
            # Save visited URLs
            with open(VISITED_URLS_FILE, 'w') as f:
                json.dump(list(visited_urls), f, indent=2)
                
            # Add a short delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing {current_url}: {str(e)}")
    
    # Create a summary of all pages
    print("\nCreating documentation summary...")
    summary_prompt = """
    Create a comprehensive summary of the Playwright framework based on the documentation pages.
    Include:
    1. Overview of what Playwright is
    2. Key browser automation features
    3. Main API classes and their relationships
    4. Getting started quick guide
    5. Common use cases and patterns
    
    Format as Markdown with clear sections.
    """
    
    try:
        summary = llm_client.generate_text(summary_prompt)
        with open(OUTPUT_DIR / "summary.md", 'w') as f:
            f.write("# Playwright Framework Summary\n\n")
            f.write(summary)
        print("Summary created successfully.")
    except Exception as e:
        print(f"Error creating summary: {str(e)}")
    
    # Close the browser
    browser_agent.stop_browser()
    print(f"\nScraping completed. Processed {page_count} pages.")

if __name__ == "__main__":
    asyncio.run(main()) 