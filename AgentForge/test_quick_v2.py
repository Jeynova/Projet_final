#!/usr/bin/env python3
"""
Simple test to verify real-time monitoring with a quick project
"""
import requests
import json
import time

def test_quick_v2():
    """Test V2 with a simple, fast project"""
    print("🎯 Testing V2 with Simple Project")
    print("🌐 Open http://localhost:5001/create in browser to see real-time updates")
    print("=" * 60)
    
    payload = {
        "prompt": "Simple calculator API with add, subtract, multiply, divide endpoints using FastAPI",
        "orchestrator": "v2",
        "name": f"quick-calc-{int(time.time())}",
        "llm_mode": "ollama"
    }
    
    print(f"📝 Testing: {payload['prompt']}")
    print(f"🚀 Starting...")
    
    try:
        response = requests.post("http://localhost:5001/api/orchestrate", json=payload)
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Started! Session: {result.get('session_id')}")
            print(f"💡 Check browser console for SocketIO events")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

if __name__ == "__main__":
    test_quick_v2()
