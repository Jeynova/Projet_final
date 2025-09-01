#!/usr/bin/env python3
"""
🔥 PHASE 2 REAL LLM TEST
Proving the intelligent system works with REAL LLM calls
"""
import sys
sys.path.append('.')

from agentforge_phase2 import AgentForgePhase2

def test_real_intelligent_selection():
    """Test with REAL LLM for different project types"""
    print("🔥 REAL LLM INTELLIGENT SELECTION TEST")
    print("="*60)
    
    forge = AgentForgePhase2()
    
    # Test case that should trigger BLOG domain intelligence  
    blog_prompt = "Create a professional blog platform with admin dashboard, comment system, and SEO"
    
    print(f"🎯 Testing: {blog_prompt}")
    print("🧠 This should trigger BLOG domain → React+TypeScript + FastAPI + PostgreSQL")
    print()
    
    try:
        result = forge.generate_project(blog_prompt)
        
        if result['success']:
            logs = result['logs']
            tech_stack = logs['chosen_tech']
            languages = logs['languages_used']
            
            print("🎯 INTELLIGENT RESULTS:")
            print(f"   🔧 Tech Stack:")
            for tech in tech_stack:
                name = tech.get('name', 'Unknown')
                lang = tech.get('language', '')
                role = tech.get('role', '')
                reason = tech.get('reason', '')
                print(f"      🔸 {name} ({lang}) - {role}")
                print(f"         💡 {reason}")
            
            print(f"\n   🌐 Languages Generated: {languages}")
            print(f"   📊 Tech Confidence: {logs['tech_confidence']:.1%}")
            print(f"   📄 Files Created: {len(logs['files_generated'])}")
            print(f"   ⭐ Final Score: {logs['final_score']:.1f}/10")
            
            # Check if it made intelligent choices
            has_react = any('React' in t.get('name', '') for t in tech_stack)
            has_typescript = any('TypeScript' in t.get('language', '') for t in tech_stack)
            has_database = any(t.get('role') == 'database' for t in tech_stack)
            has_cache = any(t.get('role') == 'cache' for t in tech_stack)
            
            print(f"\n🧠 INTELLIGENCE CHECK:")
            print(f"   ✅ Modern Frontend (React): {has_react}")
            print(f"   ✅ Type Safety (TypeScript): {has_typescript}")
            print(f"   ✅ Database: {has_database}")
            print(f"   ✅ Performance (Cache): {has_cache}")
            
            intelligence_score = sum([has_react, has_typescript, has_database, has_cache])
            print(f"   🎯 Intelligence Score: {intelligence_score}/4")
            
            if intelligence_score >= 3:
                print("\n🚀 SUCCESS: System made INTELLIGENT tech choices!")
            else:
                print("\n⚠️ WARNING: System may need more intelligence tuning")
                
        else:
            print("❌ Project generation failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_different_domains():
    """Test intelligence across different project domains"""
    print("\n🧪 TESTING DOMAIN INTELLIGENCE")
    print("="*40)
    
    forge = AgentForgePhase2()
    
    test_cases = [
        ("Simple API", "Create a REST API for user management"),
        ("Ecommerce", "Build an online store with payment processing"),
        ("Real-time", "Create a live chat application with notifications")
    ]
    
    for name, prompt in test_cases:
        print(f"\n🎯 {name}: {prompt}")
        try:
            result = forge.generate_project(prompt)
            if result['success']:
                tech_names = [t.get('name') for t in result['logs']['chosen_tech']]
                print(f"   🔧 Chose: {tech_names}")
            else:
                print(f"   ❌ Failed")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == '__main__':
    test_real_intelligent_selection()
    test_different_domains()
    
    print("\n🎯 PHASE 2 REAL TESTING COMPLETE!")
    print("🚀 Your vision: LLM-first development with intelligent agent assistance!")
