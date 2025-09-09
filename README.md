# spendcast-benchmark

A sophisticated chatbot implementation using a local large language model (LLM) with Python and MCP protocol integration. Features an intelligent agent that coordinates between users, LLMs, and MCP servers using an innovative on-demand architecture.

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

### Web Interface (Recommended)

Run the chatbot with web interface:

```bash
uv run python -m src.main --web
```

The chatbot will start a web server at `http://localhost:8000` with:
- Interactive chat interface
- Real-time debug logging
- MCP server status monitoring
- Tool discovery and management

### Command Line Interface

Run the chatbot in CLI mode:

```bash
uv run python -m src.main
```

Available CLI options:
- `--help` - Show instructions
- `--servers` - List available MCP servers
- `--tools` - Start MCP servers and show available tools
- `--web` - Start web interface

## Project Structure

- `src/` - Main application code
  - `intelligent_agent.py` - Core agent logic coordinating user, LLM, and MCP interactions
  - `mcp_on_demand_client.py` - On-demand MCP client implementation
  - `mcp_on_demand_manager.py` - Manager for on-demand MCP clients
  - `web_server.py` - FastAPI web server with WebSocket support
  - `llm_client.py` - LLM abstraction layer
  - `mcp_client.py` - MCP client and configuration management
- `tests/` - Comprehensive test suite
- `agent/` - Project documentation and planning files
- `config.json` - MCP server configuration

## Configuration

### MCP Server Configuration

The system uses `config.json` to configure MCP servers in Claude Desktop format:

```json
{
  "mcpServers": {
    "spendcast-graphdb": {
      "command": "/opt/homebrew/bin/uv",
      "args": ["--directory", "/Users/neo/Data/workspace/spendcast-mcp", "run", "src/spendcast_mcp/server.py"],
      "env": {
        "GRAPHDB_URL": "http://localhost:7200/repositories/demo",
        "GRAPHDB_USER": "bernhaeckt",
        "GRAPHDB_PASSWORD": "bernhaeckt"
      },
      "cwd": "/Users/neo/Data/workspace/spendcast-mcp"
    }
  }
}
```

### Environment Variables

Create a `.env` file for local configuration:

```bash
# LLM Configuration
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=mistral:7b

# MCP Configuration
MCP_CONFIG_FILE=config.json
```

## Development

To add new dependencies:

```bash
uv add <dependency_name>
```

## Testing

### Run All Tests
```bash
uv run python -m pytest tests/
```

### On-Demand MCP Tests
```bash
# Test on-demand MCP functionality
uv run python test_on_demand_mcp.py

# Test web server integration
uv run python test_on_demand_web.py

# Test intelligent agent with on-demand MCP
uv run python test_intelligent_agent_on_demand.py
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **On-Demand Tests**: MCP server lifecycle and efficiency testing
- **Web Interface Tests**: API and WebSocket functionality

## Key Features

### 🚀 On-Demand MCP Architecture
- **Resource Efficient**: MCP servers only start when tools are needed
- **Non-Blocking**: System remains responsive at all times
- **Automatic Cleanup**: No manual process management required
- **Timeout Protection**: Prevents hanging requests
- **Concurrent Support**: Multiple tool calls can run simultaneously

### 🧠 Intelligent Agent
- **Two-Phase Strategy**: Determines needed tools, then executes with context
- **Tool Call Parsing**: Robust parsing of LLM tool call instructions
- **Error Handling**: Comprehensive error recovery and user feedback
- **Debug Logging**: Real-time visibility into agent operations

### 🌐 Modern Web Interface
- **FastAPI Backend**: High-performance async web server
- **WebSocket Support**: Real-time communication and debug logs
- **Responsive UI**: Clean, interactive chat interface
- **Status Monitoring**: Live MCP server and tool status

## Current Status

- ✅ Story 1.1: Basic chatbot implementation with CLI interface
- ✅ Story 1.2: MCP tool integration with spendcast-mcp
- ✅ Story 1.3: Parametrized MCP servers with configuration management
- ✅ Story 1.4: Agentic communication with LLM
- ✅ Story 1.5: Web interface with FastAPI and WebSockets
- ✅ Story 1.6: MCP server lifecycle management
- ✅ Story 1.7: LLM instruction parsing and tool execution
- ✅ Story 1.8: On-demand MCP server management
- ⏳ Story 1.9: Multi-machine LLM setup (pending)

## Architecture

The project implements a sophisticated chatbot system that:
- **Intelligent Agent**: Coordinates between users, LLMs, and MCP servers
- **On-Demand MCP**: Efficient resource utilization with no persistent processes
- **Web Interface**: Modern, responsive UI with real-time debugging
- **Local LLM**: Uses Ollama for local inference
- **MCP Integration**: Seamless tool discovery and execution
- **Python Ecosystem**: Modern package management via `uv`
