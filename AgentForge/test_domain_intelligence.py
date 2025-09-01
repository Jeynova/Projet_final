#!/usr/bin/env python3
"""
🔥 TEST REAL DOMAIN INTELLIGENCE
Testing if the LLM can actually detect domains properly
"""
import sys
sys.path.append('.')

from core.llm_client import LLMClient

def test_domain_detection():
    """Test real LLM domain detection"""
    print("🔥 TESTING REAL DOMAIN INTELLIGENCE")
    print("="*50)
    
    llm = LLMClient()
    
    test_cases = [
        "Create a modern blog platform with admin dashboard",
        "Build an online store with payment processing", 
        "Develop a real-time chat application with notifications",
        "Create a task management system for teams",
        "Build a high-performance API for data analytics"
    ]
    
    for prompt in test_cases:
        print(f"\n🎯 Prompt: {prompt}")
        
        domain_prompt = f"""Analyze this project request and classify it INTELLIGENTLY:
        
Request: "{prompt}"

Classify the project domain, complexity, and suggest optimal approach:
Return JSON:
{{
    "domain": "primary business domain (blog, ecommerce, social, task-mgmt, api, enterprise, chat, etc)",
    "complexity": "simple|moderate|complex", 
    "key_features": ["feature1", "feature2", "feature3"],
    "similar_projects": ["project_type1", "project_type2"],
    "recommended_approach": "brief strategy recommendation",
    "scale_expectations": "small|medium|large",
    "performance_needs": "low|medium|high"
}}

ANALYZE CAREFULLY - detect the TRUE domain from keywords:
- blog/cms/content/article → "blog"
- shop/store/ecommerce/payment → "ecommerce"  
- chat/message/real-time → "social"
- task/todo/project/team → "task-mgmt"
- api/data/analytics → "api"

Be SMART about domain classification!"""
        
        try:
            result = llm.extract_json(
                "You are a project analysis expert who detects domains intelligently.",
                domain_prompt
            )
            
            if result:
                domain = result.get('domain', 'unknown')
                complexity = result.get('complexity', 'unknown')
                features = result.get('key_features', [])
                
                print(f"   🎯 Domain: {domain}")
                print(f"   📊 Complexity: {complexity}")
                print(f"   🔥 Features: {features[:2]}...")
                
                # Check if it detected correctly
                expected_domains = {
                    'blog': ['blog', 'cms', 'content'],
                    'ecommerce': ['store', 'shop', 'payment'],
                    'social': ['chat', 'real-time', 'message'],
                    'task-mgmt': ['task', 'management', 'team'],
                    'api': ['api', 'data', 'analytics']
                }
                
                correct = False
                for expected_domain, keywords in expected_domains.items():
                    if any(keyword in prompt.lower() for keyword in keywords):
                        if domain == expected_domain:
                            correct = True
                            break
                
                print(f"   {'✅' if correct else '⚠️'} Detection: {'Correct' if correct else 'Needs improvement'}")
            else:
                print("   ❌ LLM returned no result")
                
        except Exception as e:
            print(f"   ❌ LLM call failed: {e}")

if __name__ == '__main__':
    test_domain_detection()
