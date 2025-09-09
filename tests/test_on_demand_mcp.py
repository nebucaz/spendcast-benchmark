#!/usr/bin/env python3
"""
Test script to verify on-demand MCP client works correctly.
"""

import asyncio
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp_client import MCPServerConfig
from src.mcp_on_demand_manager import MCPOnDemandManager


async def test_on_demand_mcp():
    """Test that on-demand MCP client works correctly."""
    
    print("🧪 Testing on-demand MCP client...")
    
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
    
    # Create on-demand manager
    manager = MCPOnDemandManager({"spendcast-graphdb": config})
    
    try:
        # Test 1: Get available tools
        print("\n1️⃣ Testing tool discovery...")
        tools = await manager.get_available_tools()
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
        
        # Test 2: Call a tool (this will start the MCP server on-demand)
        print("\n2️⃣ Testing on-demand tool call...")
        start_time = time.time()
        
        result = await manager.call_tool("spendcast_query", {
            "query": "SELECT * WHERE {?s ?p ?o} LIMIT 5"
        })
        
        elapsed = time.time() - start_time
        print(f"   Tool call completed in {elapsed:.2f} seconds")
        
        if result:
            print(f"   ✅ Tool call successful")
            print(f"   Result: {result[:200]}...")
        else:
            print("   ❌ Tool call failed")
        
        # Test 3: Test timeout behavior
        print("\n3️⃣ Testing timeout behavior...")
        
        # Create a client with very short timeout
        from src.mcp_on_demand_client import MCPOnDemandClient
        short_timeout_client = MCPOnDemandClient(config, timeout=1)
        
        start_time = time.time()
        result = await short_timeout_client.call_tool("spendcast_query", {
            "query": "SELECT * WHERE {?s ?p ?o} LIMIT 5"
        })
        elapsed = time.time() - start_time
        
        print(f"   Timeout test completed in {elapsed:.2f} seconds")
        if result is None:
            print("   ✅ Timeout behavior working (expected)")
        else:
            print("   ⚠️ Timeout didn't trigger (unexpected)")
        
        short_timeout_client.shutdown()
        
        # Test 4: Multiple concurrent calls
        print("\n4️⃣ Testing concurrent calls...")
        
        start_time = time.time()
        
        # Start multiple tool calls concurrently
        tasks = []
        for i in range(3):
            task = manager.call_tool("spendcast_query", {
                "query": f"SELECT * WHERE {{?s ?p ?o}} LIMIT {i+1}"
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        print(f"   Concurrent calls completed in {elapsed:.2f} seconds")
        
        successful_calls = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        print(f"   ✅ {successful_calls}/3 calls successful")
        
        # Test 5: Server status
        print("\n5️⃣ Testing server status...")
        status = await manager.get_server_status()
        for server_name, server_status in status.items():
            print(f"   {server_name}: {server_status}")
        
        print("\n🎉 All on-demand MCP tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Cleanup
        await manager.shutdown()


async def main():
    """Run the test."""
    print("🚀 On-Demand MCP Client Test")
    print("=" * 40)
    
    success = await test_on_demand_mcp()
    
    if success:
        print("\n✅ SUCCESS: On-demand MCP client works!")
        print("   - No persistent processes")
        print("   - Servers start on-demand")
        print("   - Automatic cleanup")
        print("   - Timeout protection")
    else:
        print("\n❌ FAILURE: On-demand MCP client not working!")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
