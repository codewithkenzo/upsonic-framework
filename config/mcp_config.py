"""
MCP (Model Context Protocol) server configuration.
"""

# Available MCP servers
MCP_SERVERS = {
    "desktop_commander": {
        "name": "Desktop Commander",
        "url": "https://smithery.ai/server/@wonderwhy-er/desktop-commander",
        "description": "Execute terminal commands and manage files with diff editing capabilities."
    },
    # Add more MCP servers as needed
}

# Default MCP server to use
DEFAULT_MCP_SERVER = "desktop_commander"

def get_mcp_server_config(server_name=None):
    """Get MCP server configuration for the specified server.
    
    Args:
        server_name (str, optional): Name of the MCP server to get configuration for.
            If not provided, the default server will be used.
            
    Returns:
        dict: MCP server configuration.
    """
    if server_name is None:
        server_name = DEFAULT_MCP_SERVER
        
    if server_name in MCP_SERVERS:
        return MCP_SERVERS[server_name]
    else:
        raise ValueError(f"Unknown MCP server: {server_name}") 