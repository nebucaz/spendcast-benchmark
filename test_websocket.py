#!/usr/bin/env python3
"""
Test script to simulate WebSocket interaction and test enhanced debug logging
"""
import asyncio
import websockets
import json
import time

async def test_websocket_interaction():
    """Test WebSocket interaction to trigger debug logging"""
    
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            
            # Send a test message
            test_message = {
                "message": "What tools are available?"
            }
            
            print(f"Sending message: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for multiple responses
            print("Waiting for responses...")
            for i in range(10):  # Wait for up to 10 responses
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    print(f"Received response {i+1}: {response}")
                    
                    # Check if it's a final response
                    data = json.loads(response)
                    if data.get("type") == "response":
                        print("Got final response!")
                        break
                except asyncio.TimeoutError:
                    print(f"Timeout waiting for response {i+1}")
                    break
            
    except asyncio.TimeoutError:
        print("Timeout waiting for response")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_interaction())
