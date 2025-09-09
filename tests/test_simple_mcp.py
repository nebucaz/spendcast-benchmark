#!/usr/bin/env python3
"""
Simple test to verify MCP server can be started non-blocking.
"""

import asyncio
import subprocess
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp import MCPServerConfig


async def test_simple_mcp_start():
    """Test that MCP server can be started non-blocking."""
    
    print("🧪 Testing MCP server non-blocking start...")
    
    # Create server config
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
    
    print(f"📋 Starting: {config.command} {' '.join(config.args)}")
    
    # Start MCP server as subprocess (following project plan)
    cmd = [config.command] + config.args
    
    try:
        print("🚀 Starting subprocess...")
        start_time = time.time()
        
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
        
        elapsed = time.time() - start_time
        print(f"✅ Subprocess started in {elapsed:.3f} seconds (PID: {process.pid})")
        
        # Wait a moment for the process to start
        print("⏳ Waiting for process to initialize...")
        await asyncio.sleep(2)
        
        # Check if the process is still running
        if process.poll() is not None:
            print(f"❌ Process terminated immediately (exit code: {process.returncode})")
            stderr_output = process.stderr.read()
            print(f"Stderr: {stderr_output}")
            return False
        
        print("✅ Process is still running (non-blocking confirmed)")
        
        # Test that we can do other work while the process runs
        print("🔄 Testing non-blocking behavior...")
        for i in range(3):
            print(f"   Doing work {i+1}/3...")
            await asyncio.sleep(0.5)
            
            if process.poll() is not None:
                print(f"❌ Process terminated unexpectedly during work")
                return False
        
        print("✅ Non-blocking behavior confirmed")
        
        # Cleanup
        print("🧹 Cleaning up...")
        process.terminate()
        
        try:
            process.wait(timeout=5)
            print("✅ Process terminated cleanly")
        except subprocess.TimeoutExpired:
            print("⚠️ Process didn't terminate cleanly, force killing...")
            process.kill()
        
        print("🎉 SUCCESS: MCP server can be started non-blocking!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        if 'process' in locals():
            process.terminate()
        return False


async def test_stdio_client_blocking():
    """Test that stdio_client is blocking (for comparison)."""
    
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
    """Run tests."""
    print("🚀 Simple MCP Non-Blocking Test")
    print("=" * 40)
    
    # Test 1: Non-blocking approach
    success = await test_simple_mcp_start()
    
    # Test 2: Blocking approach (for comparison)
    await test_stdio_client_blocking()
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
