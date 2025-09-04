"""Web server for the chatbot application using FastAPI."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .mcp_subprocess_manager import MCPSubprocessManager
from .llm_client import LLMClient
from .intelligent_agent import IntelligentAgent
from .conversation import Conversation

logger = logging.getLogger(__name__)


class WebServer:
    """Web server for the chatbot application."""
    
    def __init__(self):
        """Initialize the web server."""
        self.app = FastAPI(title="Spendcast Benchmark Chatbot", version="1.0.0")
        self.mcp_manager: Optional[MCPSubprocessManager] = None
        self.llm_client: Optional[LLMClient] = None
        self.intelligent_agent: Optional[IntelligentAgent] = None
        self.active_connections: List[WebSocket] = []
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def get_index():
            """Serve the main chat interface."""
            return HTMLResponse(content=self._get_chat_html(), status_code=200)
        
        @self.app.get("/api/status")
        async def get_status():
            """Get server status."""
            if not self.mcp_manager:
                return {
                    "status": "running",
                    "mcp_servers": 0,
                    "tools_available": 0,
                    "llm_ready": self.llm_client is not None
                }
            
            tools = await self.mcp_manager.get_available_tools()
            return {
                "status": "running",
                "mcp_servers": len(self.mcp_manager.processes),
                "tools_available": len(tools),
                "llm_ready": self.llm_client is not None
            }
        
        @self.app.get("/api/servers")
        async def get_servers():
            """Get MCP server status."""
            if not self.mcp_manager:
                return {"servers": []}
            
            servers = []
            status = self.mcp_manager.get_server_status()
            for server_name, server_status in status.items():
                servers.append({
                    "name": server_name,
                    "status": "running" if server_status["running"] else "stopped",
                    "pid": server_status.get("pid", None),
                    "mcp_connected": server_status["mcp_connected"]
                })
            
            return {"servers": servers}
        
        @self.app.get("/api/tools")
        async def get_tools():
            """Get available MCP tools."""
            if not self.mcp_manager:
                return {"tools": []}
            
            tools = []
            available_tools = await self.mcp_manager.get_available_tools()
            for tool in available_tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "server": getattr(tool, 'server_name', 'unknown')
                })
            
            return {"tools": tools}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time chat."""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Receive message from client
                    data = await websocket.receive_json()
                    message = data.get("message", "")
                    
                    if not message:
                        continue
                    
                    # Process message using intelligent agent
                    if self.intelligent_agent:
                        response = await self.intelligent_agent.process_user_request(message)
                        
                        # Send response back to client
                        await websocket.send_json({
                            "type": "response",
                            "message": response
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Intelligent agent not available"
                        })
                        
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
    
    def _get_chat_html(self) -> str:
        """Get the HTML content for the chat interface."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spendcast Benchmark Chatbot</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
        }
        .chat-container {
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            border-bottom: 1px solid #eee;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }
        .message.user {
            justify-content: flex-end;
        }
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        .message.user .message-content {
            background: #007bff;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.assistant .message-content {
            background: #f1f3f4;
            color: #333;
            border-bottom-left-radius: 4px;
        }
        .input-container {
            display: flex;
            padding: 20px;
            background: #fafafa;
        }
        .input-container input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 25px;
            outline: none;
            font-size: 14px;
        }
        .input-container input:focus {
            border-color: #007bff;
        }
        .input-container button {
            margin-left: 10px;
            padding: 12px 24px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
        }
        .input-container button:hover {
            background: #0056b3;
        }
        .input-container button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .status {
            padding: 10px 20px;
            background: #e9ecef;
            font-size: 12px;
            color: #666;
            text-align: center;
        }
        .typing {
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Spendcast Benchmark Chatbot</h1>
            <p>Your intelligent AI assistant with MCP tool integration</p>
        </div>
        
        <div class="status" id="status">
            Connecting...
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message assistant">
                <div class="message-content">
                    Hello! I'm your AI assistant. How can I help you today?
                </div>
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="Type your message here..." autocomplete="off">
            <button id="sendButton" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        let ws = null;
        let isConnected = false;

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                isConnected = true;
                updateStatus('Connected');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'response') {
                    addMessage(data.message, 'assistant');
                } else if (data.type === 'error') {
                    addMessage('Error: ' + data.message, 'assistant');
                }
            };
            
            ws.onclose = function() {
                isConnected = false;
                updateStatus('Disconnected');
                // Try to reconnect after 3 seconds
                setTimeout(connect, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                updateStatus('Connection error');
            };
        }

        function updateStatus(message) {
            document.getElementById('status').textContent = message;
        }

        function addMessage(message, sender) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = message;
            
            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !isConnected) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            ws.send(JSON.stringify({ message: message }));
        }

        // Event listeners
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Connect when page loads
        connect();
    </script>
</body>
</html>
        """
    
    async def setup(self):
        """Setup the web server components."""
        try:
            # Initialize MCP subprocess manager
            self.mcp_manager = MCPSubprocessManager()
            await self.mcp_manager.start_all_servers()
            
            # Initialize LLM client
            self.llm_client = LLMClient()
            await self.llm_client.setup()
            
            # Initialize intelligent agent
            self.intelligent_agent = IntelligentAgent(self.llm_client, self.mcp_manager)
            
            logger.info("Web server setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup web server: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.llm_client:
            await self.llm_client.close()
        if self.mcp_manager:
            await self.mcp_manager.stop_all_servers()


async def start_web_server(host: str = "localhost", port: int = 8000):
    """Start the web server."""
    web_server = WebServer()
    
    # Setup components
    success = await web_server.setup()
    if not success:
        print("Failed to setup web server components")
        return
    
    # Start the server
    config = uvicorn.Config(
        web_server.app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\nShutting down web server...")
    finally:
        await web_server.cleanup()


if __name__ == "__main__":
    asyncio.run(start_web_server())
