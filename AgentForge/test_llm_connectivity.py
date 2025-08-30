#!/usr/bin/env python3
"""Test LLM connectivity for orchestrator_v2"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from orchestrator_v2.agent_base import LLMBackedMixin

class TestAgent(LLMBackedMixin):
    id = "test"

def test_direct_llm():
    """Test direct LLM client"""
    print("🧪 Testing direct LLM client...")
    try:
        client = LLMClient()
        result = client.extract_json(
            system_prompt="You are a helpful assistant that returns JSON.",
            user_prompt="Create a simple JSON with a 'message' field saying 'hello world'."
        )
        print(f"✅ Direct LLM result: {result}")
        return True
    except Exception as e:
        print(f"❌ Direct LLM failed: {e}")
        return False

def test_mixin_llm():
    """Test LLM via mixin"""
    print("\n🧪 Testing LLM via mixin...")
    try:
        agent = TestAgent()
        result = agent.llm_json(
            system="You are a helpful assistant.",
            user="Return JSON with 'test': 'success'",
            fallback={"test": "fallback"}
        )
        print(f"✅ Mixin LLM result: {result}")
        if result.get("test") == "fallback":
            print("⚠️ Warning: Got fallback response (LLM may have failed)")
            return False
        return True
    except Exception as e:
        print(f"❌ Mixin LLM failed: {e}")
        return False

def test_code_generation():
    """Test code generation specifically"""
    print("\n🧪 Testing code generation...")
    try:
        agent = TestAgent()
        result = agent.llm_json(
            system="You write concise working code.",
            user="File app/main.py purpose entrypoint\nReturn JSON {code} strictly.",
            fallback={"code": "# fallback\nprint('fallback')"}
        )
        print(f"✅ Code gen result: {result}")
        if "fallback" in result.get("code", ""):
            print("⚠️ Warning: Got fallback code (LLM may have failed)")
            return False
        return True
    except Exception as e:
        print(f"❌ Code gen failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing LLM connectivity for orchestrator_v2\n")
    
    success = True
    success &= test_direct_llm()
    success &= test_mixin_llm()
    success &= test_code_generation()
    
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    
    if not success:
        print("\n🔧 Troubleshooting:")
        print("1. Check if Ollama is running: ollama serve")
        print("2. Check if model is available: ollama list")
        print("3. Pull model if needed: ollama pull llama3.1:latest")
        print("4. Test direct connection: curl http://localhost:11434/api/version")
