#!/usr/bin/env python3
"""
Test script for orchestrator UI integration
Tests both v1 and v2 orchestrators through the Flask UI
"""
import requests
import json
import time

def test_orchestrator(version, description, tech_stack=""):
    """Test orchestrator creation through UI API"""
    print(f"\n🎯 Testing Orchestrator {version.upper()}")
    print(f"📝 Description: {description}")
    
    url = "http://localhost:5001/api/orchestrate"
    payload = {
        "prompt": description,
        "orchestrator": version,
        "name": f"test-{version}-{int(time.time())}"
    }
    
    if tech_stack:
        payload["tech_stack"] = tech_stack
    
    print(f"🚀 Sending request to {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=300)  # 5 minute timeout
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Project created: {result.get('project_id', 'Unknown')}")
            print(f"📊 Quality Score: {result.get('quality_score', 'N/A')}")
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

def main():
    print("🎮 AgentForge Orchestrator UI Test")
    print("=" * 50)
    
    # Test system status first
    try:
        response = requests.get("http://localhost:5001/api/system-status")
        if response.status_code == 200:
            status = response.json()
            print(f"🔧 System Status: {json.dumps(status, indent=2)}")
        else:
            print(f"⚠️ System status check failed: {response.status_code}")
    except Exception as e:
        print(f"💥 Cannot connect to Flask server: {e}")
        return
    
    # Test V1 Orchestrator
    v1_success = test_orchestrator(
        "v1", 
        "Simple to-do list web app with user authentication",
        "python,flask,sqlite"
    )
    
    time.sleep(2)  # Brief pause between tests
    
    # Test V2 Orchestrator  
    v2_success = test_orchestrator(
        "v2",
        "REST API for managing a library with books and authors"
    )
    
    print(f"\n📊 Test Results:")
    print(f"V1 Orchestrator: {'✅ PASS' if v1_success else '❌ FAIL'}")
    print(f"V2 Orchestrator: {'✅ PASS' if v2_success else '❌ FAIL'}")

if __name__ == "__main__":
    main()
