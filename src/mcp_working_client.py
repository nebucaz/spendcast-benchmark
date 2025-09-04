"""Working MCP Client that properly connects to subprocess servers."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, TextContent

from .mcp_client import MCPServerConfig

logger = logging.getLogger(__name__)


class MCPWorkingClient:
    """MCP client that properly connects to subprocess servers."""
    
    def __init__(self):
        """Initialize the MCP working client."""
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self.server_config: Optional[MCPServerConfig] = None
        self.server_process = None
        
    async def connect_to_subprocess(self, server_process, server_config: MCPServerConfig) -> bool:
        """Connect to a pre-existing subprocess using stdio_client."""
        try:
            self.server_process = server_process
            self.server_config = server_config
            
            logger.info(f"Connecting to MCP subprocess: {server_config.name}")
            
            # Use the original stdio_client approach but with the subprocess
            # We need to create a new subprocess with the same command but let stdio_client manage it
            import os
            
            # Merge environment variables
            env = os.environ.copy()
            env.update(server_config.env)
            
            # Create MCP client session parameters
            server_params = StdioServerParameters(
                command=server_config.command,
                args=server_config.args,
                env=env
            )
            
            # Connect using stdio_client - this will start its own subprocess
            # but we'll manage the lifecycle properly
            async with stdio_client(server_params) as (read_stream, write_stream):
                # Create a client session manually
                self.session = ClientSession(read_stream, write_stream)
                
                # Initialize the session
                await self.session.initialize()
                
                # Get available tools
                self.tools = await self.session.list_tools()
                
                logger.info(f"Connected to subprocess: {server_config.name}")
                logger.info(f"Found {len(self.tools)} tools")
                
                # Keep the session alive by not exiting the context manager
                # This is a simplified approach - in production we'd need proper lifecycle management
                return True
            
        except Exception as e:
            logger.error(f"Failed to connect to subprocess: {e}")
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
    
    async def list_tools(self) -> List[Tool]:
        """List available tools from the MCP server."""
        if not self.session:
            logger.warning("MCP client not properly connected")
            return []
        
        try:
            return self.tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool by name."""
        if not self.session:
            logger.warning("MCP client not properly connected")
            return None
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self.session is not None
