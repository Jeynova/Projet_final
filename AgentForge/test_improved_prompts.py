#!/usr/bin/env python3
"""
🔥 IMPROVED LLM PROMPTS
Test better prompts that force diverse tech choices
"""
import sys
import os
sys.path.append('.')

from core.llm_client import LLMClient

def test_improved_prompts():
    """Test improved prompts for diverse tech selection"""
    print("🔥 TESTING IMPROVED TECH SELECTION PROMPTS")
    print("="*60)
    
    os.environ["AGENTFORGE_LLM"] = "ollama"
    os.environ["OLLAMA_MODEL"] = "qwen2.5-coder:7b"
    
    llm = LLMClient()
    
    test_cases = [
        {
            'name': 'Enterprise Java',
            'prompt': 'enterprise document management system with role-based access',
            'hint': 'Enterprise systems typically use Java Spring Boot for reliability'
        },
        {
            'name': 'High Performance Go',
            'prompt': 'high-performance data analytics API processing millions of requests per second',
            'hint': 'High-performance APIs often use Go for speed and concurrency'
        },
        {
            'name': 'Real-time Node.js',
            'prompt': 'real-time chat application with WebSocket support and instant messaging',
            'hint': 'Real-time apps typically use Node.js for native WebSocket support'
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 {test['name']}")
        print(f"   📝 {test['prompt']}")
        print(f"   💡 Hint: {test['hint']}")
        
        # IMPROVED PROMPT with specific guidance
        improved_prompt = f"""You are a senior tech architect. Choose the OPTIMAL backend technology for this specific project:

PROJECT: "{test['prompt']}"

CRITICAL SELECTION RULES:
🏢 ENTERPRISE projects → Java + Spring Boot (reliability, enterprise features)
⚡ HIGH-PERFORMANCE projects → Go + Gin (speed, concurrency, millions of requests)  
💬 REAL-TIME CHAT projects → Node.js + Socket.io (native WebSocket support)
📊 DATA ANALYTICS → Python + FastAPI OR Go (depending on performance needs)
🚀 SIMPLE APIs → FastAPI + Python (rapid development)

GUIDANCE: {test['hint']}

Choose the BEST backend technology for THIS specific project.
DON'T default to FastAPI - choose what's ACTUALLY optimal!

Return JSON:
{{
    "backend": {{
        "name": "Go",
        "language": "Go", 
        "framework": "Gin",
        "reason": "Specific reason why THIS technology is perfect for THIS project"
    }},
    "database": "PostgreSQL|MongoDB|Redis",
    "reasoning": "Detailed explanation of why this choice is optimal for the project requirements"
}}

CHOOSE THE RIGHT TOOL FOR THE JOB!"""
        
        try:
            result = llm.extract_json("You are a tech selection expert who chooses the RIGHT technology for each project.", improved_prompt)
            
            if result:
                backend = result.get('backend', {})
                database = result.get('database', 'Unknown')
                reasoning = result.get('reasoning', '')
                
                backend_name = backend.get('name', 'Unknown')
                backend_lang = backend.get('language', 'Unknown') 
                framework = backend.get('framework', '')
                
                print(f"   ✅ Backend: {backend_name} ({backend_lang}) {framework}")
                print(f"   🗄️ Database: {database}")
                print(f"   💡 Reason: {backend.get('reason', '')[:80]}...")
                print(f"   🧠 Full reasoning: {reasoning[:100]}...")
                
                # Check if choice makes sense
                expected_tech = test['name'].split()[0].lower()  # 'enterprise', 'high', 'real-time'
                
                if 'enterprise' in test['name'].lower() and 'java' in backend_lang.lower():
                    print(f"   🚀 PERFECT: Chose Java for enterprise!")
                elif 'performance' in test['name'].lower() and 'go' in backend_lang.lower():
                    print(f"   🚀 PERFECT: Chose Go for performance!")
                elif 'real-time' in test['name'].lower() and ('node' in backend_name.lower() or 'javascript' in backend_lang.lower()):
                    print(f"   🚀 PERFECT: Chose Node.js for real-time!")
                else:
                    print(f"   🤔 Choice: {backend_name} - let's see if reasoning makes sense")
                    
            else:
                print("   ❌ No result from LLM")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🎯 IMPROVED PROMPT ANALYSIS COMPLETE!")

if __name__ == '__main__':
    test_improved_prompts()
