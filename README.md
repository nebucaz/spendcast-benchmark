# spendcast-benchmark

A chatbot implementation using a local large language model (LLM) with Python and MCP protocol integration.

## Prerequisites

### 1. Install Ollama

#### macOS
```bash
brew install ollama
```

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Windows
Download and install from [https://ollama.ai/download](https://ollama.ai/download)

### 2. Start the Ollama

After installing Ollama, start the server

```bash
ollama serve
```

### 3. Pull the Mistral Model

After installing Ollama, pull the Mistral 7B model:

```bash
ollama pull mistral:7b
```

This will download the model (approximately 4.1GB) and make it available for local inference.

## Installation

This project uses `uv` as the package manager. Install dependencies with:

```bash
uv sync
```

## Usage

Run the chatbot using:

```bash
uv run python -m src.main
```

The chatbot will start in command-line interface mode, allowing you to:
- Interact with the local LLM
- Have conversations with the AI
- Exit the conversation when desired

## Project Structure

- `src/` - Python MCP server files and main application
- `tests/` - Python test files
- `agent/` - Project documentation and planning files

## Development

To add new dependencies:

```bash
uv add <dependency_name>
```

## Testing

Run tests using:

```bash
uv run python -m pytest tests/
```

## Current Status

- ✅ Story 1.1: Basic chatbot implementation with CLI interface
- ⏳ Story 1.2: MCP tool integration (pending)

## Architecture

The project implements a chatbot that:
- Runs locally using Ollama for LLM inference
- Provides a command-line interface
- Is designed to integrate with MCP protocol tools
- Uses Python with modern package management via `uv`
