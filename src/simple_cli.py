"""Simplified CLI interface for debugging and management only."""

import argparse
import asyncio
import logging
import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from .mcp_server_manager import MCPServerManager
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class SimpleCLI:
    """Simplified CLI for debugging and management only."""
    
    def __init__(self):
        """Initialize the simple CLI interface."""
        self.console = Console()
        self.mcp_manager: Optional[MCPServerManager] = None
        self.llm_client: Optional[LLMClient] = None
        
    def display_help(self):
        """Display help information."""
        help_text = """
Spendcast Benchmark - CLI Management Interface

Available commands:
  --help              Show this help message
  --servers           List available MCP servers from configuration
  --tools             Start MCP servers, fetch available tools and print descriptions
  --web               Start the web interface (default)

Note: Interactive chat is now available through the web interface only.
Run with --web to start the web server.
        """
        
        panel = Panel(help_text.strip(), title="Help", border_style="green")
        self.console.print(panel)
        self.console.print()
    
    def display_servers(self):
        """Display MCP server configuration."""
        try:
            # Load configuration without starting servers
            self.mcp_manager = MCPServerManager()
            server_configs = self.mcp_manager._load_mcp_config()
            
            if not server_configs:
                self.console.print("[yellow]No MCP servers configured[/yellow]")
                return
            
            table = Table(title="Configured MCP Servers", box=box.ROUNDED)
            table.add_column("Server Name", style="cyan")
            table.add_column("Command", style="blue")
            table.add_column("Arguments", style="green")
            table.add_column("Environment", style="magenta")
            
            for server_name, config in server_configs.items():
                args_str = " ".join(config.args) if config.args else "None"
                env_str = ", ".join([f"{k}={v}" for k, v in config.env.items()]) if config.env else "None"
                table.add_row(server_name, config.command, args_str, env_str)
            
            self.console.print(table)
            self.console.print()
            
        except Exception as e:
            self.console.print(f"[red]Error loading server configuration: {e}[/red]")
    
    async def display_tools(self):
        """Start MCP servers, fetch tools and display descriptions."""
        try:
            self.console.print("[blue]Starting MCP servers...[/blue]")
            
            # Initialize MCP server manager
            self.mcp_manager = MCPServerManager()
            success = await self.mcp_manager.start_all_servers()
            
            if not success:
                self.console.print("[red]Failed to start MCP servers[/red]")
                return
            
            # Get available tools
            tools = self.mcp_manager.get_available_tools()
            
            if not tools:
                self.console.print("[yellow]No MCP tools available[/yellow]")
                return
            
            # Display tools
            table = Table(title="Available MCP Tools", box=box.ROUNDED)
            table.add_column("Tool Name", style="cyan")
            table.add_column("Server", style="blue")
            table.add_column("Description", style="green")
            
            for tool in tools:
                server_name = getattr(tool, 'server_name', 'unknown')
                table.add_row(tool.name, server_name, tool.description)
            
            self.console.print(table)
            self.console.print()
            
            # Clean up
            await self.mcp_manager.stop_all_servers()
            
        except Exception as e:
            self.console.print(f"[red]Error fetching tools: {e}[/red]")
            if self.mcp_manager:
                await self.mcp_manager.stop_all_servers()
    
    async def start_web_interface(self):
        """Start the web interface."""
        self.console.print("[blue]Starting web interface...[/blue]")
        self.console.print("Web interface will be available at: http://localhost:8000")
        self.console.print("Press Ctrl+C to stop the web server")
        
        # Import and start web server
        from .web_server import start_web_server
        await start_web_server()
    
    def run(self):
        """Run the CLI with command line arguments."""
        parser = argparse.ArgumentParser(
            description="Spendcast Benchmark - CLI Management Interface",
            add_help=False
        )
        parser.add_argument("--help", action="store_true", help="Show help message")
        parser.add_argument("--servers", action="store_true", help="List configured MCP servers")
        parser.add_argument("--tools", action="store_true", help="Start servers and list available tools")
        parser.add_argument("--web", action="store_true", help="Start web interface (default)")
        
        args = parser.parse_args()
        
        # If no arguments provided, default to web interface
        if not any([args.help, args.servers, args.tools, args.web]):
            args.web = True
        
        try:
            if args.help:
                self.display_help()
            elif args.servers:
                self.display_servers()
            elif args.tools:
                asyncio.run(self.display_tools())
            elif args.web:
                asyncio.run(self.start_web_interface())
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
