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
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class CLIInterface:
    """Command-line interface for the chatbot."""
    
    def __init__(self):
        """Initialize the CLI interface."""
        self.console = Console()
        self.conversation = Conversation()
        self.llm_client: Optional[LLMClient] = None
        self.mcp_client: Optional[MCPClient] = None
        
    def display_welcome(self):
        """Display the welcome message."""
        welcome_text = Text("🤖 Spendcast Benchmark Chatbot", style="bold blue")
        subtitle = Text("Your local LLM assistant with MCP tool integration", style="italic")
        
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
        if not self.mcp_client:
            self.console.print("[yellow]MCP client not connected[/yellow]")
            return
        
        tools = self.mcp_client.get_available_tools()
        if not tools:
            self.console.print("[yellow]No MCP tools available[/yellow]")
            return
        
        table = Table(title="Available MCP Tools", box=box.ROUNDED)
        table.add_column("Tool Name", style="cyan")
        
        for tool in tools:
            table.add_row(tool)
        
        self.console.print(table)
        self.console.print()
    
    def display_models(self):
        """Display available Ollama models and current active model."""
        if not self.llm_client:
            self.console.print("[yellow]LLM client not available[/yellow]")
            return
        
        try:
            # Get available models from the already-loaded client
            available_models = getattr(self.llm_client.ollama, 'available_models', [])
            
            if not available_models:
                self.console.print("[yellow]No models available on Ollama server[/yellow]")
                return
            
            table = Table(title="Available Ollama Models", box=box.ROUNDED)
            table.add_column("Model Name", style="cyan")
            table.add_column("Status", style="magenta")
            
            current_model = self.llm_client.ollama.default_model
            
            for model in available_models:
                status = "🟢 Active" if model == current_model else "⚪ Available"
                table.add_row(model, status)
            
            self.console.print(table)
            self.console.print(f"[blue]Current active model: {current_model}[/blue]")
            self.console.print()
            
        except Exception as e:
            self.console.print(f"[red]Error fetching models: {e}[/red]")
            self.console.print()
    
    def display_user_input(self, user_input: str):
        """Display user input in a formatted way."""
        panel = Panel(
            user_input,
            title="You",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)
        self.console.print()
    
    def display_assistant_response(self, response: str):
        """Display assistant response in a formatted way."""
        panel = Panel(
            response,
            title="Assistant",
            border_style="blue",
            box=box.ROUNDED
        )
        self.console.print(panel)
        self.console.print()
    
    def display_error(self, error_message: str):
        """Display error messages."""
        panel = Panel(
            f"[red]{error_message}[/red]",
            title="Error",
            border_style="red",
            box=box.ROUNDED
        )
        self.console.print(panel)
        self.console.print()
    
    def display_info(self, message: str):
        """Display informational messages."""
        panel = Panel(
            f"[blue]{message}[/blue]",
            title="Info",
            border_style="blue",
            box=box.ROUNDED
        )
        self.console.print(panel)
        self.console.print()
    
    def get_user_input(self) -> str:
        """Get user input with a prompt."""
        try:
            return Prompt.ask("[green]You[/green]")
        except (EOFError, KeyboardInterrupt):
            # Handle EOF gracefully
            self.console.print("\n[yellow]Input interrupted[/yellow]")
            return "exit"
    
    def confirm_exit(self) -> bool:
        """Ask user to confirm exit."""
        try:
            return Confirm.ask("Are you sure you want to exit?")
        except (EOFError, KeyboardInterrupt):
            # Handle EOF gracefully
            self.console.print("\n[yellow]Assuming yes due to input interruption[/yellow]")
            return True
    
    def is_exit_command(self, user_input: str) -> bool:
        """Check if user input is an exit command."""
        exit_commands = ['exit', 'quit', 'bye', 'goodbye']
        return user_input.lower().strip() in exit_commands
    
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
                    
                    # Generate LLM response
                    if self.llm_client:
                        # Create prompt with conversation context
                        system_prompt = self.llm_client.get_system_prompt()
                        conversation_history = self.conversation.get_formatted_history(max_messages=10)
                        
                        full_prompt = f"{system_prompt}\n\nConversation History:\n{conversation_history}\n\nUser: {user_input}\nAssistant:"
                        
                        response = await self.llm_client.generate_response(full_prompt)
                        if response:
                            self.conversation.add_assistant_message(response)
                            self.display_assistant_response(response)
                        else:
                            error_msg = "Sorry, I couldn't generate a response. Please try again."
                            self.conversation.add_assistant_message(error_msg)
                            self.display_error(error_msg)
                    else:
                        error_msg = "LLM client not available. Please check your configuration."
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
            # Initialize MCP client
            self.mcp_client = MCPClient()
            await self.mcp_client.connect()
            
            # Initialize LLM client
            self.llm_client = LLMClient()
            await self.llm_client.setup()
            
            # Update LLM client with available tools
            if self.mcp_client:
                tools = await self.mcp_client.list_tools()
                tool_names = [tool.name for tool in tools]
                self.llm_client.set_available_tools(tool_names)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup CLI interface: {e}")
            self.display_error(f"Setup failed: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.llm_client:
            await self.llm_client.close()
        if self.mcp_client:
            await self.mcp_client.disconnect()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
