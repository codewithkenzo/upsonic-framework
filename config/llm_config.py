"""
LLM configuration for use with Upsonic.
"""

from .api_keys import OPENROUTER_API_KEY

# OpenRouter model configurations
OPENROUTER_MODELS = {
    # Text-only models
    "llama3-70b": {
        "model": "meta-llama/llama-3-70b-instruct",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": False,
    },
    "llama3-8b": {
        "model": "meta-llama/llama-3-8b-instruct",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": False,
    },
    "claude-3-opus": {
        "model": "anthropic/claude-3-opus",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    "claude-3-sonnet": {
        "model": "anthropic/claude-3-sonnet",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    "claude-3-haiku": {
        "model": "anthropic/claude-3-haiku",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    "gpt-4o": {
        "model": "openai/gpt-4o",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    "gpt-4-turbo": {
        "model": "openai/gpt-4-turbo",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    "gpt-4": {
        "model": "openai/gpt-4",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": False,
    },
    "gpt-3.5-turbo": {
        "model": "openai/gpt-3.5-turbo",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": False,
    },
    "mistral-large": {
        "model": "mistralai/mistral-large",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": False,
    },
    "mistral-medium": {
        "model": "mistralai/mistral-medium",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": False,
    },
    "gemini-pro": {
        "model": "google/gemini-pro",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": False,
    },
    "gemini-1.5-pro": {
        "model": "google/gemini-1.5-pro",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    
    # Adding models without provider prefix for convenience
    "meta-llama/llama-3-70b-instruct": {
        "model": "meta-llama/llama-3-70b-instruct",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": False,
    },
    "meta-llama/llama-3-8b-instruct": {
        "model": "meta-llama/llama-3-8b-instruct",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": False,
    },
    "anthropic/claude-3-opus": {
        "model": "anthropic/claude-3-opus",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    "anthropic/claude-3-sonnet": {
        "model": "anthropic/claude-3-sonnet",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    "anthropic/claude-3-haiku": {
        "model": "anthropic/claude-3-haiku",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    "openai/gpt-4o": {
        "model": "openai/gpt-4o",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
    },
    "openai/gpt-4-turbo": {
        "model": "openai/gpt-4-turbo",
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": OPENROUTER_API_KEY,
        "supports_vision": True,
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

def get_vision_models():
    """Get a list of models that support vision/image inputs.
    
    Returns:
        List[str]: List of model names that support vision.
    """
    return [
        model_name for model_name, config in OPENROUTER_MODELS.items()
        if config.get("supports_vision", False) and '/' not in model_name
    ] 