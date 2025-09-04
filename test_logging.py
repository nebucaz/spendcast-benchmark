#!/usr/bin/env python3
"""
Test script to demonstrate enhanced debug logging
"""
import requests
import json
import time

def test_enhanced_logging():
    """Test the enhanced debug logging by making a request"""
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    # Check server status
    try:
        response = requests.get("http://localhost:8000/api/status")
        if response.status_code == 200:
            status = response.json()
            print(f"Server status: {status}")
        else:
            print(f"Server not ready: {response.status_code}")
            return
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return
    
    # Make a test request (simulate what the web interface would do)
    print("\nMaking test request...")
    
    # Since there's no direct API endpoint, we'll check the debug logs
    # to see if there are any interactions from the web interface
    
    print("Checking debug logs...")
    try:
        response = requests.get("http://localhost:8000/api/debug-logs")
        if response.status_code == 200:
            logs = response.json()
            print(f"Total debug logs: {len(logs.get('logs', []))}")
            
            # Show the last few logs
            recent_logs = logs.get('logs', [])[-5:]
            for log in recent_logs:
                print(f"\n[{log['timestamp']}] {log['category']}: {log['message']}")
                if 'data' in log:
                    print(f"  Data: {json.dumps(log['data'], indent=2)}")
        else:
            print(f"Error getting debug logs: {response.status_code}")
    except Exception as e:
        print(f"Error getting debug logs: {e}")

if __name__ == "__main__":
    test_enhanced_logging()
