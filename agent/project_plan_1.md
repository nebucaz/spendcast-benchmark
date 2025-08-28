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
Status: ⏳ Pending

### Acceptance Criteria
- The LLM should be given it's first tool: [spendcast-mcp](https://github.com/spendcastai/spendcast-mcp)

### Technical Implementation
- integrate the SPENDCAST-MCP tool and make the tool known to the LLM
- Configuration: 
  - GRAPHDB_URL=http://localhost:7200/repositories/demo
  - GRAPHDB_USER=bernhaeckt
  - GRAPHDB_PASSWORD=bernhaeckt

### Testing
- Create `tests/test_*.py` with unittests to test the integration
