"""MCP Client that works with pre-existing subprocesses."""

import asyncio
import logging
import subprocess
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, TextContent

from .mcp_client import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPSubprocessClient:
    """MCP client that works with pre-existing subprocesses."""
    
    def __init__(self):
        """Initialize the MCP subprocess client."""
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self.server_config: Optional[MCPServerConfig] = None
        self.server_process: Optional[subprocess.Popen] = None
        self._stdio_context = None
        
    async def connect_with_stdio_client(self, server_params: StdioServerParameters, server_name: str) -> bool:
        """Connect to MCP server using stdio_client."""
        try:
            logger.info(f"Connecting to MCP server: {server_name}")
            
            # Connect using stdio_client - this returns a tuple (read_stream, write_stream)
            self._stdio_context = stdio_client(server_params)
            streams = await self._stdio_context.__aenter__()
            
            # Check if we got a tuple (read_stream, write_stream)
            if isinstance(streams, tuple) and len(streams) == 2:
                read_stream, write_stream = streams
                
                # Create a ClientSession with the streams
                from mcp import ClientSession
                self.session = ClientSession(read_stream, write_stream)
                
                # Initialize the session
                await self.session.initialize()
                
                logger.info(f"Connected to MCP server: {server_name}")
                return True
            else:
                logger.error(f"Unexpected return type from stdio_client: {type(streams)}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def connect_to_subprocess(self, server_process: subprocess.Popen, server_config: MCPServerConfig) -> bool:
        """Connect to a pre-existing subprocess using real MCP protocol communication."""
        try:
            self.server_process = server_process
            self.server_config = server_config
            
            logger.info(f"Connecting to MCP subprocess: {server_config.name}")
            
            # If we have a server_process, check if it's still running
            if server_process is not None and server_process.poll() is not None:
                logger.error(f"Subprocess has already terminated: {server_config.name}")
                return False
            
            # Use the MCP stdio client to connect to the subprocess
            from mcp.client.stdio import stdio_client
            from mcp import StdioServerParameters
            
            # Create stdio server parameters
            server_params = StdioServerParameters(
                command=server_config.command,
                args=server_config.args or [],
                env=server_config.env or {}
            )
            
            # Create stdio client context manager
            self._stdio_context = stdio_client(server_params)
            
            # Get the streams from the stdio client
            streams = await self._stdio_context.__aenter__()
            read_stream, write_stream = streams
            
            # Create a ClientSession with the streams
            from mcp import ClientSession
            self.session = ClientSession(read_stream, write_stream)
            
            # Initialize the session
            await self.session.initialize()
            
            logger.info(f"Connected to subprocess: {server_config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to subprocess: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session and self.session != "connected":
            try:
                await self.session.aclose()
            except Exception as e:
                logger.warning(f"Error closing MCP session: {e}")
            self.session = None
        elif self.session == "connected":
            # Mock session, just clear it
            self.session = None
        
        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing stdio context: {e}")
            self._stdio_context = None
        
        logger.info("MCP client disconnected")
    
    async def list_tools(self) -> List[Tool]:
        """List available tools from the MCP server."""
        if not self.session or self.session == "connected":
            logger.warning("MCP client not properly connected")
            return []
        
        try:
            # Use real MCP session to list tools
            tools = await self.session.list_tools()
            return tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool by name."""
        if not self.session or self.session == "connected":
            logger.warning("MCP client not properly connected")
            return None
        
        try:
            # Use real MCP session to call tools
            result = await self.session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return (self.session is not None and 
                self.session != "connected" and 
                self.server_process is not None and 
                self.server_process.poll() is None)
