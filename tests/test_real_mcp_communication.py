#!/usr/bin/env python3
"""
Test script to verify real MCP communication with the spendcast server.
This test specifically checks if we can connect to the real MCP server and execute tools.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp_client import load_mcp_configs
from src.mcp_on_demand_manager import MCPOnDemandManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_real_mcp_communication():
    """Test real MCP communication with the spendcast server."""
    print("\n🔗 Testing Real MCP Communication")
    print("=" * 50)
    
    try:
        # Load configurations
        configs = load_mcp_configs()
        if not configs:
            print("❌ No MCP server configurations found")
            return False
        
        print(f"✅ Loaded {len(configs)} MCP server configurations")
        
        # Create manager
        manager = MCPOnDemandManager(configs)
        print("✅ Created MCP on-demand manager")
        
        # Test 1: List available tools
        print("\n📋 Testing tool listing...")
        tools = await manager.get_available_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            if isinstance(tool, dict):
                print(f"   🔧 {tool.get('name', 'unknown')}: {tool.get('description', 'No description')}")
            else:
                print(f"   🔧 {tool.name}: {tool.description}")
        
        # Test 2: Try to call a tool (this should start the real MCP server)
        print("\n🚀 Testing tool execution...")
        try:
            # Try to call the spendcast_query tool with a simple query
            result = await manager.call_tool("spendcast_query", {
                "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 5"
            })
            
            if result:
                print(f"✅ Tool call successful!")
                print(f"   Result: {result[:200]}...")
            else:
                print("⚠️ Tool call returned no result")
                
        except Exception as e:
            print(f"❌ Tool call failed: {e}")
            return False
        
        # Test 3: Check server status
        print("\n📊 Checking server status...")
        status = await manager.get_server_status()
        print(f"✅ Server status: {status}")
        
        # Test 4: Shutdown
        print("\n🛑 Shutting down...")
        await manager.shutdown()
        print("✅ Shutdown successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Real MCP communication test failed: {e}")
        logger.exception("Detailed error:")
        return False

async def main():
    """Run the real MCP communication test."""
    print("🚀 Real MCP Communication Test")
    print("=" * 50)
    
    success = await test_real_mcp_communication()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Real MCP communication test passed!")
        print("✅ The MCP server is working correctly with real communication")
    else:
        print("❌ Real MCP communication test failed!")
        print("⚠️ The MCP server may still be using mock communication")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
