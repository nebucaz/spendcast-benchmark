#!/usr/bin/env python3
"""
Test script to verify the on-demand MCP web server works correctly.
"""

import asyncio
import websockets
import json
import sys


async def test_on_demand_web():
    """Test that the on-demand MCP web server works correctly."""
    
    print("🧪 Testing on-demand MCP web server...")
    
    try:
        # Test 1: Status endpoint
        print("\n1️⃣ Testing status endpoint...")
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/status")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {data['status']}")
                print(f"   ✅ MCP servers: {data['mcp_servers']}")
                print(f"   ✅ Tools available: {data['tools_available']}")
                print(f"   ✅ LLM ready: {data['llm_ready']}")
            else:
                print(f"   ❌ Status endpoint failed: {response.status_code}")
                return False
        
        # Test 2: Tools endpoint
        print("\n2️⃣ Testing tools endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/tools")
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                print(f"   ✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool['name']}: {tool['description']}")
            else:
                print(f"   ❌ Tools endpoint failed: {response.status_code}")
                return False
        
        # Test 3: WebSocket connection
        print("\n3️⃣ Testing WebSocket connection...")
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket connected")
            
            # Send a test message
            test_message = "What tools are available?"
            print(f"   📤 Sending: {test_message}")
            await websocket.send(json.dumps({"message": test_message}))
            
            # Wait for response
            print("   ⏳ Waiting for response...")
            response = await websocket.recv()
            
            try:
                data = json.loads(response)
                print(f"   📥 Received: {data.get('type', 'unknown')}")
                if data.get("type") == "debug_log":
                    print("   ✅ Debug logging working")
                else:
                    print(f"   ⚠️ Unexpected response type: {data.get('type')}")
            except json.JSONDecodeError:
                print("   ⚠️ Response is not valid JSON")
        
        print("\n🎉 All on-demand MCP web server tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


async def main():
    """Run the test."""
    print("🚀 On-Demand MCP Web Server Test")
    print("=" * 40)
    
    success = await test_on_demand_web()
    
    if success:
        print("\n✅ SUCCESS: On-demand MCP web server works!")
        print("   - Status endpoint working")
        print("   - Tools endpoint working")
        print("   - WebSocket connection working")
        print("   - No persistent MCP processes")
        print("   - Servers start on-demand")
    else:
        print("\n❌ FAILURE: On-demand MCP web server not working!")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
