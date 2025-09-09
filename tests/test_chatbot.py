#!/usr/bin/env python3
"""
Test script to verify the chatbot can use MCP tools end-to-end.
"""

import asyncio
import websockets
import json
import sys


async def test_chatbot_mcp():
    """Test that the chatbot can use MCP tools."""
    
    print("🧪 Testing chatbot MCP tool usage...")
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send a test message that should trigger MCP tool usage
            test_message = "What tools are available for querying financial data?"
            
            print(f"📤 Sending message: {test_message}")
            await websocket.send(json.dumps({"message": test_message}))
            
            # Wait for response
            print("⏳ Waiting for response...")
            response = await websocket.recv()
            
            print(f"📥 Received response: {response}")
            
            # Parse response
            try:
                data = json.loads(response)
                if data.get("type") == "response":
                    print("✅ Received valid response")
                    print(f"📝 Response content: {data.get('content', '')[:200]}...")
                else:
                    print(f"⚠️ Unexpected response type: {data.get('type')}")
            except json.JSONDecodeError:
                print("⚠️ Response is not valid JSON")
            
            # Send another test message
            test_message2 = "Tell me about financial transactions for John Doe"
            
            print(f"\n📤 Sending message: {test_message2}")
            await websocket.send(json.dumps({"message": test_message2}))
            
            # Wait for response
            print("⏳ Waiting for response...")
            response2 = await websocket.recv()
            
            print(f"📥 Received response: {response2}")
            
            # Parse response
            try:
                data2 = json.loads(response2)
                if data2.get("type") == "response":
                    print("✅ Received valid response")
                    print(f"📝 Response content: {data2.get('content', '')[:200]}...")
                else:
                    print(f"⚠️ Unexpected response type: {data2.get('type')}")
            except json.JSONDecodeError:
                print("⚠️ Response is not valid JSON")
            
            print("\n🎉 Chatbot MCP test completed!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


async def main():
    """Run the test."""
    print("🚀 Chatbot MCP Tool Usage Test")
    print("=" * 40)
    
    success = await test_chatbot_mcp()
    
    if success:
        print("\n✅ SUCCESS: Chatbot can use MCP tools!")
    else:
        print("\n❌ FAILURE: Chatbot MCP integration not working!")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
