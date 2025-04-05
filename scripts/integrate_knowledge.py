#!/usr/bin/env python3
"""
Script to integrate the scraped documentation knowledge into our agent framework.
"""

import os
import sys
import glob
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import AgentFramework

def load_knowledge_from_directory(directory):
    """Load all markdown files from the directory into a knowledge base"""
    knowledge = {}
    
    # Get all markdown files
    md_files = glob.glob(os.path.join(directory, "*.md"))
    
    for file_path in md_files:
        file_name = os.path.basename(file_path)
        topic_name = os.path.splitext(file_name)[0]
        
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Skip empty files
        if not content.strip():
            continue
            
        knowledge[topic_name] = content
    
    return knowledge

def main():
    # Initialize the framework
    framework = AgentFramework()
    
    # Load Upsonic knowledge
    upsonic_dir = Path("knowledge/upsonic")
    if upsonic_dir.exists():
        print("Loading Upsonic knowledge...")
        upsonic_knowledge = load_knowledge_from_directory(upsonic_dir)
        print(f"Loaded {len(upsonic_knowledge)} Upsonic knowledge documents")
        
        # Create a dedicated Upsonic knowledge base
        upsonic_kb = framework.create_knowledge_base("upsonic_docs", "Upsonic Documentation")
        
        # Add knowledge to the knowledge base
        for topic, content in upsonic_knowledge.items():
            upsonic_kb.add_knowledge(topic, content)
            print(f"Added knowledge: {topic}")
    else:
        print("Upsonic knowledge directory not found. Run scrape_docs.py first.")
    
    # Load Playwright knowledge
    playwright_dir = Path("knowledge/playwright")
    if playwright_dir.exists():
        print("\nLoading Playwright knowledge...")
        playwright_knowledge = load_knowledge_from_directory(playwright_dir)
        print(f"Loaded {len(playwright_knowledge)} Playwright knowledge documents")
        
        # Create a dedicated Playwright knowledge base
        playwright_kb = framework.create_knowledge_base("playwright_docs", "Playwright Documentation")
        
        # Add knowledge to the knowledge base
        for topic, content in playwright_knowledge.items():
            playwright_kb.add_knowledge(topic, content)
            print(f"Added knowledge: {topic}")
    else:
        print("Playwright knowledge directory not found. Run scrape_playwright_docs.py first.")
    
    # Create agents with specialized knowledge
    print("\nCreating specialized agents...")
    
    # Upsonic expert agent
    if upsonic_dir.exists():
        upsonic_agent_id = framework.create_agent(
            name="UpsonicExpert",
            description="Expert on the Upsonic framework with comprehensive knowledge of its documentation",
            model_name="gpt-4",
            enable_memory=True,
            knowledge_base="upsonic_docs"
        )
        print(f"Created Upsonic expert agent with ID: {upsonic_agent_id}")
    
    # Playwright expert agent
    if playwright_dir.exists():
        playwright_agent_id = framework.create_agent(
            name="PlaywrightExpert",
            description="Expert on the Playwright framework with comprehensive knowledge of its documentation",
            model_name="gpt-4",
            enable_memory=True,
            knowledge_base="playwright_docs"
        )
        print(f"Created Playwright expert agent with ID: {playwright_agent_id}")
    
    # Full-stack agent with both knowledge bases
    if upsonic_dir.exists() and playwright_dir.exists():
        # Create a combined knowledge base
        combined_kb = framework.create_knowledge_base("combined_docs", "Combined Documentation")
        
        # Add all knowledge
        for topic, content in upsonic_knowledge.items():
            combined_kb.add_knowledge(f"upsonic_{topic}", content)
        
        for topic, content in playwright_knowledge.items():
            combined_kb.add_knowledge(f"playwright_{topic}", content)
        
        # Create the full-stack agent
        fullstack_agent_id = framework.create_agent(
            name="FullStackExpert",
            description="Expert on both Upsonic and Playwright frameworks with comprehensive knowledge",
            model_name="gpt-4",
            enable_memory=True,
            knowledge_base="combined_docs"
        )
        print(f"Created full-stack expert agent with ID: {fullstack_agent_id}")
    
    print("\nIntegration complete!")

if __name__ == "__main__":
    main() 