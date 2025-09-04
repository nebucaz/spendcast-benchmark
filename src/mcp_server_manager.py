"""MCP Server Manager for handling multiple MCP servers and their capabilities."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .mcp_client import MCPClient, MCPServerConfig

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages multiple MCP servers and their capabilities."""
    
    def __init__(self):
        """Initialize the MCP server manager."""
        self.servers: Dict[str, MCPClient] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        self.available_tools: List[Any] = []
        self.available_resources: List[Any] = []
        
    def _load_mcp_config(self) -> Dict[str, MCPServerConfig]:
        """Load MCP server configurations from config.json."""
        try:
            config_path = Path("config.json")
            if not config_path.exists():
                logger.warning("config.json not found")
                return {}
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            mcp_servers = config_data.get("mcpServers", {})
            if not mcp_servers:
                logger.warning("No MCP servers configured in config.json")
                return {}
            
            server_configs = {}
            for server_name, server_config in mcp_servers.items():
                logger.info(f"Loading MCP server configuration: {server_name}")
                server_configs[server_name] = MCPServerConfig(server_name, server_config)
            
            return server_configs
            
        except Exception as e:
            logger.error(f"Failed to load MCP configuration: {e}")
            return {}
    
    async def start_all_servers(self) -> bool:
        """Start all configured MCP servers."""
        try:
            # Load configurations
            self.server_configs = self._load_mcp_config()
            if not self.server_configs:
                logger.warning("No MCP servers to start")
                return False
            
            # Start each server
            for server_name, config in self.server_configs.items():
                logger.info(f"Starting MCP server: {server_name}")
                
                # Create MCP client for this server
                mcp_client = MCPClient()
                mcp_client.server_config = config
                
                # Start the server
                success = await mcp_client.connect()
                if success:
                    self.servers[server_name] = mcp_client
                    logger.info(f"Successfully started MCP server: {server_name}")
                else:
                    logger.error(f"Failed to start MCP server: {server_name}")
            
            # Discover capabilities from all servers
            await self.discover_all_capabilities()
            
            return len(self.servers) > 0
            
        except Exception as e:
            logger.error(f"Failed to start MCP servers: {e}")
            return False
    
    async def stop_all_servers(self):
        """Stop all running MCP servers."""
        logger.info("Stopping all MCP servers...")
        
        for server_name, mcp_client in self.servers.items():
            try:
                logger.info(f"Stopping MCP server: {server_name}")
                await mcp_client.disconnect()
            except Exception as e:
                logger.error(f"Error stopping MCP server {server_name}: {e}")
        
        self.servers.clear()
        self.available_tools.clear()
        self.available_resources.clear()
        logger.info("All MCP servers stopped")
    
    async def discover_all_capabilities(self):
        """Discover tools, resources, and prompts from all servers."""
        logger.info("Discovering capabilities from all MCP servers...")
        
        all_tools = []
        all_resources = []
        
        for server_name, mcp_client in self.servers.items():
            try:
                # Discover tools
                tools = await mcp_client.list_tools()
                for tool in tools:
                    # Add server context to tool
                    tool.server_name = server_name
                    all_tools.append(tool)
                
                # TODO: Discover resources and prompts when MCP supports them
                # For now, we'll focus on tools
                
                logger.info(f"Discovered {len(tools)} tools from server: {server_name}")
                
            except Exception as e:
                logger.error(f"Failed to discover capabilities from server {server_name}: {e}")
        
        self.available_tools = all_tools
        self.available_resources = all_resources
        
        logger.info(f"Total capabilities discovered: {len(all_tools)} tools")
    
    def get_available_tools(self) -> List[Any]:
        """Get all available tools from all servers."""
        return self.available_tools
    
    def get_available_resources(self) -> List[Any]:
        """Get all available resources from all servers."""
        return self.available_resources
    
    def get_tools_by_server(self, server_name: str) -> List[Any]:
        """Get tools from a specific server."""
        return [tool for tool in self.available_tools if hasattr(tool, 'server_name') and tool.server_name == server_name]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get tool names and their descriptions from all servers."""
        descriptions = {}
        for tool in self.available_tools:
            server_name = getattr(tool, 'server_name', 'unknown')
            descriptions[f"{tool.name} ({server_name})"] = tool.description
        return descriptions
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool by name across all servers."""
        # Find the tool and its server
        target_tool = None
        target_server = None
        
        for tool in self.available_tools:
            if tool.name == tool_name:
                target_tool = tool
                target_server = getattr(tool, 'server_name', None)
                break
        
        if not target_tool or not target_server:
            logger.error(f"Tool '{tool_name}' not found in any server")
            return None
        
        if target_server not in self.servers:
            logger.error(f"Server '{target_server}' not available for tool '{tool_name}'")
            return None
        
        # Call the tool on the appropriate server
        logger.info(f"Calling tool '{tool_name}' on server '{target_server}'")
        return await self.servers[target_server].call_tool(tool_name, arguments)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_all_servers()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_all_servers()

