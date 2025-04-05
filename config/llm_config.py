"""
LLM configuration for use with Upsonic.
"""

from .api_keys import OPENROUTER_API_KEY

# OpenRouter model configurations
OPENROUTER_MODELS = {
    "llama3-70b": {
        "model": "meta-llama/llama-3-70b-instruct",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
    },
    "claude-3-opus": {
        "model": "anthropic/claude-3-opus",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
    },
    "gpt-4o": {
        "model": "openai/gpt-4o",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
    },
    # Adding models without provider prefix for convenience
    "meta-llama/llama-3-70b-instruct": {
        "model": "meta-llama/llama-3-70b-instruct",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
    },
    "anthropic/claude-3-opus": {
        "model": "anthropic/claude-3-opus",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
    },
    "openai/gpt-4o": {
        "model": "openai/gpt-4o",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
    },
}

# Default model to use
DEFAULT_MODEL = "llama3-70b"

def get_model_config(model_name=None):
    """Get model configuration for the specified model.
    
    Args:
        model_name (str, optional): Name of the model to get configuration for.
            If not provided, the default model will be used.
            
    Returns:
        dict: Model configuration.
    """
    if model_name is None:
        model_name = DEFAULT_MODEL
        
    # Handle case where model name is passed with or without provider prefix
    if model_name in OPENROUTER_MODELS:
        return OPENROUTER_MODELS[model_name]
    
    # Try to normalize the model name
    for key, config in OPENROUTER_MODELS.items():
        if model_name == config["model"] or model_name == key.split('/')[-1]:
            return config
    
    # If we can't find the model, raise an error
    raise ValueError(f"Unknown model: {model_name}") 