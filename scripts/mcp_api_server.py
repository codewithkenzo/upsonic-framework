#!/usr/bin/env python
"""
MCP API Server - Proxy API for fronted-to-backend MCP communication.
Allows NextJS frontends to communicate with MCP servers running in Python.
"""

import asyncio
import json
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# MCP SDK imports
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp_api_server")

# Create FastAPI app
app = FastAPI(title="MCP API Server", description="API for NextJS to communicate with MCP servers")

# Add CORS middleware to allow cross-origin requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set this to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active MCP server connections
active_servers: Dict[str, Tuple[ClientSession, str]] = {}

# ==== Pydantic models for requests and responses ====

class InitializeRequest(BaseModel):
    clientName: str
    clientVersion: str
    capabilities: Dict[str, Any]
    serverPath: str = Field(..., description="Path to the MCP server script")

class ToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    serverName: str

class ResourceRequest(BaseModel):
    uri: str
    serverName: str

class PromptRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    serverName: str

class ListRequest(BaseModel):
    serverName: str

class ServerInfoResponse(BaseModel):
    name: str
    connected: bool
    capabilities: Dict[str, Any] = None

# ==== Helper functions ====

async def get_or_create_session(server_name: str, server_path: Optional[str] = None) -> ClientSession:
    """Get an existing session or create a new one if needed"""
    if server_name in active_servers:
        return active_servers[server_name][0]
    
    if not server_path:
        raise HTTPException(status_code=400, detail=f"Server {server_name} not found and no path provided")
    
    try:
        # Create server parameters
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_path]
        )
        
        # Create a new session
        read, write = await stdio_client(server_params)
        session = ClientSession(read, write)
        await session.initialize()
        
        # Store the session
        active_servers[server_name] = (session, server_path)
        return session
    except Exception as e:
        logger.error(f"Error creating session for {server_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create MCP session: {str(e)}")

# ==== API routes ====

@app.get("/servers")
async def list_servers():
    """List all active MCP servers"""
    return {
        "servers": [
            {
                "name": name,
                "path": path,
                "connected": True
            }
            for name, (_, path) in active_servers.items()
        ]
    }

@app.post("/initialize")
async def initialize(request: InitializeRequest):
    """Initialize a connection to an MCP server"""
    try:
        server_name = Path(request.serverPath).stem
        session = await get_or_create_session(server_name, request.serverPath)
        
        return {
            "serverId": server_name,
            "serverName": server_name,
            "capabilities": session.server_capabilities
        }
    except Exception as e:
        logger.error(f"Initialization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

@app.post("/listTools")
async def list_tools(request: ListRequest):
    """List available tools from an MCP server"""
    try:
        session = await get_or_create_session(request.serverName)
        tools = await session.list_tools()
        
        # Convert to serializable format
        tools_list = []
        for tool in tools:
            if hasattr(tool, "to_dict"):
                tools_list.append(tool.to_dict())
            else:
                # Fallback if the tool object doesn't have to_dict
                tools_list.append({
                    "name": getattr(tool, "name", str(tool)),
                    "description": getattr(tool, "description", ""),
                    "arguments": getattr(tool, "arguments", [])
                })
        
        return {"tools": tools_list}
    except Exception as e:
        logger.error(f"List tools error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@app.post("/listResources")
async def list_resources(request: ListRequest):
    """List available resources from an MCP server"""
    try:
        session = await get_or_create_session(request.serverName)
        resources = await session.list_resources()
        
        # Convert to serializable format
        resources_list = []
        for resource in resources:
            if hasattr(resource, "to_dict"):
                resources_list.append(resource.to_dict())
            else:
                # Fallback if the resource object doesn't have to_dict
                resources_list.append({
                    "uri": getattr(resource, "uri", str(resource)),
                    "description": getattr(resource, "description", "")
                })
        
        return {"resources": resources_list}
    except Exception as e:
        logger.error(f"List resources error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list resources: {str(e)}")

@app.post("/listPrompts")
async def list_prompts(request: ListRequest):
    """List available prompts from an MCP server"""
    try:
        session = await get_or_create_session(request.serverName)
        prompts = await session.list_prompts()
        
        # Convert to serializable format
        prompts_list = []
        for prompt in prompts:
            if hasattr(prompt, "to_dict"):
                prompts_list.append(prompt.to_dict())
            else:
                # Fallback if the prompt object doesn't have to_dict
                prompts_list.append({
                    "name": getattr(prompt, "name", str(prompt)),
                    "description": getattr(prompt, "description", ""),
                    "arguments": getattr(prompt, "arguments", [])
                })
        
        return {"prompts": prompts_list}
    except Exception as e:
        logger.error(f"List prompts error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")

@app.post("/callTool")
async def call_tool(request: ToolRequest):
    """Call a tool on an MCP server"""
    try:
        session = await get_or_create_session(request.serverName)
        result = await session.call_tool(request.name, arguments=request.arguments)
        
        # Convert result to serializable format
        if hasattr(result, "to_dict"):
            return result.to_dict()
        
        # Handle the case where we have a content property
        if hasattr(result, "content"):
            content = result.content
            if isinstance(content, list):
                content_list = []
                for item in content:
                    if hasattr(item, "to_dict"):
                        content_list.append(item.to_dict())
                    else:
                        # Fallback for simple content
                        content_list.append({
                            "type": getattr(item, "type", "text"),
                            "text": getattr(item, "text", str(item))
                        })
                return {"content": content_list}
        
        # Simple fallback
        return {"result": str(result)}
    except Exception as e:
        logger.error(f"Call tool error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to call tool: {str(e)}")

@app.post("/readResource")
async def read_resource(request: ResourceRequest):
    """Read a resource from an MCP server"""
    try:
        session = await get_or_create_session(request.serverName)
        content, mime_type = await session.read_resource(request.uri)
        
        return {
            "content": content,
            "mimeType": mime_type
        }
    except Exception as e:
        logger.error(f"Read resource error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to read resource: {str(e)}")

@app.post("/getPrompt")
async def get_prompt(request: PromptRequest):
    """Get a prompt from an MCP server"""
    try:
        session = await get_or_create_session(request.serverName)
        result = await session.get_prompt(request.name, arguments=request.arguments)
        
        # Convert to serializable format
        if hasattr(result, "to_dict"):
            return result.to_dict()
        
        # Handle messages if present
        if hasattr(result, "messages"):
            messages = result.messages
            messages_list = []
            for msg in messages:
                if hasattr(msg, "to_dict"):
                    messages_list.append(msg.to_dict())
                else:
                    # Fallback for simple messages
                    content = getattr(msg, "content", {})
                    if not isinstance(content, dict):
                        content = {"type": "text", "text": str(content)}
                    
                    messages_list.append({
                        "role": getattr(msg, "role", "user"),
                        "content": content
                    })
            return {"messages": messages_list}
        
        # Simple fallback
        return {"result": str(result)}
    except Exception as e:
        logger.error(f"Get prompt error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")

@app.delete("/disconnect/{server_name}")
async def disconnect_server(server_name: str):
    """Disconnect from an MCP server"""
    if server_name not in active_servers:
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
    
    try:
        session, _ = active_servers[server_name]
        del active_servers[server_name]
        return {"success": True, "message": f"Disconnected from {server_name}"}
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")

# ==== Server entrypoint ====

def start_server(host: str = "127.0.0.1", port: int = 3001):
    """Start the FastAPI server using uvicorn"""
    import uvicorn
    logger.info(f"Starting MCP API Server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP API Server for NextJS frontends")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3001, help="Port to bind to")
    
    args = parser.parse_args()
    start_server(host=args.host, port=args.port) 