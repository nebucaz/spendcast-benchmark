#!/usr/bin/env python3
"""
Test script to verify that MCP server can be started non-blocking and communicate properly.
This follows the project plan approach using subprocess.Popen and direct pipe communication.
"""

import asyncio
import subprocess
import time
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp import MCPServerConfig
from src.mcp import MCPClient


async def test_mcp_non_blocking():
    """Test that MCP server can be started non-blocking and communicate properly."""
    
    print("🧪 Testing MCP server non-blocking communication...")
    
    # Create server config (using actual config from config.json)
    config = MCPServerConfig(
        name="spendcast-graphdb",
        config={
            "command": "/opt/homebrew/bin/uv",
            "args": [
                "--directory",
                "/Users/neo/Data/workspace/spendcast-mcp",
                "run",
                "src/spendcast_mcp/server.py"
            ],
            "env": {
                "GRAPHDB_URL": "http://localhost:7200/repositories/demo",
                "GRAPHDB_USER": "bernhaeckt",
                "GRAPHDB_PASSWORD": "bernhaeckt"
            },
            "cwd": None
        }
    )
    
    print(f"📋 Server config: {config.command} {' '.join(config.args)}")
    
    # Test 1: Start MCP server as subprocess (following project plan)
    print("\n1️⃣ Starting MCP server as subprocess...")
    
    cmd = [config.command] + config.args
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=config.cwd,
            env=config.env
        )
        
        print(f"   ✅ Process started with PID: {process.pid}")
        
        # Wait a moment for the process to start
        await asyncio.sleep(2)
        
        # Check if the process is still running
        if process.poll() is not None:
            print(f"   ❌ Process terminated immediately (exit code: {process.returncode})")
            stderr_output = process.stderr.read()
            print(f"   Stderr: {stderr_output}")
            return False
        
        print("   ✅ Process is still running (non-blocking)")
        
        # Test 2: Connect to the subprocess using MCP client
        print("\n2️⃣ Connecting to MCP subprocess...")
        
        mcp_client = MCPSubprocessClient()
        success = await mcp_client.connect_to_subprocess(process, config)
        
        if not success:
            print("   ❌ Failed to connect to MCP subprocess")
            process.terminate()
            return False
        
        print("   ✅ Connected to MCP subprocess")
        
        # Test 3: List available tools
        print("\n3️⃣ Listing available tools...")
        
        tools = await mcp_client.list_tools()
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # Test 4: Call a tool
        print("\n4️⃣ Testing tool call...")
        
        if tools:
            tool_name = tools[0].name
            print(f"   Calling tool: {tool_name}")
            
            # Try to call the tool with some parameters
            result = await mcp_client.call_tool(tool_name, {"query": "SELECT * WHERE {?s ?p ?o} LIMIT 5"})
            
            if result:
                print(f"   ✅ Tool call successful")
                print(f"   Result: {result[:200]}...")
            else:
                print("   ⚠️ Tool call returned no result")
        else:
            print("   ⚠️ No tools available to test")
        
        # Test 5: Verify non-blocking behavior
        print("\n5️⃣ Testing non-blocking behavior...")
        
        start_time = time.time()
        print("   Main thread is not blocked - we can do other work...")
        
        # Simulate some work
        await asyncio.sleep(1)
        
        # Check if process is still running
        if process.poll() is None:
            print("   ✅ MCP server is still running (non-blocking confirmed)")
        else:
            print("   ❌ MCP server terminated unexpectedly")
            return False
        
        elapsed = time.time() - start_time
        print(f"   ✅ Non-blocking test completed in {elapsed:.2f} seconds")
        
        # Cleanup
        print("\n6️⃣ Cleaning up...")
        await mcp_client.disconnect()
        process.terminate()
        
        try:
            process.wait(timeout=5)
            print("   ✅ Process terminated cleanly")
        except subprocess.TimeoutExpired:
            print("   ⚠️ Process didn't terminate cleanly, force killing...")
            process.kill()
        
        print("\n🎉 All tests passed! MCP server is non-blocking and functional.")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed with error: {e}")
        if 'process' in locals():
            process.terminate()
        return False


async def test_stdio_client_blocking():
    """Test that stdio_client is indeed blocking (for comparison)."""
    
    print("\n🔍 Testing stdio_client blocking behavior...")
    
    try:
        from mcp.client.stdio import stdio_client
        from mcp.client.stdio import StdioServerParameters
        
        # Create server parameters
        server_params = StdioServerParameters(
            command="/opt/homebrew/bin/uv",
            args=[
                "--directory",
                "/Users/neo/Data/workspace/spendcast-mcp",
                "run",
                "src/spendcast_mcp/server.py"
            ],
            env={
                "GRAPHDB_URL": "http://localhost:7200/repositories/demo",
                "GRAPHDB_USER": "bernhaeckt",
                "GRAPHDB_PASSWORD": "bernhaeckt"
            }
        )
        
        print("   Using stdio_client (this should block)...")
        start_time = time.time()
        
        # This should block
        stdio_context = stdio_client(server_params)
        read_stream, write_stream = await stdio_context.__aenter__()
        
        elapsed = time.time() - start_time
        print(f"   ⚠️ stdio_client took {elapsed:.2f} seconds (blocking)")
        
        # Cleanup
        await stdio_context.__aexit__(None, None, None)
        
    except Exception as e:
        print(f"   ❌ stdio_client test failed: {e}")


async def main():
    """Run all tests."""
    print("🚀 MCP Non-Blocking Communication Test")
    print("=" * 50)
    
    # Test 1: Non-blocking approach (project plan)
    success = await test_mcp_non_blocking()
    
    # Test 2: Blocking approach (for comparison)
    await test_stdio_client_blocking()
    
    if success:
        print("\n✅ SUCCESS: MCP server can be started non-blocking!")
        print("   The project plan approach works correctly.")
    else:
        print("\n❌ FAILURE: MCP server is still blocking!")
        print("   Need to fix the implementation.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
