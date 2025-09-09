#!/usr/bin/env python3
"""
Direct test of the intelligent agent to debug the issue.
"""

import asyncio
import logging
from src.mcp_client import load_mcp_configs
from src.mcp_on_demand_manager import MCPOnDemandManager
from src.llm_client import LLMClient
from src.intelligent_agent import IntelligentAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_direct():
    """Test the intelligent agent directly."""
    
    print("🧪 Testing Intelligent Agent Directly...")
    
    try:
        # Load MCP configs
        configs = load_mcp_configs()
        print(f"✅ Loaded {len(configs)} MCP configs")
        
        # Create MCP manager
        mcp_manager = MCPOnDemandManager(configs)
        print("✅ Created MCP on-demand manager")
        
        # Create LLM client
        llm_client = LLMClient()
        await llm_client.setup()
        print("✅ Created LLM client")
        
        # Create intelligent agent
        agent = IntelligentAgent(llm_client, mcp_manager, None)
        print("✅ Created intelligent agent")
        
        # Test a simple request
        print("\n📤 Testing simple request...")
        response = await agent.process_user_request("What tools are available?")
        print(f"📥 Response: {response}")
        
        # Test a request that should trigger tools
        print("\n📤 Testing tool-triggering request...")
        response = await agent.process_user_request("Tell me about financial transactions for John Doe")
        print(f"📥 Response: {response}")
        
        # Cleanup
        await llm_client.close()
        await mcp_manager.shutdown()
        
        print("\n🎉 Direct agent test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    print("🚀 Direct Intelligent Agent Test")
    print("=" * 40)
    
    success = await test_agent_direct()
    
    if success:
        print("\n✅ SUCCESS: Direct agent test passed!")
    else:
        print("\n❌ FAILURE: Direct agent test failed!")

if __name__ == "__main__":
    asyncio.run(main())
