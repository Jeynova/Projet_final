#!/usr/bin/env python3
"""
Interactive test to see real-time agent monitoring in the UI
This will create a project using V2 orchestrator and show the agent execution
"""
import requests
import json
import time

def test_v2_with_monitoring():
    """Test V2 orchestrator with detailed monitoring"""
    print("🚀 Testing V2 Orchestrator with Real-time Monitoring")
    print("🔗 Open http://localhost:5001/create in your browser to see real-time updates")
    print("=" * 60)
    
    url = "http://localhost:5001/api/orchestrate"
    payload = {
        "prompt": "Create a modern blog platform with user authentication, post management, comments, and admin dashboard using FastAPI",
        "orchestrator": "v2",
        "name": f"monitored-blog-v2-{int(time.time())}",
        "llm_mode": "ollama"
    }
    
    print(f"📝 Prompt: {payload['prompt']}")
    print(f"🎮 Orchestrator: {payload['orchestrator']}")
    print(f"📦 Project Name: {payload['name']}")
    print("\n🔄 Starting orchestration...")
    
    try:
        response = requests.post(url, json=payload, timeout=600)  # 10 minute timeout
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id', 'Unknown')
            print(f"✅ Orchestration started!")
            print(f"🔍 Session ID: {session_id}")
            print(f"📊 Watch the browser for real-time agent execution!")
            
            # Wait a bit for completion
            print("\n⏳ Waiting for completion (check UI for real-time updates)...")
            time.sleep(10)
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"💀 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"💀 Raw error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"💥 Request failed: {e}")
        return False

if __name__ == "__main__":
    test_v2_with_monitoring()
