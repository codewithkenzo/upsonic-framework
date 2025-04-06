#!/usr/bin/env python3
"""
MCP Registry - Maintains a registry of available MCP servers
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_registry")

class MCPRegistry:
    """
    Registry for MCP servers
    Maintains information about available servers, their capabilities, etc.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MCP registry
        
        Args:
            config_path (str, optional): Path to the MCP configuration file
        """
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "mcp.json")
        self.servers = {}
        self.server_categories = {}
        self.load_servers()
    
    def load_servers(self):
        """Load server information from config file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Support both old and new config formats
            if "mcpServers" in config:
                server_config = config["mcpServers"]
            elif "servers" in config:
                server_config = config["servers"]
            else:
                logger.warning(f"Invalid configuration format in {self.config_path}")
                return
            
            for server_name, info in server_config.items():
                # Create standardized server info
                server_info = {
                    "name": info.get("name", server_name),
                    "description": info.get("description", ""),
                    "command": info.get("command"),
                    "args": info.get("args", []),
                    "env": info.get("env", {}),
                    "capabilities": info.get("capabilities", []),
                    "categories": info.get("categories", []),
                    "auto_start": info.get("auto_start", False)
                }
                
                self.servers[server_name] = server_info
                
                # Index by category for faster lookup
                for category in server_info.get("categories", []):
                    self.server_categories.setdefault(category.lower(), []).append(server_name)
            
            logger.info(f"Loaded {len(self.servers)} servers from registry")
        except Exception as e:
            logger.error(f"Error loading MCP registry: {str(e)}")
    
    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered servers
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of server information
        """
        return self.servers
    
    def get_server_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific server
        
        Args:
            server_name (str): Name of the server
            
        Returns:
            Optional[Dict[str, Any]]: Server information or None if not found
        """
        return self.servers.get(server_name)
    
    def get_servers_by_category(self, category: str) -> List[str]:
        """
        Get servers by category
        
        Args:
            category (str): Category to filter by
            
        Returns:
            List[str]: List of server names in the specified category
        """
        return self.server_categories.get(category.lower(), [])
    
    def get_servers_by_capability(self, capability: str) -> List[str]:
        """
        Get servers that provide a specific capability
        
        Args:
            capability (str): Capability to filter by
            
        Returns:
            List[str]: List of server names that provide the capability
        """
        servers = []
        for server_name, info in self.servers.items():
            capabilities = info.get("capabilities", [])
            if capability in capabilities or any(cap.lower() == capability.lower() for cap in capabilities):
                servers.append(server_name)
        return servers
    
    def add_server(self, server_name: str, server_info: Dict[str, Any]) -> bool:
        """
        Add a new server to the registry
        
        Args:
            server_name (str): Name of the server
            server_info (Dict[str, Any]): Server information
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        if server_name in self.servers:
            return False
        
        self.servers[server_name] = server_info
        
        # Update categories index
        for category in server_info.get("categories", []):
            self.server_categories.setdefault(category.lower(), []).append(server_name)
        
        # Persist to config
        self._save_config()
        
        return True
    
    def update_server(self, server_name: str, server_info: Dict[str, Any]) -> bool:
        """
        Update an existing server
        
        Args:
            server_name (str): Name of the server
            server_info (Dict[str, Any]): Updated server information
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        if server_name not in self.servers:
            return False
        
        # Remove from category index
        for category in self.servers[server_name].get("categories", []):
            if category.lower() in self.server_categories and server_name in self.server_categories[category.lower()]:
                self.server_categories[category.lower()].remove(server_name)
        
        # Update server info
        self.servers[server_name] = server_info
        
        # Update category index
        for category in server_info.get("categories", []):
            self.server_categories.setdefault(category.lower(), []).append(server_name)
        
        # Persist to config
        self._save_config()
        
        return True
    
    def remove_server(self, server_name: str) -> bool:
        """
        Remove a server from the registry
        
        Args:
            server_name (str): Name of the server
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        if server_name not in self.servers:
            return False
        
        # Remove from category index
        for category in self.servers[server_name].get("categories", []):
            if category.lower() in self.server_categories and server_name in self.server_categories[category.lower()]:
                self.server_categories[category.lower()].remove(server_name)
        
        # Remove server
        del self.servers[server_name]
        
        # Persist to config
        self._save_config()
        
        return True
    
    def _save_config(self):
        """Save current registry to config file"""
        try:
            # Read current config to preserve structure
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Update server information
            if "mcpServers" in config:
                config["mcpServers"] = self.servers
            elif "servers" in config:
                config["servers"] = self.servers
            else:
                # Create new config structure
                config = {"servers": self.servers}
            
            # Write back to file
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2, sort_keys=True)
        except Exception as e:
            logger.error(f"Error saving MCP registry: {str(e)}")

# Create a singleton instance
mcp_registry = MCPRegistry() 