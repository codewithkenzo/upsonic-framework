#!/usr/bin/env python3
"""
MCP Client module for interacting with MCP servers from the frontend.
"""

import os
import json
import subprocess
import threading
import time
import asyncio
import logging
import hashlib
import sys
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_client")

class MCPClient:
    """Client for interacting with MCP servers."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MCP client.
        
        Args:
            config_path (str, optional): Path to the MCP configuration file.
                If not provided, the default ~/.cursor/mcp.json will be used.
        """
        self.config_path = config_path or os.path.expanduser("~/.cursor/mcp.json")
        
        # Also check project config
        project_config = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "mcp.json")
        
        if os.path.exists(project_config):
            self.config_path = project_config
            logger.info(f"Using project configuration: {project_config}")
        
        self.config = self._load_config()
        self.running_servers = {}
        
        # Create an MCP manager instance
        try:
            # First try to import our local MCP manager
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
            from mcp_manager import MCPManager
            self._mcp_manager = MCPManager()
            logger.info("Using direct MCPManager instance")
        except ImportError:
            logger.warning("Could not import MCPManager, falling back to script-based interaction")
            self._mcp_manager = None
        
        self._mcp_manager_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "mcp_manager.py")
        self._active_servers = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the MCP configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Support both old and new config formats
            if "mcpServers" in config:
                return config["mcpServers"]
            elif "servers" in config:
                return config["servers"]
            else:
                logger.warning(f"Invalid configuration format in {self.config_path}")
                return {}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading config from {self.config_path}: {str(e)}")
            return {}
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """
        List all available MCP servers.
        
        Returns:
            List[Dict[str, Any]]: List of server information dictionaries
        """
        if hasattr(self, '_mcp_manager') and self._mcp_manager:
            return self._mcp_manager.list_servers()
        
        try:
            result = subprocess.run(
                [sys.executable, self._mcp_manager_script, 'list'],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error listing servers: {str(e)}")
            
            # Fallback to config-based listing
            servers = []
            for server_name, server_config in self.config.items():
                running = server_name in self.running_servers
                
                # Check if using new format
                if isinstance(server_config, dict) and "name" in server_config:
                    servers.append({
                        "name": server_config["name"],
                        "description": server_config.get("description", ""),
                        "status": "running" if running else "available",
                        "capabilities": server_config.get("capabilities", [])
                    })
                else:
                    # Old style config
                    servers.append({
                        "name": server_name,
                        "status": "running" if running else "available",
                        "command": server_config.get("command"),
                        "args": server_config.get("args", [])
                    })
            
            return servers
    
    def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """
        Get the status of an MCP server.
        
        Args:
            server_name (str): Name of the server
            
        Returns:
            Dict[str, Any]: Server status information
        """
        if hasattr(self, '_mcp_manager') and self._mcp_manager:
            return self._mcp_manager.get_server_status(server_name)
        
        try:
            result = subprocess.run(
                [sys.executable, self._mcp_manager_script, 'status', server_name],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error getting server status: {str(e)}")
            
            # Fallback: check if server is in config
            if server_name not in self.config:
                return {"status": "error", "message": f"Server '{server_name}' not found"}
            
            running = server_name in self.running_servers
            server_config = self.config[server_name]
            
            # Check if using new format
            if isinstance(server_config, dict) and "name" in server_config:
                return {
                    "name": server_config["name"],
                    "status": "running" if running else "available",
                    "description": server_config.get("description", ""),
                    "capabilities": server_config.get("capabilities", [])
                }
            else:
                # Old style config
                return {
                    "name": server_name,
                    "status": "running" if running else "available"
                }
    
    def start_server(self, server_name: str) -> Dict[str, Any]:
        """
        Start an MCP server.
        
        Args:
            server_name (str): Name of the server to start
            
        Returns:
            Dict[str, Any]: Status information
        """
        if hasattr(self, '_mcp_manager') and self._mcp_manager:
            return self._mcp_manager.start_server(server_name)
        
        try:
            result = subprocess.run(
                [sys.executable, self._mcp_manager_script, 'start', server_name],
                capture_output=True,
                text=True,
                check=True
            )
            status = json.loads(result.stdout.strip())
            if status.get("status") == "started" or status.get("status") == "already_running":
                self.running_servers[server_name] = True
            return status
        except Exception as e:
            logger.error(f"Error starting server: {str(e)}")
            
            # Fallback: check if server is in config
            if server_name not in self.config:
                return {"status": "error", "message": f"Server '{server_name}' not found"}
            
            server_config = self.config[server_name]
            if server_name in self.running_servers:
                return {"status": "already_running", "message": f"Server '{server_name}' is already running"}
            
            command = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env", {})
            
            if not command:
                return {"status": "error", "message": f"No command specified for server '{server_name}'"}
            
            try:
                import subprocess
                
                # Merge environment variables
                merged_env = os.environ.copy()
                merged_env.update(env)
                
                # Start the process
                full_command = [command] + args
                process = subprocess.Popen(
                    full_command,
                    env=merged_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                self.running_servers[server_name] = process
                
                return {"status": "started", "message": f"Server '{server_name}' started successfully"}
            except Exception as e:
                return {"status": "error", "message": f"Error starting server '{server_name}' directly: {str(e)}"}
    
    def stop_server(self, server_name: str) -> Dict[str, Any]:
        """
        Stop an MCP server.
        
        Args:
            server_name (str): Name of the server to stop
            
        Returns:
            Dict[str, Any]: Status information
        """
        if hasattr(self, '_mcp_manager') and self._mcp_manager:
            return self._mcp_manager.stop_server(server_name)
        
        try:
            result = subprocess.run(
                [sys.executable, self._mcp_manager_script, 'stop', server_name],
                capture_output=True,
                text=True,
                check=True
            )
            status = json.loads(result.stdout.strip())
            if status.get("status") == "stopped":
                if server_name in self.running_servers:
                    del self.running_servers[server_name]
            return status
        except Exception as e:
            logger.error(f"Error stopping server: {str(e)}")
            
            # Fallback: Stop the process directly
            if server_name not in self.running_servers:
                return {"status": "not_running", "message": f"Server '{server_name}' is not running"}
            
            process = self.running_servers[server_name]
            if not hasattr(process, "terminate"):
                del self.running_servers[server_name]
                return {"status": "error", "message": f"Server '{server_name}' cannot be terminated"}
            
            try:
                # Try to terminate the process gracefully
                process.terminate()
                
                # Wait a bit for graceful termination
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # If it doesn't terminate gracefully, force kill
                    process.kill()
                
                del self.running_servers[server_name]
                return {"status": "stopped", "message": f"Server '{server_name}' stopped successfully"}
            except Exception as e:
                return {"status": "error", "message": f"Error stopping server '{server_name}' directly: {str(e)}"}
    
    def save_content_to_file(self, content: str, prefix: str = "mcp_output", file_format: str = "md") -> Dict[str, Any]:
        """
        Save content from an MCP operation to a file.
        
        Args:
            content (str): The content to save
            prefix (str, optional): Prefix for the filename
            file_format (str, optional): File format (extension)
            
        Returns:
            Dict[str, Any]: Information about the saved file
        """
        # Create a documents directory if it doesn't exist
        output_dir = Path(os.path.expanduser("~/Documents/upsonic-outputs"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a hash of the content to ensure unique filenames
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        
        # Create a timestamp for the filename
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        # Create the filename
        filename = f"{prefix}_{timestamp}_{content_hash}.{file_format}"
        
        # Full path to the file
        file_path = output_dir / filename
        
        # Save the content
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved content to {file_path}")
            
            return {
                "status": "success",
                "file_path": str(file_path),
                "file_name": filename,
                "content_type": file_format,
                "size": len(content)
            }
        except Exception as e:
            logger.error(f"Error saving content to file: {str(e)}")
            return {
                "status": "error",
                "message": f"Error saving content: {str(e)}"
            }
    
    def save_webpage_to_file(self, url: str, content: str, format: str = "md") -> Dict[str, Any]:
        """
        Save a scraped webpage to a file.
        
        Args:
            url (str): The URL of the webpage
            content (str): The content to save
            format (str, optional): Format of the content (md, html, txt)
            
        Returns:
            Dict[str, Any]: Information about the saved file
        """
        # Extract domain from URL for the filename
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace("www.", "")
            
            # Clean up the path for filename
            path = parsed_url.path.strip("/").replace("/", "_")
            if len(path) > 30:
                path = path[:30]
            
            filename_prefix = f"webpage_{domain}_{path}"
        except:
            filename_prefix = "webpage"
        
        return self.save_content_to_file(content, prefix=filename_prefix, file_format=format) 