"""
Module for direct integration with LLMs via OpenRouter.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List, Union

from src.agent_base import Task

# Import API keys from config
import sys
sys.path.append(".")
from config.api_keys import OPENROUTER_API_KEY
from config.llm_config import get_model_config, DEFAULT_MODEL

class LLMClient:
    """Client for interacting with LLMs via OpenRouter."""
    
    def __init__(self, api_key=None):
        """Initialize the LLM client.
        
        Args:
            api_key (str, optional): OpenRouter API key. If not provided, it will be taken from config.
        """
        self.api_key = api_key or OPENROUTER_API_KEY
        
    def generate(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Generate text from the LLM.
        
        Args:
            prompt (str): The prompt to send to the LLM.
            model_name (str, optional): Name of the model to use. If not provided, the default model will be used.
            system_prompt (str, optional): System prompt to use. Defaults to None.
            max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 1000.
            temperature (float, optional): Temperature for generation. Defaults to 0.7.
            stop_sequences (List[str], optional): Sequences that will stop generation. Defaults to None.
            
        Returns:
            str: Generated text.
        """
        # Get model configuration
        model_config = get_model_config(model_name or DEFAULT_MODEL)
        model = model_config.get("model")
        api_base = model_config.get("api_base")
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request body
        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if stop_sequences:
            body["stop"] = stop_sequences
            
        # Make the request
        try:
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=body
            )
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Extract the generated text
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error generating text: {e}")
            return f"Error generating text: {e}"
            
    def process_task(self, task: Task, model_name: Optional[str] = None) -> str:
        """Process a task using the LLM.
        
        Args:
            task (Task): The task to process.
            model_name (str, optional): Name of the model to use. If not provided, the default model will be used.
            
        Returns:
            str: Generated text.
        """
        # Extract context from the task
        context_text = ""
        if task.context:
            for ctx_item in task.context:
                if hasattr(ctx_item, 'sources'):
                    # Handle KnowledgeBase objects
                    for source in ctx_item.sources:
                        if isinstance(source, dict) and 'content' in source:
                            context_text += f"\n{source['content']}"
                        elif isinstance(source, str):
                            # Try to read file if it exists
                            if os.path.exists(source):
                                try:
                                    with open(source, 'r') as f:
                                        context_text += f"\n{f.read()}"
                                except Exception as e:
                                    context_text += f"\nError reading file {source}: {e}"
                            else:
                                context_text += f"\n{source}"
                else:
                    # Handle other context items
                    context_text += f"\n{str(ctx_item)}"
        
        # Create the final prompt with context
        final_prompt = task.description
        if context_text:
            final_prompt = f"Context information:\n{context_text}\n\nTask: {task.description}"
            
        # Generate the response
        return self.generate(
            prompt=final_prompt,
            model_name=model_name
        ) 