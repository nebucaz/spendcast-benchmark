"""Command-line interface for the chatbot application."""

import logging
import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from .conversation import Conversation
from .llm_client import LLMClient
from .mcp_server_manager import MCPServerManager
from .intelligent_agent import IntelligentAgent

logger = logging.getLogger(__name__)


class CLIInterface:
    """Command-line interface for the chatbot."""
    
    def __init__(self):
        """Initialize the CLI interface."""
        self.console = Console()
        self.conversation = Conversation()
        self.llm_client: Optional[LLMClient] = None
        self.mcp_manager: Optional[MCPServerManager] = None
        self.intelligent_agent: Optional[IntelligentAgent] = None
        
    def display_welcome(self):
        """Display the welcome message."""
        welcome_text = Text("🤖 Spendcast Benchmark Chatbot", style="bold blue")
        subtitle = Text("Your intelligent AI assistant with MCP tool integration", style="italic")
        
        panel = Panel(
            f"{welcome_text}\n{subtitle}",
            border_style="blue",
            box=box.ROUNDED
        )
        self.console.print(panel)
        self.console.print()
    
    def display_help(self):
        """Display help information."""
        help_text = """
Available commands:
- Type your message to chat with the AI
- Type 'exit', 'quit', or 'bye' to end the conversation
- Type 'help' to show this message
- Type 'clear' to clear conversation history
- Type 'tools' to show available MCP tools
- Type 'servers' to show MCP server status
- Type 'models' to show available Ollama models
- Type 'status' to show conversation status
        """
        
        panel = Panel(help_text.strip(), title="Help", border_style="green")
        self.console.print(panel)
        self.console.print()
    
    def display_status(self):
        """Display conversation status."""
        summary = self.conversation.get_summary()
        
        table = Table(title="Conversation Status", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Messages", str(summary["message_count"]))
        table.add_row("User Messages", str(summary["user_messages"]))
        table.add_row("Assistant Messages", str(summary["assistant_messages"]))
        table.add_row("Duration", f"{summary['duration_seconds']:.1f}s")
        table.add_row("Status", "Active" if summary["is_active"] else "Ended")
        
        self.console.print(table)
        self.console.print()
    
    def display_tools(self):
        """Display available MCP tools."""
        if not self.mcp_manager:
            self.console.print("[yellow]MCP manager not available[/yellow]")
            return
        
        tools = self.mcp_manager.get_available_tools()
        if not tools:
            self.console.print("[yellow]No MCP tools available[/yellow]")
            return
        
        table = Table(title="Available MCP Tools", box=box.ROUNDED)
        table.add_column("Tool Name", style="cyan")
        table.add_column("Server", style="blue")
        table.add_column("Description", style="green")
        
        for tool in tools:
            server_name = getattr(tool, 'server_name', 'unknown')
            table.add_row(tool.name, server_name, tool.description)
        
        self.console.print(table)
        self.console.print()
    
    def display_servers(self):
        """Display MCP server status."""
        if not self.mcp_manager:
            self.console.print("[yellow]MCP manager not available[/yellow]")
            return
        
        servers = self.mcp_manager.servers
        if not servers:
            self.console.print("[yellow]No MCP servers running[/yellow]")
            return
        
        table = Table(title="MCP Server Status", box=box.ROUNDED)
        table.add_column("Server Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Tools", style="blue")
        
        for server_name, mcp_client in servers.items():
            status = "Running" if mcp_client.session else "Stopped"
            tools_count = len(self.mcp_manager.get_tools_by_server(server_name))
            table.add_row(server_name, status, str(tools_count))
        
        self.console.print(table)
        self.console.print()
    
    def display_models(self):
        """Display available Ollama models and current active model."""
        if not self.llm_client:
            self.console.print("[yellow]LLM client not available[/yellow]")
            return
        
        try:
            # Get available models
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, can't call sync methods
                self.console.print("[yellow]Cannot check models in async context[/yellow]")
                return
            
            # This would need to be async in a real implementation
            self.console.print("[green]✓ LLM client available[/green]")
            self.console.print(f"Current model: {self.llm_client.ollama.default_model}")
            
        except Exception as e:
            self.console.print(f"[red]Error checking models: {e}[/red]")
        
        self.console.print()
    
    def display_user_input(self, user_input: str):
        """Display user input."""
        self.console.print(f"[bold blue]You:[/bold blue] {user_input}")
    
    def display_assistant_response(self, response: str):
        """Display assistant response."""
        self.console.print(f"[bold green]Assistant:[/bold green] {response}")
        self.console.print()
    
    def display_error(self, error_msg: str):
        """Display error message."""
        self.console.print(f"[bold red]Error:[/bold red] {error_msg}")
        self.console.print()
    
    def display_info(self, info_msg: str):
        """Display info message."""
        self.console.print(f"[bold yellow]Info:[/bold yellow] {info_msg}")
        self.console.print()
    
    def get_user_input(self) -> str:
        """Get user input from the console."""
        return Prompt.ask("[bold blue]You[/bold blue]")
    
    def confirm_exit(self) -> bool:
        """Confirm if the user wants to exit."""
        return Confirm.ask("Are you sure you want to exit?")
    
    def is_exit_command(self, user_input: str) -> bool:
        """Check if user input is an exit command."""
        return user_input.lower().strip() in ['exit', 'quit', 'bye']
    
    def is_help_command(self, user_input: str) -> bool:
        """Check if user input is a help command."""
        return user_input.lower().strip() == 'help'
    
    def is_clear_command(self, user_input: str) -> bool:
        """Check if user input is a clear command."""
        return user_input.lower().strip() == 'clear'
    
    def is_status_command(self, user_input: str) -> bool:
        """Check if user input is a status command."""
        return user_input.lower().strip() == 'status'
    
    def is_tools_command(self, user_input: str) -> bool:
        """Check if user input is a tools command."""
        return user_input.lower().strip() == 'tools'
    
    def is_servers_command(self, user_input: str) -> bool:
        """Check if user input is a servers command."""
        return user_input.lower().strip() == 'servers'
    
    def is_models_command(self, user_input: str) -> bool:
        """Check if user input is a models command."""
        return user_input.lower().strip() == 'models'
    
    def handle_special_commands(self, user_input: str) -> bool:
        """Handle special commands and return True if handled."""
        if self.is_help_command(user_input):
            self.display_help()
            return True
        elif self.is_clear_command(user_input):
            self.conversation.clear_history()
            self.display_info("Conversation history cleared")
            return True
        elif self.is_status_command(user_input):
            self.display_status()
            return True
        elif self.is_tools_command(user_input):
            self.display_tools()
            return True
        elif self.is_servers_command(user_input):
            self.display_servers()
            return True
        elif self.is_models_command(user_input):
            self.display_models()
            return True
        return False
    
    def display_goodbye(self):
        """Display goodbye message."""
        summary = self.conversation.get_summary()
        goodbye_text = f"""
Thank you for using Spendcast Benchmark Chatbot!

Conversation Summary:
- Total messages: {summary['message_count']}
- Duration: {summary['duration_seconds']:.1f} seconds
- Messages exchanged: {summary['user_messages']} user, {summary['assistant_messages']} assistant

Goodbye! 👋
        """
        
        panel = Panel(
            goodbye_text.strip(),
            title="Goodbye",
            border_style="yellow",
            box=box.ROUNDED
        )
        self.console.print(panel)
    
    async def run_conversation_loop(self):
        """Run the main conversation loop."""
        try:
            while self.conversation.is_active:
                try:
                    user_input = self.get_user_input()
                    
                    # Check for exit command
                    if self.is_exit_command(user_input):
                        if self.confirm_exit():
                            self.conversation.end_conversation()
                            break
                        else:
                            continue
                    
                    # Handle special commands
                    if self.handle_special_commands(user_input):
                        continue
                    
                    # Add user message to conversation
                    self.conversation.add_user_message(user_input)
                    self.display_user_input(user_input)
                    
                    # Process request using intelligent agent
                    if self.intelligent_agent:
                        response = await self.intelligent_agent.process_user_request(user_input)
                        self.conversation.add_assistant_message(response)
                        self.display_assistant_response(response)
                    else:
                        error_msg = "Intelligent agent not available. Please check your configuration."
                        self.display_error(error_msg)
                        
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Interrupted by user[/yellow]")
                    if self.confirm_exit():
                        self.conversation.end_conversation()
                        break
                except Exception as e:
                    logger.error(f"Error in conversation loop: {e}")
                    self.display_error(f"An error occurred: {str(e)}")
                    
        finally:
            self.display_goodbye()
    
    async def setup(self):
        """Set up the CLI interface components."""
        try:
            # Initialize MCP server manager
            self.mcp_manager = MCPServerManager()
            await self.mcp_manager.start_all_servers()
            
            # Initialize LLM client
            self.llm_client = LLMClient()
            await self.llm_client.setup()
            
            # Initialize intelligent agent
            self.intelligent_agent = IntelligentAgent(self.llm_client, self.mcp_manager)
            
            logger.info("CLI interface setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup CLI interface: {e}")
            self.display_error(f"Setup failed: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.llm_client:
            await self.llm_client.close()
        if self.mcp_manager:
            await self.mcp_manager.stop_all_servers()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
