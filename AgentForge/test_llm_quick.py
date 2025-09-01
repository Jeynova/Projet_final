#!/usr/bin/env python3
"""
Quick test of the LLM connection and our organic intelligence
"""
import sys
sys.path.append('.')

from core.llm_client import LLMClient

def test_basic_llm():
    print("🧪 Testing basic LLM connection...")
    
    try:
        client = LLMClient()
        
        # Simple test call
        system_prompt = "You are a helpful assistant. Respond with valid JSON."
        user_prompt = "What technologies would you choose for a simple blog? Respond with JSON: {\"backend\": \"your_choice\", \"reasoning\": \"why\"}"
        
        print("📞 Making LLM call...")
        result = client.extract_json(system_prompt, user_prompt)
        
        print(f"✅ LLM Response: {result}")
        
        if result:
            backend = result.get('backend', 'Unknown')
            reasoning = result.get('reasoning', 'No reasoning provided')
            print(f"🎯 LLM chose: {backend}")
            print(f"💭 Reasoning: {reasoning}")
        
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_llm()
