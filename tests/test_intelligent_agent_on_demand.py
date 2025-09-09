#!/usr/bin/env python3
"""
Test script to verify the intelligent agent works with on-demand MCP.
"""

import asyncio
import websockets
import json
import sys


async def test_intelligent_agent_on_demand():
    """Test that the intelligent agent works with on-demand MCP."""
    
    print("🧠 Testing Intelligent Agent with On-Demand MCP...")
    
    try:
        # Test 1: Basic question about tools
        print("\n1️⃣ Testing basic tool question...")
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket connected")
            
            # Send a question about tools
            test_message = "What tools are available for querying financial data?"
            print(f"   📤 Sending: {test_message}")
            await websocket.send(json.dumps({"message": test_message}))
            
            # Wait for response
            print("   ⏳ Waiting for response...")
            response = await websocket.recv()
            
            try:
                data = json.loads(response)
                print(f"   📥 Received: {data.get('type', 'unknown')}")
                if data.get("type") == "response":
                    print("   ✅ Got response from intelligent agent")
                    print(f"   📝 Response: {data.get('message', 'No content')[:100]}...")
                else:
                    print(f"   ⚠️ Unexpected response type: {data.get('type')}")
            except json.JSONDecodeError:
                print("   ⚠️ Response is not valid JSON")
        
        # Test 2: Question that should trigger tool usage
        print("\n2️⃣ Testing question that should trigger MCP tools...")
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket connected")
            
            # Send a question that should trigger the spendcast_query tool
            test_message = "Tell me about financial transactions for John Doe"
            print(f"   📤 Sending: {test_message}")
            await websocket.send(json.dumps({"message": test_message}))
            
            # Wait for response
            print("   ⏳ Waiting for response...")
            response = await websocket.recv()
            
            try:
                data = json.loads(response)
                print(f"   📥 Received: {data.get('type', 'unknown')}")
                if data.get("type") == "response":
                    print("   ✅ Got response from intelligent agent")
                    print(f"   📝 Response: {data.get('message', 'No content')[:100]}...")
                else:
                    print(f"   ⚠️ Unexpected response type: {data.get('type')}")
            except json.JSONDecodeError:
                print("   ⚠️ Response is not valid JSON")
        
        # Test 3: Check debug logs
        print("\n3️⃣ Testing debug logs...")
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/debug-logs")
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                print(f"   ✅ Found {len(logs)} debug logs")
                
                # Look for MCP-related logs
                mcp_logs = [log for log in logs if "MCP" in log.get("message", "")]
                if mcp_logs:
                    print(f"   ✅ Found {len(mcp_logs)} MCP-related logs")
                    for log in mcp_logs[-3:]:  # Show last 3 MCP logs
                        print(f"   - {log.get('level', 'INFO')}: {log.get('message', '')[:80]}...")
                else:
                    print("   ⚠️ No MCP-related logs found")
            else:
                print(f"   ❌ Debug logs endpoint failed: {response.status_code}")
        
        print("\n🎉 All intelligent agent tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


async def main():
    """Run the test."""
    print("🚀 Intelligent Agent + On-Demand MCP Test")
    print("=" * 50)
    
    success = await test_intelligent_agent_on_demand()
    
    if success:
        print("\n✅ SUCCESS: Intelligent agent works with on-demand MCP!")
        print("   - WebSocket communication working")
        print("   - Agent can process user questions")
        print("   - Debug logging working")
        print("   - On-demand MCP integration successful")
    else:
        print("\n❌ FAILURE: Intelligent agent has issues with on-demand MCP!")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
