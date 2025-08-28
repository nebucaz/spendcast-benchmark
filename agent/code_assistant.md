# CODE ASSISTANT

This file provides guidance to CODE-ASSISTANT when working with code in this repository.

> Important: Throughout all the documents with instructions in the current folder, 'Cursor' is referenced as "CODE-ASSISTANT". So, whenever "CODE-ASSISTANT". CODE-ASSISTANT is therefore always used when cursor is meant: whenever an instruction or a rule is described for CODE-ASSISTANT, this applies accordingly to cursor

## Quick Start for New Sessions

Before starting any work, read these files in order:
- pair_programming.md - Our workflow process for story-driven development
- project_plan_{some_extension}.md - Current progress and next story to work on
- technical_considerations.md - Lessons learned and implementation decisions

## Overview
This project imlpements a chatbot with a local large language model (LLM). The chatbot is implemented in python and connects other sources using the MCP-Protocl. 

## Development Commands
This is a python project that uses `uv`as the package manager.

### Package Management
- Uses uv as the package manager (not pip)
- Lock file: uv.lock

### Install Dependencies 
Install dependencies using uv:
```bash
uv sync
```

### Install Additional Dependencies
```bash
uv add <dependency_name>
```

## Architecture Overview
Technology Stack
 - Python 
    
Implementation Status: ⏳ Pending 

## Project Structure Overview
Key locations:
    src/ - Python mcp server-files
    test/ - Python tests


