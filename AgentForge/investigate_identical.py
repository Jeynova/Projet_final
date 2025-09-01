#!/usr/bin/env python3
"""
🔍 INVESTIGATE LLM IDENTICAL RESPONSES
Why is qwen giving the same tech stack for different projects?
"""
import sys
import os
sys.path.append('.')

from core.llm_client import LLMClient

def test_llm_variation():
    """Test if LLM gives different responses to different prompts"""
    print("🔍 TESTING LLM RESPONSE VARIATION")
    print("="*50)
    
    # Set environment
    os.environ["AGENTFORGE_LLM"] = "ollama"
    os.environ["OLLAMA_MODEL"] = "qwen2.5-coder:7b"
    
    llm = LLMClient()
    
    # Test completely different project types
    test_cases = [
        {
            'name': 'Simple API',
            'prompt': 'Create a simple REST API for user management with just backend, no frontend needed'
        },
        {
            'name': 'Chat App',  
            'prompt': 'Build a real-time chat application that needs WebSocket support and instant messaging'
        },
        {
            'name': 'Data Analytics',
            'prompt': 'Create a high-performance data analytics API that processes millions of records'
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 {test['name']}")
        print(f"   📝 Prompt: {test['prompt']}")
        
        # Use same system prompt as TechSelectAgent
        tech_prompt = f"""You are THE TECH SELECTION GENIUS. Choose the OPTIMAL tech stack:

Project: "{test['prompt']}"
Domain: api
Complexity: moderate
Performance Needs: medium

🎯 INTELLIGENCE RULES (choose the BEST fit):

📱 FRONTEND: Only if UI needed!
- API-only projects → NO FRONTEND
- Chat apps → React + TypeScript  
- Analytics → Optional dashboard

🖥️ BACKEND:
- Simple API → FastAPI + Python
- Real-time chat → Node.js + Socket.io
- High-performance → Go + Gin
- Analytics → Python + FastAPI OR Go

💾 DATABASE:
- Simple API → PostgreSQL or SQLite
- Chat → MongoDB (flexible) + Redis
- Analytics → PostgreSQL + Redis

Return JSON:
{{
    "stack": [
        {{"name": "FastAPI", "language": "Python", "role": "backend", "reason": "Perfect for {test['name']}"}}
    ],
    "reasoning": "Specific reasoning for {test['name']} requirements",
    "confidence": 0.95
}}

CHOOSE DIFFERENT STACKS FOR DIFFERENT PROJECTS!"""
        
        try:
            result = llm.extract_json("You are a tech selection expert.", tech_prompt)
            
            if result:
                stack = result.get('stack', [])
                reasoning = result.get('reasoning', '')
                
                print(f"   🔧 Chosen stack:")
                for tech in stack:
                    name = tech.get('name', 'Unknown')
                    role = tech.get('role', 'Unknown')
                    print(f"      - {name} ({role})")
                
                print(f"   💡 Reasoning: {reasoning[:100]}...")
                
                # Check if no frontend for API
                has_frontend = any(t.get('role') == 'frontend' for t in stack)
                print(f"   🖥️ Has Frontend: {has_frontend}")
                
            else:
                print("   ❌ No result from LLM")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🎯 ANALYSIS:")
    print("If all results are identical, the LLM prompt needs improvement!")

if __name__ == '__main__':
    test_llm_variation()
