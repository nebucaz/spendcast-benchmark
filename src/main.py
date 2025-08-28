#!/usr/bin/env python3
"""Main entry point for the Spendcast Benchmark chatbot."""

import asyncio
import logging
import sys
from pathlib import Path

from .cli_interface import CLIInterface
from .config import get_settings

# Configure logging
def setup_logging():
    """Set up logging configuration."""
    settings = get_settings()
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('chatbot.log')
        ]
    )

async def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Spendcast Benchmark chatbot...")
        
        # Create and run CLI interface
        async with CLIInterface() as cli:
            # Display welcome message
            cli.display_welcome()
            
            # Display help
            cli.display_help()
            
            # Run the conversation loop
            await cli.run_conversation_loop()
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nGoodbye! 👋")
    except EOFError:
        logger.info("Application received EOF - ending gracefully")
        print("\nInput ended - Goodbye! 👋")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)

def run():
    """Entry point for the application."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
    except Exception as e:
        print(f"\n❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
