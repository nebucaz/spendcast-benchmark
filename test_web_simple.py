#!/usr/bin/env python3
"""
Simple test to verify the web interface is working.
"""

import asyncio
import websockets
import json
import time

async def test_web_simple():
    """Test the web interface with a simple request."""
    
    print("🌐 Testing Web Interface...")
    
    try:
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket connected")
            
            # Send a simple request
            test_message = "Hello, what tools are available?"
            print(f"   📤 Sending: {test_message}")
            await websocket.send(json.dumps({"message": test_message}))
            
            # Wait for responses (might be multiple messages)
            print("   ⏳ Waiting for responses...")
            responses = []
            
            for i in range(15):  # Wait for up to 15 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    responses.append(data)
                    print(f"   📥 Message {i+1}: {data.get('type', 'unknown')} - {str(data.get('message', ''))[:50]}...")
                    
                    if data.get('type') == 'response':
                        print(f"   ✅ Got final response: {data.get('message', 'No content')[:100]}...")
                        break
                        
                except asyncio.TimeoutError:
                    print("   ⏰ Timeout waiting for response")
                    break
                except json.JSONDecodeError:
                    print("   ⚠️ Invalid JSON received")
                    break
            
            print(f"   📊 Total messages received: {len(responses)}")
            
            # Check if we got a proper response
            response_messages = [r for r in responses if r.get('type') == 'response']
            if response_messages:
                print("   ✅ SUCCESS: Web interface is working!")
                return True
            else:
                print("   ❌ FAILURE: No response message received")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

async def main():
    """Run the test."""
    print("🚀 Simple Web Interface Test")
    print("=" * 40)
    
    success = await test_web_simple()
    
    if success:
        print("\n✅ SUCCESS: Web interface is working!")
    else:
        print("\n❌ FAILURE: Web interface has issues!")

if __name__ == "__main__":
    asyncio.run(main())
