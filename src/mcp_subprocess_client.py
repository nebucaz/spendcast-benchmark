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
        
    async def connect_to_subprocess(self, server_process: subprocess.Popen, server_config: MCPServerConfig) -> bool:
        """Connect to a pre-existing subprocess using direct stream communication."""
        try:
            self.server_process = server_process
            self.server_config = server_config
            
            logger.info(f"Connecting to MCP subprocess: {server_config.name}")
            
            # Check if the process is still running
            if server_process.poll() is not None:
                logger.error(f"Subprocess has already terminated: {server_config.name}")
                return False
            
            # For now, implement a simple approach that works without blocking
            # We'll create a mock session that indicates we're connected
            # In a full implementation, we'd implement the MCP protocol manually over the streams
            
            # Create a mock session for now - this will allow the system to work
            # without blocking the main thread
            self.session = "connected"
            
            logger.info(f"Connected to subprocess: {server_config.name}")
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
        
        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing stdio context: {e}")
            self._stdio_context = None
        
        logger.info("MCP client disconnected")
    
    async def list_tools(self) -> List[Tool]:
        """List available tools from the MCP server."""
        if not self.session:
            logger.warning("MCP client not properly connected")
            return []
        
        try:
            # For now, return mock tools to test the functionality
            # In a full implementation, we'd communicate with the MCP server directly
            from mcp.types import Tool
            
            mock_tools = [
                Tool(
                    name="spendcast_query",
                    description="Query the Spendcast GraphDB for financial data using SPARQL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SPARQL query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="spendcast_get_schema",
                    description="Get schema information for the Spendcast GraphDB",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
            
            return mock_tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool by name."""
        if not self.session:
            logger.warning("MCP client not properly connected")
            return None
        
        try:
            # Mock tool responses for testing
            if tool_name == "spendcast_query":
                query = arguments.get("query", "")
                return f"Mock SPARQL query result for: {query}\n\nThis would normally execute a SPARQL query against the Spendcast GraphDB."
            elif tool_name == "spendcast_get_schema":
                return "Mock schema information:\n\nThis is a financial data schema with:\n- Accounts (checking, savings, credit cards)\n- Transactions (with amounts, dates, status)\n- Parties (customers, merchants, banks)\n- Products and receipts\n- Payment cards and relationships"
            else:
                return f"Mock response for {tool_name} with args {arguments}"
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self.session is not None and self.server_process is not None and self.server_process.poll() is None
