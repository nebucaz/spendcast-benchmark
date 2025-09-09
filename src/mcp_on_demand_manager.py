"""
On-demand MCP manager that starts servers only when tools are needed.
This approach is more efficient and avoids the blocking issues of persistent servers.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .mcp_client import MCPServerConfig
from .mcp_on_demand_client import MCPOnDemandClient

logger = logging.getLogger(__name__)


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
