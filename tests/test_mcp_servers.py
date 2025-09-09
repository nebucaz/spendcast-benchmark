#!/usr/bin/env python3
"""
Simple test script to verify MCP server configuration and basic functionality.
This test checks:
1. MCP server configuration loading
2. MCP server startup (without blocking)
3. Basic tool listing
4. Server status
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp import load_mcp_configs, MCPServerConfig
from src.mcp import MCPOnDemandManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_mcp_configuration():
    """Test MCP server configuration loading."""
    print("\n🔧 Testing MCP Configuration")
    print("=" * 50)
    
    try:
        # Load configurations
        configs = load_mcp_configs()
        print(f"✅ Loaded {len(configs)} MCP server configurations")
        
        for name, config in configs.items():
            print(f"   📋 {name}:")
            print(f"      Command: {config.command}")
            print(f"      Args: {config.args}")
            print(f"      CWD: {config.cwd}")
            print(f"      Env: {config.env}")
        
        return configs
    except Exception as e:
        print(f"❌ Failed to load MCP configurations: {e}")
        return None

async def test_mcp_manager():
    """Test MCP on-demand manager creation."""
    print("\n🏗️ Testing MCP Manager")
    print("=" * 50)
    
    try:
        # Load configurations
        configs = load_mcp_configs()
        if not configs:
            print("❌ No configurations available")
            return None
        
        # Create manager
        manager = MCPOnDemandManager(configs)
        print(f"✅ Created MCP on-demand manager with {len(configs)} servers")
        
        # Test available tools
        tools = await manager.get_available_tools()
        print(f"✅ Available tools: {len(tools)}")
        for tool in tools:
            if isinstance(tool, dict):
                print(f"   🔧 {tool.get('name', 'unknown')}: {tool.get('description', 'No description')}")
            else:
                print(f"   🔧 {tool.name}: {tool.description}")
        
        return manager
    except Exception as e:
        print(f"❌ Failed to create MCP manager: {e}")
        return None

async def test_basic_functionality():
    """Test basic MCP functionality without complex operations."""
    print("\n🧪 Testing Basic Functionality")
    print("=" * 50)
    
    try:
        # Load configurations
        configs = load_mcp_configs()
        if not configs:
            print("❌ No configurations available")
            return False
        
        # Create manager
        manager = MCPOnDemandManager(configs)
        print("✅ Manager created successfully")
        
        # Test tool listing
        tools = await manager.get_available_tools()
        print(f"✅ Tool listing successful: {len(tools)} tools found")
        
        # Test server status
        status = await manager.get_server_status()
        print(f"✅ Server status: {status}")
        
        # Test shutdown
        await manager.shutdown()
        print("✅ Manager shutdown successful")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 MCP Server Test Suite")
    print("=" * 50)
    
    # Test 1: Configuration loading
    configs = await test_mcp_configuration()
    if not configs:
        print("\n❌ Configuration test failed - stopping")
        return
    
    # Test 2: Manager creation
    manager = await test_mcp_manager()
    if not manager:
        print("\n❌ Manager test failed - stopping")
        return
    
    # Test 3: Basic functionality
    success = await test_basic_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())