# Upsonic Agent Framework

A modular framework for building AI agent teams that can work together to handle complex tasks. Built on top of the Upsonic library and supporting MCP (Model Context Protocol) tools.

## Features

- **Modular Agent Architecture**: Create specialized agents for different tasks
- **MCP Tool Integration**: Use various MCP servers for extended capabilities
- **Parallel Task Execution**: Run multiple agent tasks concurrently
- **Knowledge Base Management**: Provide agents with relevant information
- **Memory Support**: Agents can maintain context over time
- **Direct LLM Calls**: Make direct calls to LLMs for simpler tasks
- **Browser Agent**: Web browsing capabilities using Playwright
- **Vision Capabilities**: Process and analyze images with vision-enabled LLMs

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/upsonic-framework.git
cd upsonic-framework

# Create a virtual environment and activate it
uv venv
source .venv/bin/activate.fish  # For fish shell users
# Or for bash users: source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Install Playwright browser
python -m playwright install chromium
```

## Usage

Here's a simple example of using the framework:

```python
from src.main import framework
from upsonic import KnowledgeBase

# Create a knowledge base
kb = KnowledgeBase(
    sources=[
        {
            "content": "Your knowledge content here"
        }
    ]
)

# Create an agent
agent = framework.create_agent(
    name="My Agent",
    description="A helpful assistant",
    model_name="llama3-70b",  # Using OpenRouter model
    enable_memory=True,
    knowledge_base=kb
)

# Execute a task
result = agent.execute_task("What can you tell me about this knowledge?")
print(result)

# Make a direct LLM call
direct_result = agent.direct_llm_call("Summarize the knowledge in one sentence")
print(direct_result)
```

### Vision Capabilities

You can use vision-enabled models to analyze images:

```python
from src.llm_integration import LLMClient
from config.llm_config import get_vision_models

# Get available vision models
vision_models = get_vision_models()
print(f"Available vision models: {', '.join(vision_models)}")

# Create LLM client
client = LLMClient()

# Process an image
result = client.generate(
    prompt="Describe what you see in this image in detail.",
    model_name="gpt-4o",  # Use a vision-capable model
    image_paths=["path/to/your/image.jpg"]
)
print(result)
```

### Browser Agent Example

```python
import asyncio
from src.main import framework

async def main():
    # Create a browser agent
    browser_agent = framework.create_browser_agent(
        name="Web Explorer",
        description="An agent that can browse the web and analyze content",
        model_name="gpt-4o",
        enable_memory=True,
        headless=False  # Set to True to run without UI
    )
    
    # Browse to a website
    result = await browser_agent.browse("https://docs.upsonic.ai/introduction")
    
    # Extract text content
    content_result = await browser_agent.get_page_text()
    
    # Take a screenshot
    screenshot_result = await browser_agent.take_screenshot()
    
    # Perform a task with the browser content
    summary = browser_agent.execute_browsing_task(
        "Summarize the key features of Upsonic based on this page content."
    )
    print(summary)
    
    # Always close the browser when done
    await browser_agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Command Line Interface

The framework includes a CLI for common operations:

```bash
# Create an agent
python app.py create "My Agent" --description "A helpful assistant" --model "llama3-70b" --memory

# Run a task with an agent
python app.py task <agent_id> "What is the capital of France?"

# Make a direct LLM call
python app.py direct "What is the meaning of life?" --model "gpt-4o"

# Make a direct LLM call with an image
python app.py direct "What's in this image?" --model "gpt-4o" --image "path/to/image.jpg"

# Create a browser agent and browse a website
python app.py browser https://docs.upsonic.ai/introduction --task "Summarize this page" --model "gpt-4o"

# List all agents
python app.py list

# Delete an agent
python app.py delete <agent_id>
```

## Architecture

The framework is structured into several key components:

- **BaseAgent**: Core agent class that wraps Upsonic's Agent
- **MCPToolAgent**: Extends BaseAgent with MCP tool capabilities
- **BrowserAgent**: Extends BaseAgent with web browsing capabilities
- **KnowledgeManager**: Manages knowledge bases for agents
- **ParallelTaskExecutor**: Handles parallel task execution
- **AgentFramework**: Main entry point for creating and managing agents

## Configuration

You can configure the framework by editing the files in the `config` directory:

- **api_keys.py**: Store your API keys
- **llm_config.py**: Configure LLM models (like OpenRouter)
- **mcp_config.py**: Configure MCP servers

## Examples

The `examples` directory contains example scripts demonstrating how to use the framework:

- **simple_agent.py**: Basic usage of agents, knowledge bases, and parallel tasks
- **browser_agent_example.py**: Example of using the browser agent
- **cli_browser_agent.sh**: Shell script showcasing CLI browser agent commands
- **vision_test.py**: Example of analyzing images with vision-enabled LLMs

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 