# spendcast-benchmark Phase 1 Project Plan

## Overview
Phase 1.0 creates a functional MVP. The focus is to create a chatbot that takes user input, queries a local LLM and returns the response to to the user.

## Story Status Legend

    ⏳ Pending - Not started
    🔄 In Progress - Currently being worked on
    ✅ Completed - Implemented and verified
    🧪 Testing - Implementation complete, awaiting verification

## Story 1.1: Implement the chatbot user interface
Status: ✅ Completed

### Acceptance Criteria:
 - The user interface runs in a command line interface ✅
 - The script interacts with a local LLM ✅
 - The response is printed to the console and a new promt is requested. ✅
 - The user must have the possibility to exit the conversation ✅

### Technical Implementation:
 - Create `main.py` as the CLI application controlling the whole process ✅
 - Create functions to parse the different entities within the templates ✅
 - Collect related  functions in modules ✅
 - Mind to choose a framework that allows connecting tools via the MCP protocol ✅

### Testing:
 - Unittest: Create necessary tests in `tests/test_*.py` with unittests to test the funtionaloity ✅

## Story 1.2: Connect the sample data using
Status: ✅ Completed

### Acceptance Criteria
- The LLM should be given it's first tool: [spendcast-mcp](https://github.com/spendcastai/spendcast-mcp) ✅

### Technical Implementation
- integrate the SPENDCAST-MCP tool and make the tool known to the LLM ✅
- Configuration: 
  - GRAPHDB_URL=http://localhost:7200/repositories/demo ✅
  - GRAPHDB_USER=bernhaeckt ✅
  - GRAPHDB_PASSWORD=bernhaeckt ✅
- MCP client implementation with config.json-based server configuration ✅
- Tool discovery and integration with LLM ✅
- Tool calling functionality with proper error handling ✅
- Claude Desktop-style MCP configuration format ✅

### Testing
- Create `tests/test_*.py` with unittests to test the integration ✅

## Story 1.3: Parametrized MCP Servers
Status: ✅ Completed

### Acceptance Criteria
- Multiple MCP Servers can be configured in Claude Desktop-style ✅
- The chatbot manages the configured MCP-servers (start, stop) ✅
- The chatbot announces the available MCP-servers to the LLM ✅

### Technical Implementation
- MCP Server configuration goes into the `config.json` file ✅
- The chatbot analyzes the file and instantiates each MCP-server as a process using the command given in the configuration ✅
- When the chatbot exits, the MCP-servers must be terminated ✅
- Enhanced MCP Server Manager for handling multiple servers ✅
- Intelligent Agent implementing two-phase strategy for coordinating between user, LLM, and MCP servers ✅

### Testing
- Test the MCP-Lifecycle that the chatbot must manage (start, stop, announce to the LLM) ✅
- Comprehensive test suite for MCP Server Manager, Intelligent Agent, and end-to-end functionality ✅

## Story 1.4: Agentic communication with the LLM
Status: ❌ Failed

### Acceptance Criteria
- The Chatbot should act as an agent between the user, the LLM and the available MCP-Servers ✅
- The agent manages the communication between LLM, MCP-Servers and the user ✅
- This concept is explained in the file `agent/mcp_agent_explained.md` ✅

### Technical Implementation
- Implemented Intelligent Agent class coordinating between user, LLM, and MCP servers ✅
- Two-phase strategy: Phase 1 determines needed resources/tools, Phase 2 executes with gathered context ✅
- Enhanced CLI interface integrating with Intelligent Agent and MCP Server Manager ✅
- Tool discovery, capability announcement, and intelligent tool selection ✅

### Testing
- Test the announcing of tools and capabilities of the MCP servers to the LLM ✅
- Comprehensive test suite for Intelligent Agent functionality and end-to-end workflows ✅

## Story 1.5: Change user interface from CLI to Web-UI
Status: ✅ Completed

### Acceptance Criteria
- Interaction with the agent should be over Web ✅
- Promting should not be possible in CLI any more ✅
- A Web server provides a chat session ✅
- THe user interface is simple yet interactive and performant ✅

### Technical Implementation
- Choose the appropriate technology for the web interface ✅ (FastAPI + WebSocket)
- Strip down the options of the CLI to the following options: ✅
 --help show instructions
 --servers list available MCP servers    (from configuration)
 --tools start each MCP server, fetch available tools and print tool-description

### Testing
- Test the CLI-Options ✅
- Web Interface is tested by human ✅

### Note
- Web interface cann not be tested because of MCP-servers blocking executionen askinols,
- MCP server blocking issue will be resolved in Story 1.6

## Story 1.6 MCP Server Lifecycle Management
Status: ✅ Completed

### Acceptance criteria
- The main script must read the MCP configuration file and launch each MCP server listed. ✅
- MCP servers must be started as subprocesses so the main script remains non-blocking. ✅
- Each subprocess must expose stdin, stdout, and stderr streams for communication and logging. ✅
- The agent must connect to the MCP servers using their stdio streams via the MCP Client. ✅
- The main script must keep references to the subprocess handles in order to: ✅
  - Monitor for crashes/failures. ✅
  - Restart or shut down servers gracefully when needed. ✅
  - Starting the MCP servers must not interfere with starting the web server or handling user prompts. ✅
- Logs from MCP servers (stderr) must be captured and made available for debugging. ✅

### Technical Implementation
- Use Python's subprocess.Popen to start each MCP server defined in the config. ✅
Example:
```
proc = subprocess.Popen(
    [cmd, *args],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
```
- Store process handles in a registry (e.g., dict keyed by server name). ✅
- Wrap stdout/stderr in non-blocking readers (e.g., asyncio.create_task or threading.Thread with a queue). ✅
- Initialize MCP Client with the stdin/stdout pipes of each subprocess. ✅
- After all MCP servers are started, launch the web server (e.g., FastAPI, Flask). ✅
- Ensure the main script handles signals (SIGINT/SIGTERM) to shut down MCP servers cleanly. ✅

### Testing
1. Unit tests:
  - Simulate launching a fake MCP server binary with echo or a mock script.
  - Verify subprocess is started with correct args from the config.
  - Test proper cleanup when the subprocess is terminated.
2. Integration tests:
  - Start one or more real MCP servers as subprocesses.
  - Verify that the agent can connect and exchange messages with them via MCP Client.
  - Check that stderr logs are captured.
3. Failure scenarios:
  - Kill a subprocess manually → ensure main script detects and logs the crash.
  - Start with invalid config → ensure startup fails gracefully.
4. End-to-end test:
  - Run the full main script:
    - Config is read.
    - Two MCP servers start successfully.
    - Web server starts and accepts a prompt.
    - Agent routes a request through one of the MCP servers and returns the result.

## Story 1.7 LLM-Instruction Parsing and Tool Execution
Status: ✅ Completed

### Acceptance criteria
- The agent must parse the LLM output for tool calls (TOOL_CALL) and their parameters.
- The agent must validate extracted parameters (e.g., valid JSON, required fields).
- The agent should optionally present proposed tool calls to the user for approval.
- Only after parsing (and optional approval) should the agent invoke the MCP client.
- The results from MCP servers must be returned to the LLM as context for further reasoning.
- Parsing errors must be reported clearly to the LLM for regeneration or correction.

### Technical Implementation
- Implement a parser in the agent to detect TOOL_CALL blocks in LLM output.
- Use json.loads or a safe JSON parser for parameters, with error handling.
- Wrap MCP client calls in a function that optionally asks the user for confirmation.
- Feed MCP results back to LLM for reasoning or response generation.
- Maintain logs of tool calls, results, and user approvals for auditing.

### Testing
1. Unit tests
  - Validate parser extracts tool name + parameters correctly from sample LLM outputs.
  - Check parsing error handling for malformed JSON or missing fields.

2. Integration tests
  - Run the agent → LLM → MCP server → verify that tool calls are executed correctly.
  - Include tests with simulated user approvals/rejections.

3. End-to-end tests
  - Submit a query to the agent.
  - Verify: LLM suggests a tool call, agent parses it, optionally asks for user approval, executes MCP call, and returns results to LLM.

### Implementation Notes
- Enhanced the `IntelligentAgent` with robust tool call parsing using regex patterns
- Added `_parse_tool_parameters()` method with proper JSON boundary detection
- Implemented `_generate_final_response()` to feed tool results back to LLM
- Added comprehensive error handling and logging for tool execution
- Improved prompts to guide LLM in proper tool call formatting
- Tool calls are now properly parsed and executed without JSON parsing errors


## Story 1.8 Abstraction Layer for Multi-Machine LLM Setup
Status: ⏳ Pending

### Acceptance criteria
- The chatbot agent must communicate with LLMs via a common abstraction layer (LLMClient) instead of direct API calls.
- The abstraction must support multiple LLM backends (e.g., Ollama, vLLM, Hugging Face Transformers).
- The backend configuration must be read from a config file, allowing model/service selection without code changes.
- The system must support running the LLM service on a different machine than the chatbot agent.
- The LLM backend must be reachable via network endpoints (e.g., REST API, OpenAI-compatible API).
- Security/compliance requirement: all communication remains within the company’s local network (no external services).
- The chatbot agent should continue to orchestrate interactions with MCP servers/tools independently of the chosen LLM backend.

### Technical Implementation
- Introduce an interface LLMClient with a common method (e.g., generate(prompt: str) -> str).
- Implement backend adapters:
  - OllamaClient → communicates with Ollama’s HTTP API (http://<host>:11434).
  - VLLMClient → communicates with vLLM’s OpenAI-compatible API (http://<host>:8000/v1/completions).
  . TransformersClient → runs Hugging Face models locally (Python-based, slower).

- Extend the configuration file to specify:
  - Which backend to use (ollama, vllm, transformers).
  - Host and port for networked LLM services.
  - Model identifier.
- Enable the chatbot agent to instantiate the right LLMClient at startup based on the config.
- Ensure network setup allows agent (Machine A) to call LLM server (Machine B) on the configured host/port.

### Testing
1. Unit tests:
  - Test each LLMClient implementation independently (mock API responses).
  - Verify error handling (unreachable host, invalid config).
2. Integration tests (single-machine):
  - Run chatbot agent with Ollama locally.
  - Run chatbot agent with vLLM locally (OpenAI-compatible mode).
3. Integration tests (multi-machine):
  - Deploy Ollama on Machine B, agent on Machine A → confirm agent connects via network.
  - Deploy vLLM on Machine B, agent on Machine A → confirm agent connects via network.
4. End-to-end test:
  - Start chatbot agent with MCP servers configured.
  - Submit a user query that triggers tool usage.
  - Verify the LLM decision + tool execution + final response flow works across the abstraction layer.

