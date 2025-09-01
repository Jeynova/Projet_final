#!/usr/bin/env python3
"""
🔍 INVESTIGATE LLM BIAS
Why does qwen2.5-coder:7b always choose Go?
Let's force it to compare options explicitly!
"""
import sys
import os
sys.path.append('.')

from core.llm_client import LLMClient

def test_llm_comparison():
    """Force LLM to explicitly compare technologies"""
    print("🔍 INVESTIGATING LLM TECH BIAS")
    print("="*50)
    
    os.environ["AGENTFORGE_LLM"] = "ollama"
    os.environ["OLLAMA_MODEL"] = "qwen2.5-coder:7b"
    
    llm = LLMClient()
    
    # Force explicit comparison
    comparison_prompt = """You are a technology consultant. Compare these backend options for a SIMPLE BLOG:

PROJECT: Simple blog with posts and comments (basic CRUD operations)

COMPARE THESE OPTIONS:

OPTION A: FastAPI + Python
- Pros: Rapid development, easy to learn, great for MVPs
- Cons: Slower than compiled languages
- Best for: Quick prototypes, ML integration, simple APIs

OPTION B: Node.js + Express  
- Pros: JavaScript everywhere, huge npm ecosystem, good for real-time
- Cons: Single-threaded limitations for CPU-intensive tasks
- Best for: Real-time apps, unified JavaScript stack, rapid iteration

OPTION C: Go + Gin
- Pros: Exceptional performance, simple deployment, great concurrency
- Cons: Smaller ecosystem, more verbose syntax
- Best for: High-performance APIs, microservices, system programming

OPTION D: Spring Boot + Java
- Pros: Enterprise-grade, mature ecosystem, JVM performance
- Cons: Heavy setup, verbose, slower development
- Best for: Enterprise applications, complex business logic

FOR A SIMPLE BLOG (just posts and comments), which is MOST appropriate?
Consider development speed vs performance trade-offs.

Return JSON:
{
    "choice": "FastAPI|Node.js|Go|Spring Boot",
    "reasoning": "Why this choice is most appropriate for a SIMPLE blog",
    "comparison": "How you weighed the pros/cons for this specific use case"
}

Choose the most PRACTICAL option for a simple blog!"""
    
    try:
        result = llm.extract_json("You are a practical technology consultant.", comparison_prompt)
        
        if result:
            choice = result.get('choice', 'Unknown')
            reasoning = result.get('reasoning', '')
            comparison = result.get('comparison', '')
            
            print(f"🎯 LLM CHOICE: {choice}")
            print(f"💡 REASONING: {reasoning}")
            print(f"⚖️ COMPARISON: {comparison}")
            
            if choice == 'FastAPI':
                print("✅ GOOD: Chose FastAPI for simple blog (rapid development)")
            elif choice == 'Go':
                print("🤔 INTERESTING: Chose Go for simple blog (performance over simplicity)")
            elif choice == 'Node.js':
                print("✅ GOOD: Chose Node.js for simple blog (JavaScript ecosystem)")
            elif choice == 'Spring Boot':
                print("🤔 HEAVY: Chose Spring Boot for simple blog (overkill?)")
        else:
            print("❌ No result from LLM")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_specific_scenarios():
    """Test very specific scenarios that should force different choices"""
    print("\n🎯 TESTING SPECIFIC SCENARIOS")
    print("="*50)
    
    llm = LLMClient()
    
    scenarios = [
        {
            'name': 'Microservice API Only',
            'prompt': 'Create ONLY a REST API microservice. No frontend needed. Just JSON endpoints.',
            'hint': 'API-only should prefer FastAPI or Go'
        },
        {
            'name': 'Real-time Game Backend',
            'prompt': 'Real-time multiplayer game backend with WebSocket connections and low latency',
            'hint': 'Real-time games need Node.js or Go with WebSocket'
        },
        {
            'name': 'Enterprise Web Portal',
            'prompt': 'Enterprise web portal with complex business logic, reporting, and user management',
            'hint': 'Enterprise typically needs Java Spring Boot'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🧪 {scenario['name']}")
        print(f"   📝 {scenario['prompt']}")
        
        direct_prompt = f"""Choose the backend technology for: "{scenario['prompt']}"

You MUST choose from exactly these options:
1. FastAPI + Python
2. Node.js + Express
3. Go + Gin
4. Spring Boot + Java

Which ONE is most appropriate? Be decisive!

Return JSON:
{{
    "choice": "FastAPI|Node.js|Go|Spring Boot",
    "reason": "One sentence why"
}}"""
        
        try:
            result = llm.extract_json("Be decisive in your technology choice.", direct_prompt)
            if result:
                choice = result.get('choice', 'Unknown')
                reason = result.get('reason', '')
                print(f"   🎯 CHOSE: {choice}")
                print(f"   💡 BECAUSE: {reason}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == '__main__':
    test_llm_comparison()
    test_specific_scenarios()
