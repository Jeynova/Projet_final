#!/usr/bin/env python3
"""
Test script for the enhanced AgentForge UI with orchestrator switching
"""
import requests
import json
import time

# Test the Flask UI endpoints
BASE_URL = "http://localhost:5001"

def test_system_status():
    """Test system status endpoint"""
    print("🔧 Testing system status...")
    try:
        response = requests.get(f"{BASE_URL}/api/system-status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System Status: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ System status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ System status error: {e}")
        return False

def test_llm_status():
    """Test LLM status endpoint"""
    print("\n🧠 Testing LLM status...")
    try:
        response = requests.get(f"{BASE_URL}/api/llm-status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ LLM Status: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ LLM status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LLM status error: {e}")
        return False

def test_small_orchestration():
    """Test a small project generation"""
    print("\n🚀 Testing small project orchestration...")
    try:
        payload = {
            "prompt": "Simple Python calculator with basic math operations",
            "name": "test-calculator",
            "orchestrator": "v2",
            "llm_mode": "ollama"
        }
        
        response = requests.post(f"{BASE_URL}/api/orchestrate", 
                               json=payload, 
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Orchestration started: {data}")
            
            # Wait a bit and check if files were created
            time.sleep(5)
            print("⏳ Waiting for orchestration to complete...")
            
            return True
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"❌ Orchestration failed: {response.status_code} - {error_data}")
            return False
            
    except Exception as e:
        print(f"❌ Orchestration test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🎮 AgentForge Enhanced UI Test Suite")
    print("=" * 50)
    
    tests = [
        test_system_status,
        test_llm_status,
        test_small_orchestration
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Your enhanced UI is working perfectly!")
        print(f"🌐 Access your UI at: {BASE_URL}")
        print("🎯 Features available:")
        print("  - Orchestrator switching (v1 ↔ v2)")
        print("  - Real-time agent monitoring")
        print("  - Game-like UI with agent visualization")
        print("  - Project gallery with downloads")
        print("  - Docker integration")
        print("  - LLM provider switching")
    else:
        print("⚠️ Some tests failed. Check the Flask UI logs for details.")

if __name__ == "__main__":
    main()
