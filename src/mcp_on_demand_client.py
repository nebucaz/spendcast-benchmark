"""
On-demand MCP client that starts servers only when needed.
This approach starts MCP servers in separate threads when tools are requested,
waits for the response with a timeout, then cleans up the server.
"""

import asyncio
import mcp
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from .mcp_client import MCPServerConfig
from .mcp_subprocess_client import MCPSubprocessClient

logger = logging.getLogger(__name__)


class MCPOnDemandClient:
    """On-demand MCP client that starts servers only when tools are needed."""
    
    def __init__(self, config: MCPServerConfig, timeout: int = 30):
        """Initialize the on-demand MCP client."""
        self.config = config
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool by starting an MCP server on-demand."""
        try:
            logger.info(f"Starting on-demand MCP server for tool: {tool_name}")
            
            # Start the MCP server in a separate thread
            future = self.executor.submit(self._run_mcp_tool_call, tool_name, arguments)
            
            # Wait for the result with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.wrap_future(future), 
                    timeout=self.timeout
                )
                logger.info(f"Tool call completed: {tool_name}")
                return result
            except asyncio.TimeoutError:
                logger.error(f"Tool call timed out after {self.timeout}s: {tool_name}")
                future.cancel()
                return None
                
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return None
    
    def _run_mcp_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Run the MCP tool call using MCP library's connect_to_server method."""
        try:
            # Use asyncio.run to handle the async connection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Use MCP library's connect_to_server method
                result = loop.run_until_complete(
                    self._connect_and_call_tool(tool_name, arguments)
                )
                
                return result
                
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Error in MCP tool call: {e}")
            return None
    
    async def _connect_and_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Connect to MCP server and call tool using MCP library's connect_to_server method."""
        from mcp.client.stdio import stdio_client
        from mcp import StdioServerParameters, ClientSession
        from contextlib import AsyncExitStack
        
        exit_stack = AsyncExitStack()
        
        try:
            # Create stdio server parameters from config
            server_params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args or [],
                env=self.config.env or {}
            )
            
            # Use stdio_client to connect to the server
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
            read_stream, write_stream = stdio_transport
            
            # Create client session
            session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            
            # Initialize the session
            await session.initialize()
            
            # List available tools to verify connection
            tools_response = await session.list_tools()
            logger.info(f"Connected to MCP server, found {len(tools_response.tools)} tools")
            
            # Log all available tools
            available_tool_names = []
            for tool in tools_response.tools:
                available_tool_names.append(tool.name)
                logger.info(f"Available tool: {tool.name} - {tool.description}")
            
            logger.info(f"Available tool names: {available_tool_names}")
            
            # Find the requested tool
            target_tool = None
            for tool in tools_response.tools:
                if tool.name == tool_name:
                    target_tool = tool
                    break
            
            if not target_tool:
                logger.error(f"Tool {tool_name} not found on MCP server. Available tools: {available_tool_names}")
                return None
            
            # Call the tool
            result = await session.call_tool(tool_name, arguments)
            
            if result.content:
                # Extract text content from result
                content = result.content[0].text if result.content[0].text else str(result.content[0])
                logger.info(f"Tool {tool_name} executed successfully")
                return content
            else:
                logger.warning(f"Tool {tool_name} returned no content")
                return None
                
        except Exception as e:
            logger.error(f"Error connecting to MCP server: {e}")
            return None
        finally:
            # Clean up resources
            await exit_stack.aclose()
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the actual MCP server."""
        try:
            # Use asyncio.run to handle the async connection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Connect to server and get real tools
                tools = loop.run_until_complete(self._get_server_tools())
                return tools
                
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Error getting tools from server: {e}")
            # Fallback to static tools if server connection fails
            return [
                {
                    "name": "execute_sparql",
                    "description": "Execute SPARQL queries against a financial data triple store containing comprehensive banking, transaction, and retail data",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SPARQL query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "execute_sparql_validated",
                    "description": "Execute SPARQL queries with validation against a financial data triple store",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SPARQL query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_schema_help",
                    "description": "Get schema documentation and query examples for the financial data store",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "get_schema_content",
                    "description": "Get the actual content of schema resources instead of just the URIs",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "resource_name": {
                                "type": "string",
                                "description": "Which resource to read. Options: 'schema_summary', 'example_queries', 'ontology'"
                            }
                        },
                        "required": ["resource_name"]
                    }
                }
            ]
    
    async def _get_server_tools(self) -> List[Dict[str, Any]]:
        """Get tools from the actual MCP server."""
        from mcp.client.stdio import stdio_client
        from mcp import StdioServerParameters, ClientSession
        from contextlib import AsyncExitStack
        
        exit_stack = AsyncExitStack()
        
        try:
            # Create stdio server parameters from config
            server_params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args or [],
                env=self.config.env or {}
            )
            
            # Use stdio_client to connect to the server
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
            read_stream, write_stream = stdio_transport
            
            # Create client session
            session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools_response = await session.list_tools()
            logger.info(f"Connected to MCP server, found {len(tools_response.tools)} tools")
            
            # Convert tools to dictionary format
            tools = []
            for tool in tools_response.tools:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                    "server": self.config.name
                }
                tools.append(tool_dict)
                logger.info(f"Found tool: {tool.name} - {tool.description}")
            
            return tools
                
        except Exception as e:
            logger.error(f"Error getting tools from MCP server: {e}")
            return []
        finally:
            # Clean up resources
            await exit_stack.aclose()
    
    def shutdown(self):
        """Shutdown the executor."""
        self.executor.shutdown(wait=True)
