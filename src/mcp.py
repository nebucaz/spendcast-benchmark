"""Consolidated MCP (Model Context Protocol) client and manager."""

import asyncio
import logging
import os
import subprocess
import threading
import time
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


def load_mcp_configs() -> Dict[str, MCPServerConfig]:
    """Load MCP server configurations from config.json."""
    import json
    from pathlib import Path
    
    config_file = Path("config.json")
    if not config_file.exists():
        logger.warning("config.json not found, using empty configuration")
        return {}
    
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        configs = {}
        for server_name, server_config in config_data.get("mcpServers", {}).items():
            configs[server_name] = MCPServerConfig(server_name, server_config)
            logger.info(f"Loaded MCP server config: {server_name}")
        
        return configs
    except Exception as e:
        logger.error(f"Failed to load MCP configurations: {e}")
        return {}


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


class MCPOnDemandClient:
    """On-demand MCP client that starts servers only when needed."""
    
    def __init__(self):
        """Initialize the on-demand MCP client."""
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self.server_config: Optional[MCPServerConfig] = None
        self.server_process: Optional[subprocess.Popen] = None
        self._stdio_context = None
        
    async def connect_to_server(self, config: Dict[str, Any]) -> bool:
        """Connect to an MCP server using configuration."""
        try:
            # Create server config from dict
            self.server_config = MCPServerConfig("temp", config)
            
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
            
            # Connect using stdio_client
            self._stdio_context = stdio_client(server_params)
            streams = await self._stdio_context.__aenter__()
            
            if isinstance(streams, tuple) and len(streams) == 2:
                read_stream, write_stream = streams
                self.session = ClientSession(read_stream, write_stream)
                await self.session.initialize()
                
                logger.info(f"Connected to MCP server: {self.server_config.name}")
                return True
            else:
                logger.error(f"Unexpected return type from stdio_client: {type(streams)}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
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
    
    async def dispose(self):
        """Dispose of the client and clean up resources."""
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
        
        logger.info("MCP on-demand client disposed")


class MCPOnDemandManager:
    """Manager for on-demand MCP servers."""
    
    def __init__(self, configs: Dict[str, MCPServerConfig]):
        """Initialize the on-demand MCP manager."""
        self.configs = configs
        self.clients = {}
        
        # Create on-demand clients for each server config
        for server_name, config in configs.items():
            self.clients[server_name] = MCPOnDemandClient()
            logger.info(f"Created on-demand client for: {server_name}")
    
    async def get_available_tools(self) -> List[Any]:
        """Get all available tools from all servers."""
        all_tools = []

        for server_name, client in self.clients.items():
            try:
                # Connect for this server (client expects dict-like config)
                cfg = self.configs[server_name]
                cfg_payload = {
                    "command": cfg.command,
                    "args": cfg.args,
                    "env": cfg.env,
                }
                await client.connect_to_server(cfg_payload)
                tools_response = await client.list_tools()

                # tools_response.tools is a list of Tool objects
                for tool in getattr(tools_response, "tools", []):
                    tool_dict: Dict[str, Any] = {
                        "name": getattr(tool, "name", "unknown"),
                        "description": getattr(tool, "description", ""),
                        "inputSchema": getattr(tool, "inputSchema", {}),
                        "server": server_name,
                    }
                    all_tools.append(tool_dict)
            except Exception as e:
                logger.error(f"Failed to get tools from {server_name}: {e}")
            finally:
                try:
                    await client.dispose()
                except Exception:
                    pass

        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool by name across all servers."""
        for server_name, client in self.clients.items():
            try:
                logger.info(f"Attempting to call tool {tool_name} on server {server_name}")
                cfg = self.configs[server_name]
                cfg_payload = {
                    "command": cfg.command,
                    "args": cfg.args,
                    "env": cfg.env,
                }
                await client.connect_to_server(cfg_payload)

                result = await client.call_tool(tool_name, arguments)

                # Extract textual content from MCP result if present
                content_text: Optional[str] = None
                if result is not None:
                    try:
                        contents = getattr(result, "content", [])
                        if contents:
                            first = contents[0]
                            content_text = getattr(first, "text", None) or str(first)
                    except Exception:
                        # Fall back if structure differs
                        content_text = str(result)

                if content_text:
                    logger.info(f"Tool call successful on {server_name}")
                    return content_text
            except Exception as e:
                logger.error(f"Failed to call tool {tool_name} on {server_name}: {e}")
            finally:
                try:
                    await client.dispose()
                except Exception:
                    pass
        
        logger.warning(f"Tool {tool_name} not found on any server")
        return None
    
    async def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all servers (always shows as available for on-demand)."""
        status = {}
        for server_name in self.configs.keys():
            status[server_name] = {
                "running": True,  # On-demand servers are always "available"
                "mcp_connected": True,
                "pid": None,  # No persistent PID for on-demand
                "exit_code": None,
                "type": "on_demand"
            }
        return status
    
    def get_available_resources(self) -> List[Any]:
        """Get available resources (placeholder for compatibility)."""
        # For now, return empty list as we don't have resources implemented
        return []
    
    async def shutdown(self):
        """Shutdown all on-demand clients."""
        for client in self.clients.values():
            try:
                await client.dispose()
            except Exception as e:
                logger.error(f"Error shutting down client: {e}")
        logger.info("All on-demand MCP clients shut down")


class MCPServerManager:
    """Legacy MCP server manager for CLI compatibility."""
    
    def __init__(self):
        """Initialize the MCP server manager."""
        self.servers: Dict[str, MCPClient] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        self.available_tools: List[Tool] = []
        self.available_resources: List[Any] = []
        
    def _load_mcp_config(self) -> Dict[str, MCPServerConfig]:
        """Load MCP server configurations from config.json."""
        return load_mcp_configs()
    
    async def start_all_servers(self) -> bool:
        """Start all configured MCP servers."""
        try:
            # Load configurations
            self.server_configs = self._load_mcp_config()
            if not self.server_configs:
                logger.warning("No MCP servers to start")
                return False
            
            # Start each server
            success_count = 0
            for server_name, config in self.server_configs.items():
                try:
                    logger.info(f"Starting MCP server: {server_name}")
                    
                    # Create MCP client
                    client = MCPClient()
                    client.server_config = config
                    
                    # Connect to server
                    success = await client.connect()
                    if success:
                        self.servers[server_name] = client
                        success_count += 1
                        logger.info(f"Successfully started MCP server: {server_name}")
                    else:
                        logger.error(f"Failed to start MCP server: {server_name}")
                        
                except Exception as e:
                    logger.error(f"Error starting MCP server {server_name}: {e}")
            
            logger.info(f"Started {success_count}/{len(self.server_configs)} MCP servers")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to start MCP servers: {e}")
            return False
    
    async def stop_all_servers(self):
        """Stop all running MCP servers."""
        logger.info("Stopping all MCP servers...")
        
        for server_name, client in self.servers.items():
            try:
                await client.disconnect()
                logger.info(f"Stopped MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error stopping MCP server {server_name}: {e}")
        
        self.servers.clear()
        self.available_tools.clear()
        self.available_resources.clear()
        logger.info("All MCP servers stopped")
    
    async def discover_all_capabilities(self):
        """Discover capabilities from all servers."""
        all_tools = []
        
        for server_name, client in self.servers.items():
            try:
                tools = await client.list_tools()
                for tool in tools:
                    # Add server context to tool
                    tool.server_name = server_name
                    all_tools.append(tool)
            except Exception as e:
                logger.error(f"Failed to get tools from {server_name}: {e}")
        
        self.available_tools = all_tools
        logger.info(f"Discovered {len(all_tools)} tools from {len(self.servers)} servers")
    
    def get_available_tools(self) -> List[Tool]:
        """Get available tools."""
        return self.available_tools
    
    def get_tools_by_server(self, server_name: str) -> List[Tool]:
        """Get tools from a specific server."""
        return [tool for tool in self.available_tools if getattr(tool, 'server_name', '') == server_name]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get tool descriptions."""
        descriptions = {}
        for tool in self.available_tools:
            server_name = getattr(tool, 'server_name', 'unknown')
            descriptions[f"{tool.name} ({server_name})"] = tool.description
        return descriptions
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool by name across all servers."""
        for server_name, client in self.servers.items():
            try:
                result = await client.call_tool(tool_name, arguments)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Failed to call tool {tool_name} on {server_name}: {e}")
        return None
    
    def get_available_resources(self) -> List[Any]:
        """Get available resources (placeholder for compatibility)."""
        return self.available_resources
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_all_servers()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_all_servers()
