# Contributing to Upsonic Framework

Thank you for your interest in contributing to the Upsonic Framework! Here's how to get started.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/upsonic-framework.git
cd upsonic-framework
```

2. Create and activate a virtual environment:
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # For bash
# or
source .venv/bin/activate.fish  # For fish shell
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Install Playwright browser for browser agents:
```bash
python -m playwright install chromium
```

5. Set up API keys:
```bash
cp config/api_keys.py.template config/api_keys.py
```
Then edit `config/api_keys.py` with your API keys.

## Code Structure

- `src/`: Core framework code
  - `agent_base.py`: Base agent implementation
  - `browser_agent.py`: Browser agent using Playwright
  - `main.py`: Main framework and agent creation
  - `llm_integration.py`: LLM client for API calls
- `app.py`: CLI interface
- `examples/`: Example code demonstrating usage
- `config/`: Configuration files

## Running Tests

```bash
pytest tests/
```

## Code Style

We follow PEP 8 guidelines. Please ensure your code is properly formatted before submitting PRs.

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add or update tests as needed
5. Submit a pull request

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License. 