#!/usr/bin/env python3
"""
Simple API server for Upsonic Framework using Python's built-in HTTP server
"""

import http.server
import json
import socketserver
import urllib.parse
from src.main import AgentFramework
from src.llm_integration import LLMClient

# Initialize framework
framework = AgentFramework()

class UpsonicRequestHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self._set_headers()
        
    def do_GET(self):
        path = self.path
        
        if path == "/" or path == "":
            # Root path - serve basic API info
            api_info = {
                "name": "Upsonic Framework API",
                "version": "1.0.0",
                "description": "API for interacting with the Upsonic agent framework",
                "endpoints": {
                    "agents": "/api/agents",
                    "llm": "/api/llm/direct",
                    "browser_agents": "/api/browser_agents/create"
                },
                "documentation": "See api/README.md for complete documentation"
            }
            self._set_headers()
            self.wfile.write(json.dumps(api_info, indent=2).encode())
            return
        
        if path.startswith("/api/agents"):
            # List all agents
            agents = framework.get_all_agents()
            self._set_headers()
            self.wfile.write(json.dumps({"agents": agents}).encode())
            return
            
        elif path.startswith("/api/models"):
            # List available models
            models = framework.get_all_models() if hasattr(framework, "get_all_models") else []
            self._set_headers()
            self.wfile.write(json.dumps({"models": models}).encode())
            return
            
        # Default 404 response
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        path = self.path
        content_length = int(self.headers.get("Content-Length", 0))
        request_body = self.rfile.read(content_length).decode("utf-8")
        
        try:
            data = json.loads(request_body)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return
        
        if path == "/api/llm/direct":
            # Direct LLM query
            if "prompt" not in data:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'prompt' field"}).encode())
                return
                
            model = data.get("model", "default")
            llm_client = LLMClient(model_name=model)
            
            try:
                response = llm_client.generate_text(data["prompt"])
                self._set_headers()
                self.wfile.write(json.dumps({"response": response}).encode())
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
                
        elif path == "/api/agents/create":
            # Create a new agent
            required_fields = ["name", "description"]
            if not all(field in data for field in required_fields):
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing required fields"}).encode())
                return
                
            try:
                agent_id = framework.create_agent(
                    name=data["name"],
                    description=data["description"],
                    model_name=data.get("model_name"),
                    enable_memory=data.get("enable_memory", False)
                )
                self._set_headers()
                self.wfile.write(json.dumps({"agent_id": agent_id}).encode())
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        
        elif path == "/api/browser_agents/create":
            # Create a new browser agent
            required_fields = ["name", "description"]
            if not all(field in data for field in required_fields):
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing required fields"}).encode())
                return
                
            try:
                agent_id = framework.create_browser_agent(
                    name=data["name"],
                    description=data["description"],
                    model_name=data.get("model_name"),
                    enable_memory=data.get("enable_memory", False),
                    headless=data.get("headless", True)
                )
                self._set_headers()
                self.wfile.write(json.dumps({"agent_id": agent_id}).encode())
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
                
        elif path.startswith("/api/agents/") and path.endswith("/execute"):
            # Execute a task with an agent
            agent_id = path.split("/")[3]
            
            if "task" not in data:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'task' field"}).encode())
                return
                
            try:
                agent = framework.get_agent(agent_id)
                if not agent:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": f"Agent {agent_id} not found"}).encode())
                    return
                    
                result = agent.execute_task(data["task"])
                self._set_headers()
                self.wfile.write(json.dumps({"result": result}).encode())
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
            
        elif path.startswith("/api/browser_agents/") and path.endswith("/browse"):
            # Execute browse with a browser agent
            agent_id = path.split("/")[3]
            
            if "url" not in data:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'url' field"}).encode())
                return
                
            try:
                agent = framework.get_agent(agent_id)
                if not agent:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": f"Agent {agent_id} not found"}).encode())
                    return
                
                if not hasattr(agent, "browse"):
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": f"Agent {agent_id} is not a browser agent"}).encode())
                    return
                
                success, error = agent.browse(data["url"])
                if not success:
                    self._set_headers(500)
                    self.wfile.write(json.dumps({"error": error}).encode())
                    return
                
                content = ""
                if "get_content" in data and data["get_content"]:
                    content_success, content_result = agent.get_page_text()
                    if content_success:
                        content = content_result
                
                screenshot = None
                if "take_screenshot" in data and data["take_screenshot"]:
                    screenshot_success, screenshot_path = agent.take_screenshot()
                    if screenshot_success:
                        screenshot = screenshot_path
                
                self._set_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "content": content,
                    "screenshot": screenshot
                }).encode())
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        
        # Default 404 response
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Not found"}).encode())

def run_server(port=8000):
    """Start the API server on the specified port"""
    with socketserver.TCPServer(("", port), UpsonicRequestHandler) as httpd:
        print(f"Server running at http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")
            httpd.shutdown()

if __name__ == "__main__":
    run_server() 