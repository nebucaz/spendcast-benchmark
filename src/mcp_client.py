"""MCP (Model Context Protocol) client for tool integration."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, TextContent

from .config import get_settings

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP client for managing connections and tool interactions."""
    
    def __init__(self):
        """Initialize the MCP client."""
        self.settings = get_settings()
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            # For now, we'll use a placeholder connection
            # In Story 1.2, we'll connect to the spendcast-mcp server
            # For now, just mark as connected without actual server
            logger.info("MCP client placeholder connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.aclose()
            self.session = None
            logger.info("MCP client disconnected")
    
    async def list_tools(self) -> List[Tool]:
        """List available tools from the MCP server."""
        if not self.session:
            logger.warning("MCP client not connected")
            return []
        
        try:
            tools = await self.session.list_tools()
            self.tools = tools
            logger.info(f"Found {len(tools)} tools")
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
            result = await self.session.call_tool(tool_name, arguments)
            if result.content:
                # Extract text content from the result
                for content in result.content:
                    if isinstance(content, TextContent):
                        return content.text
            return "Tool executed successfully"
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return None
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
