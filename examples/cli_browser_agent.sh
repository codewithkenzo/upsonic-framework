#!/bin/bash
# Example of using the browser agent from the command line

# Navigate to the project root directory
cd "$(dirname "$0")/.."

# Create a browser agent and browse a website
python app.py browser https://docs.upsonic.ai/introduction --task "Summarize the key capabilities and features of Upsonic based on this page content." --name "Docs Explorer" --model "gpt-4o"

# Browse GitHub with a specific task
python app.py browser https://github.com/upsonic-ai/upsonic --task "Identify the main components of the Upsonic framework based on the repository structure and README."

# Example with headless mode
python app.py browser https://news.ycombinator.com --task "Summarize the top 3 trending topics on Hacker News." --headless 