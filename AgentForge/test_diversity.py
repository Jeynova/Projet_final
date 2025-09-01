#!/usr/bin/env python3
"""
🎯 FINAL TEST: Phase 2 with Diverse Tech Selection
Test if improved prompts lead to diverse tech choices
"""
import sys
import os
sys.path.append('.')

# Set environment for real LLM
os.environ["AGENTFORGE_LLM"] = "ollama"
os.environ["OLLAMA_MODEL"] = "qwen2.5-coder:7b"

from agentforge_phase2 import AgentForgePhase2

def test_diverse_projects():
    """Test Phase 2 with projects that should get DIFFERENT tech stacks"""
    print("🎯 TESTING DIVERSE TECH SELECTION")
    print("="*60)
    
    projects = [
        {
            'name': 'Enterprise Document System',
            'prompt': 'enterprise document management system with role-based access control and audit trails',
            'expected': 'Java Spring Boot'
        },
        {
            'name': 'High-Performance Analytics',
            'prompt': 'high-performance data analytics API processing millions of requests per second',
            'expected': 'Go + Gin'
        },
        {
            'name': 'Real-Time Chat',
            'prompt': 'real-time chat application with WebSocket support and instant messaging',
            'expected': 'Node.js + Socket.io'
        },
        {
            'name': 'Simple Blog API',
            'prompt': 'simple blog API with posts and comments',
            'expected': 'FastAPI + Python'
        }
    ]
    
    forge = AgentForgePhase2()
    
    for i, project in enumerate(projects, 1):
        print(f"\n🚀 PROJECT {i}: {project['name']}")
        print(f"   📝 Prompt: {project['prompt']}")
        print(f"   🎯 Expected: {project['expected']}")
        print("-" * 50)
        
        try:
            result = forge.generate_project(project['prompt'])
            
            # Extract tech stack from result
            tech_stack = result.get('tech', {}).get('stack', [])
            
            backend_techs = [t for t in tech_stack if t.get('role') == 'backend']
            
            if backend_techs:
                backend = backend_techs[0]
                backend_name = backend.get('name', 'Unknown')
                backend_lang = backend.get('language', 'Unknown')
                backend_reason = backend.get('reason', '')
                
                print(f"   ✅ Chosen: {backend_name} ({backend_lang})")
                print(f"   💡 Reason: {backend_reason[:100]}...")
                
                # Analyze if choice is appropriate
                if 'enterprise' in project['name'].lower() and 'java' in backend_lang.lower():
                    print(f"   🎉 PERFECT: Java for enterprise! ✓")
                elif 'performance' in project['name'].lower() and 'go' in backend_lang.lower():
                    print(f"   🎉 PERFECT: Go for performance! ✓")
                elif 'chat' in project['name'].lower() and ('node' in backend_name.lower() or 'javascript' in backend_lang.lower()):
                    print(f"   🎉 PERFECT: Node.js for real-time! ✓")
                elif 'blog' in project['name'].lower() and ('fastapi' in backend_name.lower() or 'python' in backend_lang.lower()):
                    print(f"   🎉 PERFECT: FastAPI for simple blog! ✓")
                else:
                    print(f"   🤔 Unexpected choice: {backend_name} ({backend_lang})")
                    print(f"      Expected: {project['expected']}")
                
            else:
                print("   ❌ No backend technology found in result")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🏆 DIVERSITY TEST COMPLETE!")
    print("Does each project get a DIFFERENT optimal technology? 🤔")

if __name__ == '__main__':
    test_diverse_projects()
