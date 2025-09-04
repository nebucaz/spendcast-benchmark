"""MCP (Model Context Protocol) client for tool integration."""

import logging
import os
import subprocess
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, TextContent

from .config import get_settings

logger = logging.getLogger(__name__)


class MCPServerConfig:
    """Configuration for an MCP server."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize MCP server configuration."""
        self.name = name
        self.command = config.get("command", "")
        self.args = config.get("args", [])
        self.env = config.get("env", {})
        self.cwd = config.get("cwd", None)
    
    def __repr__(self):
        return f"MCPServerConfig(name='{self.name}', command='{self.command}', args={self.args}, cwd='{self.cwd}')"


class MCPClient:
    """MCP client for managing connections and tool interactions."""
    
    def __init__(self):
        """Initialize the MCP client."""
        self.settings = get_settings()
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self.server_config: Optional[MCPServerConfig] = None
        self.server_process: Optional[subprocess.Popen] = None
        
    async def connect(self) -> bool:
        """Connect to the MCP server using the provided configuration."""
        if not self.server_config:
            logger.error("No server configuration provided")
            return False
            
        try:
            logger.info(f"Connecting to MCP server: {self.server_config.name}")
            
            # Merge environment variables
            env = os.environ.copy()
            env.update(self.server_config.env)
            
            # Create MCP client session parameters
            server_params = StdioServerParameters(
                command=self.server_config.command,
                args=self.server_config.args,
                env=env
            )
            
            # Use stdio_client but run it in a way that doesn't block the main thread
            # The key is to not let the MCP server output interfere with our CLI
            async with stdio_client(server_params) as (read_stream, write_stream):
                # Create a client session manually
                from mcp import ClientSession
                self.session = ClientSession(read_stream, write_stream)
                
                # Initialize the session
                await self.session.initialize()
                
                logger.info(f"Successfully connected to MCP server: {self.server_config.name}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.server_config.name}: {e}")
            if self.session:
                try:
                    await self.session.aclose()
                except Exception:
                    pass
                self.session = None
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            try:
                await self.session.aclose()
            except Exception as e:
                logger.warning(f"Error closing MCP session: {e}")
            self.session = None
            logger.info("MCP client disconnected")
        
        if self.server_process:
            try:
                self.server_process.terminate()
                # Wait for the process to terminate gracefully
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    self.server_process.kill()
                    self.server_process.wait()
            except Exception as e:
                logger.warning(f"Error terminating MCP server process: {e}")
            self.server_process = None
            logger.info("MCP server process terminated")
    
    async def list_tools(self) -> List[Tool]:
        """List available tools from the MCP server."""
        if not self.session:
            logger.warning("MCP client not connected")
            return []
        
        try:
            tools = await self.session.list_tools()
            self.tools = tools
            logger.info(f"Found {len(tools)} tools: {[tool.name for tool in tools]}")
            return tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a specific tool with arguments."""
        if not self.session:
            logger.warning("MCP client not connected")
            return None
        
        try:
            logger.info(f"Calling tool '{tool_name}' with arguments: {arguments}")
            result = await self.session.call_tool(tool_name, arguments)
            
            if result.content:
                # Extract text content from the result
                for content in result.content:
                    if isinstance(content, TextContent):
                        logger.info(f"Tool '{tool_name}' returned: {content.text[:100]}...")
                        return content.text
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            return "Tool executed successfully"
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return None
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get tool names and their descriptions."""
        return {tool.name: tool.description for tool in self.tools}
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
