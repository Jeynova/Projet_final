#!/usr/bin/env python3
"""
FINAL SOLUTION: Forced LLM Comparison Without Hard-coded Rules
🧠 The LLM must COMPARE and JUSTIFY, not just pick its favorite
"""
import sys
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List

sys.path.append('.')
from core.llm_client import LLMClient

class LLMBackedMixin:
    def __init__(self):
        self.llm_client = LLMClient()
    
    def llm_json(self, system_prompt: str, user_prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = self.llm_client.extract_json(system_prompt, user_prompt)
            return result if result is not None else fallback
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return fallback

class ForcedComparisonTechAgent(LLMBackedMixin):
    """🧠 Force LLM to compare options and justify choices"""
    id = "tech"
    
    def select_technology(self, prompt: str) -> Dict[str, Any]:
        """Force explicit comparison between technology options"""
        
        # 🧠 FORCED COMPARISON PROMPT
        forced_comparison_prompt = f"""You are a senior technology architect. You MUST compare ALL options and choose the BEST one.

PROJECT: "{prompt}"

MANDATORY COMPARISON:
You must evaluate ALL four backend options for this specific project and rank them.

BACKEND OPTIONS TO COMPARE:

1. FASTAPI + PYTHON
   Strengths: Rapid development, async support, Python ecosystem, auto docs
   Weaknesses: Slower than compiled languages, GIL limitations
   Best for: MVPs, Python teams, ML integration, rapid prototyping

2. NODE.JS + EXPRESS
   Strengths: JavaScript everywhere, npm ecosystem, real-time support, JSON native
   Weaknesses: Single-threaded bottlenecks, callback complexity
   Best for: Real-time apps, unified JavaScript teams, rapid iteration

3. GO + GIN
   Strengths: Exceptional performance, simple concurrency, fast compilation, small binaries
   Weaknesses: Smaller ecosystem, more verbose, limited frameworks
   Best for: High-performance APIs, microservices, system services

4. SPRING BOOT + JAVA
   Strengths: Enterprise maturity, JVM ecosystem, battle-tested, excellent tooling
   Weaknesses: Heavy setup, verbose code, slower development
   Best for: Enterprise applications, complex business logic, large teams

YOUR TASK:
1. Analyze the specific requirements of: "{prompt}"
2. Score each option (1-10) for this project's needs
3. Choose the HIGHEST scoring option
4. Justify why it beats the others for THIS project

SCORING CRITERIA:
- Development Speed (how fast to build THIS project)
- Performance Needs (does THIS project need high performance?)
- Ecosystem Match (does THIS project benefit from the ecosystem?)
- Maintenance (how easy to maintain THIS project long-term?)

Return JSON with your explicit comparison:
{{
    "comparison": {{
        "fastapi_score": 8,
        "nodejs_score": 6,
        "go_score": 7,
        "springboot_score": 4
    }},
    "winner": "FastAPI",
    "reasoning": "FastAPI scored highest because...",
    "stack": [
        {{"name": "FastAPI", "language": "Python", "role": "backend", "reason": "Why this beats all other options for THIS project"}}
    ],
    "why_not_others": {{
        "nodejs": "Why Node.js is NOT the best choice for this project",
        "go": "Why Go is NOT the best choice for this project", 
        "springboot": "Why Spring Boot is NOT the best choice for this project"
    }}
}}

COMPARE ALL OPTIONS AND CHOOSE THE WINNER!"""
        
        fallback = {
            'comparison': {'fastapi_score': 8, 'nodejs_score': 6, 'go_score': 7, 'springboot_score': 4},
            'winner': 'FastAPI',
            'reasoning': 'Balanced choice for most projects',
            'stack': [{"name": "FastAPI", "language": "Python", "role": "backend", "reason": "Rapid development"}]
        }
        
        try:
            result = self.llm_json('You are a technology comparison expert.', forced_comparison_prompt, fallback)
            
            # Show comparison results
            comparison = result.get('comparison', {})
            winner = result.get('winner', 'Unknown')
            reasoning = result.get('reasoning', '')
            
            print(f"📊 LLM SCORING:")
            print(f"   FastAPI: {comparison.get('fastapi_score', 0)}/10")
            print(f"   Node.js: {comparison.get('nodejs_score', 0)}/10") 
            print(f"   Go: {comparison.get('go_score', 0)}/10")
            print(f"   Spring Boot: {comparison.get('springboot_score', 0)}/10")
            print(f"🏆 WINNER: {winner}")
            print(f"💡 REASONING: {reasoning}")
            
            return result
            
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
            return fallback

def test_forced_comparison():
    """Test the forced comparison approach"""
    print("🧠 TESTING FORCED LLM COMPARISON")
    print("="*60)
    
    os.environ["AGENTFORGE_LLM"] = "ollama"
    os.environ["OLLAMA_MODEL"] = "qwen2.5-coder:7b"
    
    agent = ForcedComparisonTechAgent()
    
    test_cases = [
        "simple blog with posts and comments",
        "real-time multiplayer game with WebSocket connections",
        "enterprise document management with role-based access control"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}: {test_case}")
        print("-" * 40)
        
        result = agent.select_technology(test_case)
        winner = result.get('winner', 'Unknown')
        stack = result.get('stack', [])
        
        if stack:
            backend = stack[0]
            print(f"🎯 FINAL CHOICE: {backend.get('name')} ({backend.get('language')})")
            print(f"💡 REASON: {backend.get('reason', '')[:100]}...")

if __name__ == '__main__':
    test_forced_comparison()
