# Upsonic Framework API

A lightweight API server for interacting with the Upsonic agent framework.

## Features

- **Direct LLM queries**: Send prompts directly to language models
- **Agent management**: Create and manage agents
- **Task execution**: Execute tasks with agents
- **Browser automation**: Create browser agents and control web browsing

## Quick Start

1. Start the API server:

```bash
python api/run_api.py --port 8000
```

2. Open the test client in your browser:

```bash
# Just open the file in your browser
api/test_client.html
```

## API Endpoints

### LLM

- `POST /api/llm/direct` - Direct LLM query
  - Request body: `{ "prompt": "Your prompt", "model": "model_name" }`

### Agents

- `GET /api/agents` - List all agents
- `POST /api/agents/create` - Create a new agent
  - Request body: `{ "name": "Agent name", "description": "Description", "model_name": "model_name", "enable_memory": false }`
- `POST /api/agents/{agent_id}/execute` - Execute a task with an agent
  - Request body: `{ "task": "Task description" }`

### Browser Agents

- `POST /api/browser_agents/create` - Create a new browser agent
  - Request body: `{ "name": "Agent name", "description": "Description", "model_name": "model_name", "enable_memory": false, "headless": true }`
- `POST /api/browser_agents/{agent_id}/browse` - Browse to a URL
  - Request body: `{ "url": "https://example.com", "get_content": true, "take_screenshot": true }`

## Integration

You can interact with the API using any HTTP client:

```python
import requests

# Direct LLM query
response = requests.post(
    "http://localhost:8000/api/llm/direct",
    json={"prompt": "What is the capital of France?"}
)
print(response.json())

# Create an agent
response = requests.post(
    "http://localhost:8000/api/agents/create",
    json={
        "name": "My Assistant",
        "description": "A helpful assistant",
        "model_name": "gpt-4",
        "enable_memory": True
    }
)
agent_id = response.json()["agent_id"]

# Execute a task
response = requests.post(
    f"http://localhost:8000/api/agents/{agent_id}/execute",
    json={"task": "Tell me about quantum physics"}
)
print(response.json()["result"])
```

## Security Note

This API has no authentication and should only be used in a secure, local environment. Do not expose this API to the internet without implementing proper authentication and authorization. 