// NextJS MCP Client for connecting to local MCP servers
// Can be imported into your NextJS components

import { useState, useEffect } from 'react';

/**
 * MCP Client class for managing connections to MCP servers
 */
class McpClient {
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
    this.connected = false;
    this.capabilities = null;
    this.tools = [];
    this.resources = [];
    this.prompts = [];
    this.eventListeners = {};
  }

  /**
   * Initialize connection to the MCP server
   */
  async connect() {
    try {
      const response = await fetch(`${this.serverUrl}/initialize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clientName: 'nextjs-mcp-client',
          clientVersion: '1.0.0',
          capabilities: {
            prompts: {},
            resources: {},
            tools: {}
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to connect: ${response.statusText}`);
      }

      const data = await response.json();
      this.capabilities = data.capabilities;
      this.connected = true;
      
      // Immediately fetch available tools and resources
      await this.listTools();
      await this.listResources();
      await this.listPrompts();
      
      this._emit('connected', { capabilities: this.capabilities });
      return true;
    } catch (error) {
      console.error('MCP connection error:', error);
      this._emit('error', { error });
      return false;
    }
  }

  /**
   * List available tools from the MCP server
   */
  async listTools() {
    if (!this.connected) {
      throw new Error('Not connected to MCP server');
    }

    try {
      const response = await fetch(`${this.serverUrl}/listTools`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to list tools: ${response.statusText}`);
      }

      const data = await response.json();
      this.tools = data.tools || [];
      this._emit('toolsUpdated', { tools: this.tools });
      return this.tools;
    } catch (error) {
      console.error('Error listing tools:', error);
      this._emit('error', { error });
      throw error;
    }
  }

  /**
   * List available resources from the MCP server
   */
  async listResources() {
    if (!this.connected) {
      throw new Error('Not connected to MCP server');
    }

    try {
      const response = await fetch(`${this.serverUrl}/listResources`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to list resources: ${response.statusText}`);
      }

      const data = await response.json();
      this.resources = data.resources || [];
      this._emit('resourcesUpdated', { resources: this.resources });
      return this.resources;
    } catch (error) {
      console.error('Error listing resources:', error);
      this._emit('error', { error });
      throw error;
    }
  }

  /**
   * List available prompts from the MCP server
   */
  async listPrompts() {
    if (!this.connected) {
      throw new Error('Not connected to MCP server');
    }

    try {
      const response = await fetch(`${this.serverUrl}/listPrompts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to list prompts: ${response.statusText}`);
      }

      const data = await response.json();
      this.prompts = data.prompts || [];
      this._emit('promptsUpdated', { prompts: this.prompts });
      return this.prompts;
    } catch (error) {
      console.error('Error listing prompts:', error);
      this._emit('error', { error });
      throw error;
    }
  }

  /**
   * Call a tool on the MCP server
   */
  async callTool(toolName, args = {}) {
    if (!this.connected) {
      throw new Error('Not connected to MCP server');
    }

    try {
      const response = await fetch(`${this.serverUrl}/callTool`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: toolName,
          arguments: args
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to call tool: ${response.statusText}`);
      }

      const data = await response.json();
      this._emit('toolCalled', { name: toolName, result: data });
      return data;
    } catch (error) {
      console.error(`Error calling tool ${toolName}:`, error);
      this._emit('error', { error });
      throw error;
    }
  }

  /**
   * Read a resource from the MCP server
   */
  async readResource(resourceUri) {
    if (!this.connected) {
      throw new Error('Not connected to MCP server');
    }

    try {
      const response = await fetch(`${this.serverUrl}/readResource`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          uri: resourceUri
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to read resource: ${response.statusText}`);
      }

      const data = await response.json();
      this._emit('resourceRead', { uri: resourceUri, result: data });
      return data;
    } catch (error) {
      console.error(`Error reading resource ${resourceUri}:`, error);
      this._emit('error', { error });
      throw error;
    }
  }

  /**
   * Get a prompt from the MCP server
   */
  async getPrompt(promptName, args = {}) {
    if (!this.connected) {
      throw new Error('Not connected to MCP server');
    }

    try {
      const response = await fetch(`${this.serverUrl}/getPrompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: promptName,
          arguments: args
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to get prompt: ${response.statusText}`);
      }

      const data = await response.json();
      this._emit('promptFetched', { name: promptName, result: data });
      return data;
    } catch (error) {
      console.error(`Error getting prompt ${promptName}:`, error);
      this._emit('error', { error });
      throw error;
    }
  }

  /**
   * Disconnect from the MCP server
   */
  disconnect() {
    this.connected = false;
    this.tools = [];
    this.resources = [];
    this.prompts = [];
    this._emit('disconnected', {});
  }

  /**
   * Register an event listener
   */
  on(event, callback) {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    this.eventListeners[event].push(callback);
  }

  /**
   * Remove an event listener
   */
  off(event, callback) {
    if (!this.eventListeners[event]) return;
    this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
  }

  /**
   * Emit an event to all listeners
   */
  _emit(event, data) {
    if (!this.eventListeners[event]) return;
    this.eventListeners[event].forEach(callback => callback(data));
  }
}

/**
 * React hook for using MCP in components
 */
export function useMcpClient(serverUrl) {
  const [client, setClient] = useState(null);
  const [connected, setConnected] = useState(false);
  const [tools, setTools] = useState([]);
  const [resources, setResources] = useState([]);
  const [prompts, setPrompts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Initialize client on component mount
  useEffect(() => {
    const mcpClient = new McpClient(serverUrl);
    
    // Set up event listeners
    mcpClient.on('connected', () => setConnected(true));
    mcpClient.on('disconnected', () => setConnected(false));
    mcpClient.on('toolsUpdated', ({ tools }) => setTools(tools));
    mcpClient.on('resourcesUpdated', ({ resources }) => setResources(resources));
    mcpClient.on('promptsUpdated', ({ prompts }) => setPrompts(prompts));
    mcpClient.on('error', ({ error }) => setError(error));
    
    setClient(mcpClient);
    
    // Clean up on unmount
    return () => {
      if (mcpClient.connected) {
        mcpClient.disconnect();
      }
    };
  }, [serverUrl]);

  // Connect function
  const connect = async () => {
    if (!client) return false;
    setLoading(true);
    setError(null);
    try {
      const result = await client.connect();
      setLoading(false);
      return result;
    } catch (err) {
      setError(err);
      setLoading(false);
      return false;
    }
  };

  // Call tool function
  const callTool = async (toolName, args) => {
    if (!client || !connected) {
      setError(new Error('Not connected to MCP server'));
      return null;
    }
    
    setLoading(true);
    try {
      const result = await client.callTool(toolName, args);
      setLoading(false);
      return result;
    } catch (err) {
      setError(err);
      setLoading(false);
      return null;
    }
  };

  // Read resource function
  const readResource = async (resourceUri) => {
    if (!client || !connected) {
      setError(new Error('Not connected to MCP server'));
      return null;
    }
    
    setLoading(true);
    try {
      const result = await client.readResource(resourceUri);
      setLoading(false);
      return result;
    } catch (err) {
      setError(err);
      setLoading(false);
      return null;
    }
  };

  // Get prompt function
  const getPrompt = async (promptName, args) => {
    if (!client || !connected) {
      setError(new Error('Not connected to MCP server'));
      return null;
    }
    
    setLoading(true);
    try {
      const result = await client.getPrompt(promptName, args);
      setLoading(false);
      return result;
    } catch (err) {
      setError(err);
      setLoading(false);
      return null;
    }
  };

  return {
    client,
    connect,
    disconnect: client ? () => client.disconnect() : null,
    callTool,
    readResource,
    getPrompt,
    connected,
    tools,
    resources,
    prompts,
    error,
    loading
  };
}

/**
 * Example of using the MCP client in a NextJS component:
 *
 * ```jsx
 * import { useMcpClient } from '../scripts/nextjs_mcp_client';
 * 
 * export default function McpComponent() {
 *   const { 
 *     connect, 
 *     disconnect, 
 *     callTool, 
 *     connected, 
 *     tools, 
 *     error, 
 *     loading 
 *   } = useMcpClient('http://localhost:3001/mcp');
 *   
 *   // Connect to the server
 *   useEffect(() => {
 *     connect();
 *     return () => disconnect();
 *   }, []);
 *   
 *   // Call a tool
 *   const handleAction = async () => {
 *     const result = await callTool('navigate_to_url', { url: 'https://example.com' });
 *     console.log(result);
 *   };
 *   
 *   return (
 *     <div>
 *       <h1>MCP Client</h1>
 *       {connected ? <p>Connected!</p> : <p>Not connected</p>}
 *       {loading && <p>Loading...</p>}
 *       {error && <p>Error: {error.message}</p>}
 *       
 *       <button onClick={handleAction} disabled={!connected || loading}>
 *         Navigate to Example.com
 *       </button>
 *       
 *       <h2>Available Tools</h2>
 *       <ul>
 *         {tools.map(tool => (
 *           <li key={tool.name}>{tool.name}: {tool.description}</li>
 *         ))}
 *       </ul>
 *     </div>
 *   );
 * }
 * ```
 */

export default McpClient; 