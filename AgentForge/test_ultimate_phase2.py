#!/usr/bin/env python3
"""
🔥 ULTIMATE PHASE 2 TEST
Test different domains to see REAL intelligent tech selection
"""
import sys
import os
sys.path.append('.')

from agentforge_phase2 import AgentForgePhase2

def test_ultimate_intelligence():
    """Test truly different tech stacks for different domains"""
    print("🔥 ULTIMATE PHASE 2 INTELLIGENCE TEST")
    print("="*60)
    
    # Set environment for real LLM
    os.environ["AGENTFORGE_LLM"] = "ollama"
    os.environ["OLLAMA_MODEL"] = "qwen2.5-coder:7b"
    
    forge = AgentForgePhase2()
    
    test_cases = [
        {
            'name': 'Enterprise Java',
            'prompt': 'Create an enterprise document management system with role-based access and audit trails',
            'expected_backend': 'Java'
        },
        {
            'name': 'High Performance Go',
            'prompt': 'Build a high-performance API for real-time data analytics with millions of requests',
            'expected_backend': 'Go'
        },
        {
            'name': 'PHP CMS',
            'prompt': 'Create a content management system with Symfony framework for a publishing company',
            'expected_backend': 'PHP'
        }
    ]
    
    for test in test_cases:
        print(f"\n🎯 {test['name']}: {test['prompt']}")
        print(f"   🎯 Expected: Should choose {test['expected_backend']} backend")
        
        try:
            result = forge.generate_project(test['prompt'])
            
            if result['success']:
                chosen_stack = result['logs']['chosen_tech']
                backend_techs = [t for t in chosen_stack if t.get('role') == 'backend']
                
                if backend_techs:
                    chosen_backend = backend_techs[0].get('language', 'Unknown')
                    backend_name = backend_techs[0].get('name', 'Unknown')
                    confidence = result['logs']['tech_confidence']
                    
                    print(f"   ✅ Chose: {backend_name} ({chosen_backend})")
                    print(f"   📊 Confidence: {confidence:.1%}")
                    
                    # Check if it made intelligent choice
                    expected = test['expected_backend'].lower()
                    if expected in chosen_backend.lower() or expected in backend_name.lower():
                        print(f"   🚀 PERFECT: Chose {expected} as expected!")
                    else:
                        print(f"   🤔 Different choice: {chosen_backend} instead of {expected}")
                        print(f"      💡 Reason: {backend_techs[0].get('reason', 'No reason')}")
                else:
                    print(f"   ❌ No backend tech found")
            else:
                print(f"   ❌ Generation failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("-" * 50)
    
    print("\n🎯 INTELLIGENCE ANALYSIS COMPLETE!")

if __name__ == '__main__':
    test_ultimate_intelligence()
