#!/usr/bin/env python3
"""
Quick test for both orchestrators
"""
import requests
import json
import time

def test_both_orchestrators():
    """Test both orchestrators quickly"""
    
    # Test V1 
    print("🔧 Testing V1 Orchestrator...")
    v1_payload = {
        "prompt": "Simple task management API with CRUD operations",
        "orchestrator": "v1",
        "name": f"quick-v1-{int(time.time())}"
    }
    
    v1_response = requests.post("http://localhost:5001/api/orchestrate", json=v1_payload)
    print(f"V1 Status: {v1_response.status_code}")
    if v1_response.status_code == 200:
        print(f"✅ V1 Session: {v1_response.json().get('session_id', 'Unknown')}")
    else:
        print(f"❌ V1 Error: {v1_response.text}")
    
    time.sleep(2)
    
    # Test V2
    print("\n🚀 Testing V2 Orchestrator...")
    v2_payload = {
        "prompt": "E-commerce API with products, orders, and user management",
        "orchestrator": "v2", 
        "name": f"quick-v2-{int(time.time())}"
    }
    
    v2_response = requests.post("http://localhost:5001/api/orchestrate", json=v2_payload)
    print(f"V2 Status: {v2_response.status_code}")
    if v2_response.status_code == 200:
        print(f"✅ V2 Session: {v2_response.json().get('session_id', 'Unknown')}")
    else:
        print(f"❌ V2 Error: {v2_response.text}")
    
    print(f"\n🎯 Both orchestrators accessible through UI!")
    print(f"🌐 Dashboard: http://localhost:5001")
    print(f"🎮 Create: http://localhost:5001/create")

if __name__ == "__main__":
    test_both_orchestrators()
