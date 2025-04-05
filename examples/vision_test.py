#!/usr/bin/env python3
"""
Example of using vision-enabled LLMs to analyze images.
"""

import sys
import os
import argparse
sys.path.append(".")

from src.llm_integration import LLMClient
from config.llm_config import get_vision_models

def main():
    """Run the vision test."""
    parser = argparse.ArgumentParser(description="Test vision capabilities with OpenRouter models")
    parser.add_argument("--image", type=str, required=True, help="Path to the image file to analyze")
    parser.add_argument("--prompt", type=str, default="Describe what you see in this image in detail.",
                        help="Prompt to ask about the image")
    parser.add_argument("--model", type=str, default="gpt-4o", 
                        help="Model to use (must support vision)")
    args = parser.parse_args()
    
    # Verify that the image exists
    if not os.path.exists(args.image):
        print(f"Error: Image file '{args.image}' not found.")
        sys.exit(1)
    
    # Get vision models
    vision_models = get_vision_models()
    print(f"Available vision models: {', '.join(vision_models)}")
    
    # Verify that the selected model supports vision
    if args.model not in vision_models:
        print(f"Warning: Model '{args.model}' may not support vision. Available vision models: {', '.join(vision_models)}")
        response = input("Do you want to continue anyway? (y/n): ")
        if response.lower() != "y":
            sys.exit(0)
    
    # Create LLM client
    client = LLMClient()
    
    # Process the image
    print(f"Using model: {args.model}")
    print(f"Analyzing image: {args.image}")
    print(f"Prompt: {args.prompt}")
    print("\nGenerating response...\n")
    
    result = client.generate(
        prompt=args.prompt,
        model_name=args.model,
        image_paths=[args.image]
    )
    
    print("=" * 80)
    print(result)
    print("=" * 80)

if __name__ == "__main__":
    main() 