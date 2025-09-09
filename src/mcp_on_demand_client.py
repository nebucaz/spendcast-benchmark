"""
On-demand MCP client that starts servers only when needed.
This approach starts MCP servers in separate threads when tools are requested,
waits for the response with a timeout, then cleans up the server.
"""

import logging
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


logger = logging.getLogger(__name__)


class MCPOnDemandClient:
    """On-demand MCP client that starts servers only when tools are needed."""
    
    def __init__(self):
        """Initialize the on-demand MCP client."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, config, timeout: int = 30):
        server_params = StdioServerParameters(
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env", {})
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
    
        await self.session.initialize()

    async def list_tools(self):
        if self.session is None:
            raise RuntimeError("Session not initialized")
        return await self.session.list_tools()

    async def call_tool(self, tool_name, params):
        if self.session is None:
            raise RuntimeError("Session not initialized")
        return await self.session.call_tool(tool_name, params)

    async def dispose(self):
        """Properly close the session and its resources."""
        try:
            await self.exit_stack.aclose()
        except Exception:
            pass
        finally:
            self.session = None
