#!/usr/bin/env python3
"""
Script to scrape Upsonic documentation, process it with LLM,
and store it as knowledge for the agent framework.
This version uses synchronous methods for browser interaction.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import AgentFramework
from src.llm_integration import LLMClient

# Configuration
DOCS_BASE_URL = "https://docs.upsonic.ai"
START_URLS = [
    "https://docs.upsonic.ai/introduction",
    "https://docs.upsonic.ai/getting-started/installation",
    "https://docs.upsonic.ai/guides/first-steps",
]
OUTPUT_DIR = Path("knowledge/upsonic")
VISITED_URLS_FILE = OUTPUT_DIR / "visited_urls.json"
MAX_PAGES = 30  # Limit to avoid excessive scraping
SCREENSHOT_DIR = os.path.join(os.getcwd(), "screenshots")

# Ensure output directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Load previously visited URLs if available
visited_urls = set()
if VISITED_URLS_FILE.exists():
    with open(VISITED_URLS_FILE, 'r') as f:
        visited_urls = set(json.load(f))

def main():
    # Initialize the framework
    framework = AgentFramework()
    llm_client = LLMClient()
    
    # Queue of URLs to visit
    urls_to_visit = [url for url in START_URLS if url not in visited_urls]
    
    # Process URLs
    page_count = 0
    extracted_links = []
    
    # Use Playwright directly
    with sync_playwright() as playwright:
        # Launch the browser
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        while urls_to_visit and page_count < MAX_PAGES:
            current_url = urls_to_visit.pop(0)
            if current_url in visited_urls:
                continue
                
            print(f"\nScraping: {current_url}")
            page_count += 1
            
            # Browse to the URL
            try:
                page.goto(current_url)
                page_title = page.title()
                print(f"Page title: {page_title}")
            except Exception as e:
                print(f"Error browsing to {current_url}: {str(e)}")
                continue
            
            # Get page content
            try:
                # Extract the visible text using JavaScript
                content = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('body *'))
                        .filter(el => el.textContent.trim() && getComputedStyle(el).display !== 'none')
                        .map(el => el.textContent)
                        .join('\\n');
                }""")
                
                if not content:
                    print(f"Failed to extract content from {current_url}")
                    continue
            except Exception as e:
                print(f"Error extracting content: {str(e)}")
                continue
            
            # Take a screenshot
            try:
                timestamp = int(time.time())
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"screenshot_{timestamp}.png")
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to: {screenshot_path}")
            except Exception as e:
                print(f"Error taking screenshot: {str(e)}")
                screenshot_path = None
            
            # Process the content with LLM
            prompt = f"""
            Extract the key information from this Upsonic documentation page.
            Focus on:
            1. Core concepts
            2. Usage examples
            3. API details
            4. Best practices
            
            Format your response as Markdown with proper sections.
            
            Here is the page content:
            
            {content[:8000]}  # Limit content to avoid token limits
            """
            
            try:
                print("Processing content with LLM...")
                processed_content = llm_client.generate_text(prompt)
                
                # Save processed content
                page_name = current_url.split('/')[-1] or 'index'
                output_file = OUTPUT_DIR / f"{page_name}.md"
                
                with open(output_file, 'w') as f:
                    f.write(f"# {page_name.replace('-', ' ').title()}\n\n")
                    f.write(f"Source: {current_url}\n\n")
                    f.write(processed_content)
                
                print(f"Saved processed content to {output_file}")
                
                # Extract links for further scraping
                extract_links_prompt = f"""
                Extract all links to other Upsonic documentation pages from this content.
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
        
        # Close the browser
        context.close()
        browser.close()
    
    # Create a summary of all pages
    print("\nCreating documentation summary...")
    summary_prompt = """
    Create a comprehensive summary of the Upsonic framework based on the documentation pages.
    Include:
    1. Overview of what Upsonic is
    2. Key components and their relationships
    3. Main features and capabilities
    4. Getting started quick guide
    5. Common use cases
    
    Format as Markdown with clear sections.
    """
    
    try:
        summary = llm_client.generate_text(summary_prompt)
        with open(OUTPUT_DIR / "summary.md", 'w') as f:
            f.write("# Upsonic Framework Summary\n\n")
            f.write(summary)
        print("Summary created successfully.")
    except Exception as e:
        print(f"Error creating summary: {str(e)}")
    
    print(f"\nScraping completed. Processed {page_count} pages.")

if __name__ == "__main__":
    main() 