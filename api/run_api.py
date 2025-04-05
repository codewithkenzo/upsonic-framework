#!/usr/bin/env python3
"""
Launcher script for the Upsonic API server
"""

import argparse
import os
import sys

# Add the parent directory to the path so we can import the server module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.simple_server import run_server

def main():
    parser = argparse.ArgumentParser(description="Run the Upsonic API server")
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to run the server on (default: 8000)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting Upsonic API server on port {args.port}")
    run_server(port=args.port)

if __name__ == "__main__":
    main() 