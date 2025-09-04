"""MCP Subprocess Manager for handling MCP servers as separate processes."""

import asyncio
import logging
import subprocess
import os
import signal
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
import queue

from .mcp_client import MCPServerConfig
from .mcp_subprocess_client import MCPSubprocessClient

logger = logging.getLogger(__name__)


class MCPSubprocessManager:
    """Manages MCP servers as separate subprocesses."""
    
    def __init__(self):
        """Initialize the MCP subprocess manager."""
        self.processes: Dict[str, subprocess.Popen] = {}
        self.mcp_clients: Dict[str, MCPSubprocessClient] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        self.log_queues: Dict[str, queue.Queue] = {}
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        self.shutdown_event = threading.Event()
        
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
    
    def _log_reader(self, server_name: str, stream, log_queue: queue.Queue):
        """Read logs from a subprocess stream."""
        try:
            for line in iter(stream.readline, ''):
                if line:
                    log_queue.put(f"[{server_name}] {line.strip()}")
                    logger.debug(f"MCP Server {server_name}: {line.strip()}")
        except Exception as e:
            logger.error(f"Error reading logs from {server_name}: {e}")
        finally:
            stream.close()
    
    def _monitor_process(self, server_name: str, process: subprocess.Popen):
        """Monitor a subprocess for crashes and health."""
        while not self.shutdown_event.is_set():
            if process.poll() is not None:
                # Process has terminated
                logger.error(f"MCP server {server_name} has crashed (exit code: {process.returncode})")
                # Remove from active processes
                if server_name in self.processes:
                    del self.processes[server_name]
                break
            
            time.sleep(1)  # Check every second
    
    async def start_server(self, server_name: str, config: MCPServerConfig) -> bool:
        """Start a single MCP server as a subprocess using the MCPServerProcess approach."""
        try:
            logger.info(f"Starting MCP server: {server_name}")
            
            # Start the MCP server as a subprocess using the approach from Story 1.6
            cmd = [config.command] + (config.args or [])
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=config.cwd,
                env=config.env
            )
            
            # Store the process
            self.processes[server_name] = process
            
            # Wait a moment for the process to start
            await asyncio.sleep(1)
            
            # Check if the process is still running
            if process.poll() is not None:
                logger.error(f"MCP server process terminated immediately: {server_name} (exit code: {process.returncode})")
                if server_name in self.processes:
                    del self.processes[server_name]
                return False
            
            # Create MCP subprocess client and connect using the subprocess streams
            mcp_client = MCPSubprocessClient()
            success = await mcp_client.connect_to_subprocess(process, config)
            
            if success:
                self.mcp_clients[server_name] = mcp_client
                logger.info(f"Successfully started MCP server: {server_name}")
                return True
            else:
                logger.error(f"Failed to connect to MCP subprocess: {server_name}")
                # Clean up the process if connection failed
                process.terminate()
                if server_name in self.processes:
                    del self.processes[server_name]
                return False
                
        except Exception as e:
            logger.error(f"Failed to start MCP server {server_name}: {e}")
            return False
    
    
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
                success = await self.start_server(server_name, config)
                if success:
                    success_count += 1
                else:
                    logger.error(f"Failed to start MCP server: {server_name}")
            
            logger.info(f"Started {success_count}/{len(self.server_configs)} MCP servers")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to start MCP servers: {e}")
            return False
    
    async def stop_server(self, server_name: str):
        """Stop a specific MCP server."""
        try:
            logger.info(f"Stopping MCP server: {server_name}")
            
            # Disconnect MCP client if exists
            if server_name in self.mcp_clients:
                await self.mcp_clients[server_name].disconnect()
                del self.mcp_clients[server_name]
            
            # Clean up process reference
            if server_name in self.processes:
                del self.processes[server_name]
            
            logger.info(f"Stopped MCP server: {server_name}")
            
        except Exception as e:
            logger.error(f"Error stopping MCP server {server_name}: {e}")
    
    async def stop_all_servers(self):
        """Stop all running MCP servers."""
        logger.info("Stopping all MCP servers...")
        
        # Stop all servers
        for server_name in list(self.mcp_clients.keys()):
            await self.stop_server(server_name)
        
        logger.info("All MCP servers stopped")
    
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all servers."""
        status = {}
        for server_name in self.server_configs.keys():
            mcp_client = self.mcp_clients.get(server_name)
            process = self.processes.get(server_name)
            
            status[server_name] = {
                "running": mcp_client is not None and mcp_client.session is not None,
                "mcp_connected": mcp_client is not None and mcp_client.session is not None,
                "pid": process.pid if process else None,
                "exit_code": process.returncode if process else None
            }
        return status
    
    async def get_available_tools(self) -> List[Any]:
        """Get all available tools from all servers."""
        all_tools = []
        for server_name, mcp_client in self.mcp_clients.items():
            try:
                tools = await mcp_client.list_tools()
                for tool in tools:
                    # Add server context to tool
                    tool.server_name = server_name
                    all_tools.append(tool)
            except Exception as e:
                logger.error(f"Failed to get tools from {server_name}: {e}")
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool by name across all servers."""
        for server_name, mcp_client in self.mcp_clients.items():
            try:
                result = await mcp_client.call_tool(tool_name, arguments)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Failed to call tool {tool_name} on {server_name}: {e}")
        return None
    
    def get_available_resources(self) -> List[Any]:
        """Get available resources (placeholder for compatibility)."""
        # For now, return empty list as we don't have resources implemented
        return []
    
    def get_available_tools_sync(self) -> List[Any]:
        """Get available tools synchronously (for compatibility)."""
        # This is a placeholder - in a real implementation we'd need to handle async properly
        return []
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_all_servers()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_all_servers()
