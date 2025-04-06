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
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_client")

class MCPClient:
    """Client for interacting with MCP servers."""
    
    def __init__(self, config_path: Optional[str] = None, mcp_manager_script: Optional[str] = None):
        """
        Initialize the MCP client.
        
        Args:
            config_path (str, optional): Path to the MCP configuration file.
                If not provided, the default ~/.cursor/mcp.json will be used.
            mcp_manager_script (str, optional): Path to the MCP manager script
        """
        self.config_path = config_path or os.path.expanduser("~/.cursor/mcp.json")
        self.config = self._load_config()
        self.running_servers = {}
        
        # Create an MCP manager instance
        try:
            from mcp_manager import MCPManager
            self._mcp_manager = MCPManager()
            logger.info("Using direct MCPManager instance")
        except ImportError:
            logger.warning("Could not import MCPManager, falling back to script-based interaction")
            self._mcp_manager = None
        
        self._mcp_manager_script = mcp_manager_script or os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcp_manager.sh')
        self._active_servers = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """Load the MCP configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return a default config if the file doesn't exist or is invalid
            return {"mcpServers": {}}
    
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
                [self._mcp_manager_script, 'list'],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error listing servers: {str(e)}")
            return []
    
    def start_server(self, server_name: str) -> Dict[str, Any]:
        """
        Start an MCP server.
        
        Args:
            server_name (str): Name of the server to start
            
        Returns:
            Dict[str, Any]: Server status information
            
        Raises:
            ValueError: If the server is not found in the configuration
        """
        if server_name not in self.config.get("mcpServers", {}):
            raise ValueError(f"Unknown MCP server: {server_name}")
            
        if server_name in self.running_servers:
            return {"name": server_name, "status": "already_running"}
            
        server_config = self.config["mcpServers"][server_name]
        command = server_config.get("command")
        args = server_config.get("args", [])
        env = os.environ.copy()
        
        # Add any environment variables from the config
        if "env" in server_config:
            for key, value in server_config["env"].items():
                env[key] = value
                
        # Start the server process
        try:
            process = subprocess.Popen(
                [command] + args,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store the process
            self.running_servers[server_name] = {
                "process": process,
                "start_time": time.time(),
                "stdout": [],
                "stderr": []
            }
            
            # Start threads to read output
            self._start_output_threads(server_name)
            
            return {"name": server_name, "status": "started"}
        except Exception as e:
            return {"name": server_name, "status": "error", "error": str(e)}
    
    def _start_output_threads(self, server_name: str):
        """Start threads to read stdout and stderr from the server process."""
        server_info = self.running_servers[server_name]
        process = server_info["process"]
        
        def read_stdout():
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    server_info["stdout"].append(line.strip())
                    # Limit the number of stored lines
                    if len(server_info["stdout"]) > 1000:
                        server_info["stdout"].pop(0)
        
        def read_stderr():
            for line in iter(process.stderr.readline, ''):
                if line.strip():
                    server_info["stderr"].append(line.strip())
                    # Limit the number of stored lines
                    if len(server_info["stderr"]) > 1000:
                        server_info["stderr"].pop(0)
        
        # Start the threads
        threading.Thread(target=read_stdout, daemon=True).start()
        threading.Thread(target=read_stderr, daemon=True).start()
    
    def stop_server(self, server_name: str) -> Dict[str, Any]:
        """
        Stop an MCP server.
        
        Args:
            server_name (str): Name of the server to stop
            
        Returns:
            Dict[str, Any]: Server status information
        """
        if server_name not in self.running_servers:
            return {"name": server_name, "status": "not_running"}
            
        server_info = self.running_servers[server_name]
        process = server_info["process"]
        
        try:
            process.terminate()
            # Wait for the process to terminate
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
                
            # Remove from running servers
            del self.running_servers[server_name]
            
            return {"name": server_name, "status": "stopped"}
        except Exception as e:
            return {"name": server_name, "status": "error", "error": str(e)}
    
    def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """
        Get the status of an MCP server.
        
        Args:
            server_name (str): Name of the server to get status for
            
        Returns:
            Dict[str, Any]: Server status information
        """
        if server_name not in self.config.get("mcpServers", {}):
            return {"name": server_name, "status": "unknown"}
            
        if server_name in self.running_servers:
            server_info = self.running_servers[server_name]
            process = server_info["process"]
            
            # Check if the process is still running
            if process.poll() is None:
                return {
                    "name": server_name,
                    "status": "running",
                    "start_time": server_info["start_time"],
                    "uptime": time.time() - server_info["start_time"],
                    "stdout_lines": len(server_info["stdout"]),
                    "stderr_lines": len(server_info["stderr"])
                }
            else:
                # Process has exited
                exit_code = process.returncode
                # Remove from running servers
                del self.running_servers[server_name]
                
                return {
                    "name": server_name,
                    "status": "exited",
                    "exit_code": exit_code
                }
        else:
            return {"name": server_name, "status": "stopped"}
    
    def get_server_output(self, server_name: str, stream: str = "stdout", max_lines: int = 100) -> Dict[str, Any]:
        """
        Get the output from an MCP server.
        
        Args:
            server_name (str): Name of the server to get output for
            stream (str): Which stream to get output from ('stdout' or 'stderr')
            max_lines (int): Maximum number of lines to return
            
        Returns:
            Dict[str, Any]: Server output information
        """
        if server_name not in self.running_servers:
            return {"name": server_name, "status": "not_running", "lines": []}
            
        server_info = self.running_servers[server_name]
        
        if stream == "stdout":
            lines = server_info["stdout"][-max_lines:] if max_lines > 0 else server_info["stdout"]
        elif stream == "stderr":
            lines = server_info["stderr"][-max_lines:] if max_lines > 0 else server_info["stderr"]
        else:
            lines = []
            
        return {
            "name": server_name,
            "status": "running",
            "stream": stream,
            "lines": lines
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the MCP configuration.
        
        Args:
            new_config (Dict[str, Any]): New configuration to update with
            
        Returns:
            Dict[str, Any]: Updated configuration
        """
        # Merge the new config with the existing one
        if "mcpServers" in new_config:
            for server_name, server_config in new_config["mcpServers"].items():
                self.config.setdefault("mcpServers", {})[server_name] = server_config
        
        # Save the updated config
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2, sort_keys=True)
            
        return self.config 

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