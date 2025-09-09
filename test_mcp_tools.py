#!/usr/bin/env python3
"""
Test script to check what tools are actually available on the MCP server.
"""

import asyncio
import logging
import sys
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

async def check_mcp_tools():
    """Check what tools are available on the MCP server."""
    print("\n🔍 Checking MCP Server Tools")
    print("=" * 50)
    
    try:
        # Load configurations
        configs = load_mcp_configs()
        if not configs:
            print("❌ No MCP server configurations found")
            return
        
        print(f"✅ Loaded {len(configs)} MCP server configurations")
        
        # Create manager
        manager = MCPOnDemandManager(configs)
        print("✅ Created MCP on-demand manager")
        
        # Get available tools
        tools = await manager.get_available_tools()
        print(f"\n📋 Available tools from manager ({len(tools)}):")
        for i, tool in enumerate(tools, 1):
            name = tool.get("name", "unknown")
            description = tool.get("description", "no description")
            print(f"   {i}. {name}: {description}")
        
        # Test with the correct tool names from the server
        print(f"\n🚀 Testing tool calls with real server tools...")
        
        # Test execute_sparql tool
        print(f"\n🔧 Testing execute_sparql tool...")
        result = await manager.call_tool("execute_sparql", {"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 5"})
        
        if result:
            print(f"✅ execute_sparql success: {result[:200]}...")
        else:
            print("❌ execute_sparql failed")
        
        # Test get_schema_help tool
        print(f"\n🔧 Testing get_schema_help tool...")
        result = await manager.call_tool("get_schema_help", {})
        
        if result:
            print(f"✅ get_schema_help success: {result[:200]}...")
        else:
            print("❌ get_schema_help failed")
        
        await manager.shutdown()
        print("\n✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_mcp_tools())
