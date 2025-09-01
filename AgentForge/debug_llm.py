#!/usr/bin/env python3
"""
🔥 DEBUG LLM CALLS
Check why LLM calls are not happening in Phase 2
"""
import sys
sys.path.append('.')

from core.llm_client import LLMClient

def test_direct_llm():
    """Test direct LLM calls to see if they work"""
    print("🔥 TESTING DIRECT LLM CALLS")
    print("="*40)
    
    llm = LLMClient()
    
    # Simple test
    simple_prompt = """Analyze this project and return JSON:

Project: "Create a modern blog platform"

Return:
{
    "domain": "blog",
    "tech": "React + FastAPI"
}"""
    
    print("🧪 Testing simple JSON extraction...")
    try:
        result = llm.extract_json("You are helpful", simple_prompt)
        print(f"✅ Result: {result}")
        print(f"✅ Type: {type(result)}")
        
        if result is None:
            print("❌ LLM returned None - this is the problem!")
        else:
            print("✅ LLM working correctly")
            
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test chat completion directly
    print("\n🧪 Testing chat completion...")
    try:
        response = llm.chat_completion(
            "You are helpful",
            "What is 2+2? Reply with just the number."
        )
        print(f"✅ Chat result: {response}")
    except Exception as e:
        print(f"❌ Chat failed: {e}")

def test_llm_json_method():
    """Test the exact method used in agents"""
    print("\n🔥 TESTING LLM_JSON METHOD")
    print("="*40)
    
    class TestAgent:
        def __init__(self):
            self.llm_client = LLMClient()
        
        def llm_json(self, system_prompt: str, user_prompt: str, fallback: dict):
            try:
                print(f"🔄 Calling LLM...")
                result = self.llm_client.extract_json(system_prompt, user_prompt)
                print(f"🔄 LLM result: {result}")
                print(f"🔄 Result type: {type(result)}")
                
                if result is None:
                    print("⚠️ LLM returned None, using fallback")
                    return fallback
                else:
                    print("✅ LLM returned valid result")
                    return result
            except Exception as e:
                print(f"❌ LLM call failed: {e}")
                return fallback
    
    agent = TestAgent()
    
    test_prompt = """Analyze this project:
    
Project: "Create a blog platform"

Return JSON:
{
    "domain": "blog",
    "reasoning": "This is clearly a blog project"
}"""
    
    fallback = {"domain": "fallback", "reasoning": "Using fallback"}
    
    result = agent.llm_json("You are helpful", test_prompt, fallback)
    print(f"🎯 Final result: {result}")
    
    if result == fallback:
        print("❌ PROBLEM: Always using fallback - LLM not working")
    else:
        print("✅ SUCCESS: LLM working correctly")

if __name__ == '__main__':
    test_direct_llm()
    test_llm_json_method()
