#!/usr/bin/env python3
"""Main entry point for the Spendcast Benchmark chatbot."""

import logging
import sys
from pathlib import Path

from .simple_cli import SimpleCLI
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

def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Spendcast Benchmark chatbot...")
        
        # Create and run simple CLI
        cli = SimpleCLI()
        cli.run()
            
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

if __name__ == "__main__":
    main()
