#!/usr/bin/env python3
"""
🎭 MULTI-PERSPECTIVE LLM INTELLIGENCE
Let the LLM wear multiple hats and decide naturally!

Your vision: LLM as Lead PM + Developer + Product Owner + Consultant + End User
NO hard-coded tech options - pure organic intelligence!
"""
import sys
import os
sys.path.append('.')

from core.llm_client import LLMClient

def test_multi_perspective_intelligence():
    """Test LLM thinking from multiple perspectives naturally"""
    print("🎭 TESTING MULTI-PERSPECTIVE LLM INTELLIGENCE")
    print("="*60)
    
    os.environ["AGENTFORGE_LLM"] = "ollama"
    os.environ["OLLAMA_MODEL"] = "qwen2.5-coder:7b"
    
    llm = LLMClient()
    
    test_projects = [
        "simple blog with posts and comments",
        "real-time chat application with instant messaging", 
        "enterprise document management system",
        "high-performance analytics dashboard"
    ]
    
    for i, project in enumerate(test_projects, 1):
        print(f"\n🎭 PROJECT {i}: {project}")
        print("-" * 50)
        
        # 🎭 MULTI-PERSPECTIVE ORGANIC PROMPT
        organic_prompt = f"""You are a technology decision-making team. Think from multiple perspectives about this project:

PROJECT: "{project}"

🎭 WEAR THESE HATS AND THINK NATURALLY:

👔 LEAD PROJECT MANAGER perspective:
- What are the timeline constraints and budget considerations?
- What risks need to be mitigated?
- What team skills and resources are available?

💻 LEAD DEVELOPER perspective:  
- What technical challenges will we face?
- What technologies would make development efficient?
- What long-term maintenance concerns exist?

📋 PRODUCT OWNER perspective:
- What user experience is most important?
- What business value needs to be delivered?
- What scalability requirements exist?

🎯 CONSULTANT perspective:
- What industry best practices apply?
- What technologies have proven success for similar projects?
- What architectural patterns would be most suitable?

👤 END USER perspective:
- What performance and reliability do users expect?
- What features matter most for user satisfaction?
- What accessibility and usability concerns exist?

THINK ORGANICALLY from these perspectives and naturally arrive at technology choices.
Don't pick from a menu - think about what technologies would emerge from this analysis.

Consider any technologies that make sense:
- Any frontend framework or approach
- Any backend language/framework  
- Any database system
- Any deployment approach
- Any additional tools or services

Think freely and arrive at your natural conclusion.

Return JSON with your organic analysis:
{{
    "perspectives_analysis": {{
        "project_manager": "PM concerns and requirements",
        "developer": "Technical challenges and preferences", 
        "product_owner": "Business and user value requirements",
        "consultant": "Industry best practices and recommendations",
        "end_user": "User experience and performance expectations"
    }},
    "natural_tech_conclusion": {{
        "frontend": {{"technology": "React|Vue|Angular|etc", "reasoning": "Why this emerged from the analysis"}},
        "backend": {{"technology": "FastAPI|Node.js|Go|Java|etc", "reasoning": "Why this emerged from the analysis"}},
        "database": {{"technology": "PostgreSQL|MongoDB|etc", "reasoning": "Why this emerged from the analysis"}}
    }},
    "decision_rationale": "How all perspectives converged on this technology choice",
    "confidence": 0.85
}}

THINK ORGANICALLY - LET THE TECHNOLOGY CHOICES EMERGE NATURALLY!"""
        
        try:
            result = llm.extract_json("You are a multi-perspective technology decision team.", organic_prompt)
            
            if result:
                perspectives = result.get('perspectives_analysis', {})
                tech_conclusion = result.get('natural_tech_conclusion', {})
                rationale = result.get('decision_rationale', '')
                confidence = result.get('confidence', 0)
                
                print(f"🎭 MULTI-PERSPECTIVE ANALYSIS:")
                print(f"   👔 PM: {perspectives.get('project_manager', '')[:60]}...")
                print(f"   💻 DEV: {perspectives.get('developer', '')[:60]}...")
                print(f"   📋 PO: {perspectives.get('product_owner', '')[:60]}...")
                
                print(f"\n🧠 NATURAL TECHNOLOGY EMERGENCE:")
                frontend = tech_conclusion.get('frontend', {})
                backend = tech_conclusion.get('backend', {})
                database = tech_conclusion.get('database', {})
                
                print(f"   🎨 Frontend: {frontend.get('technology', 'None')}")
                print(f"      💡 {frontend.get('reasoning', '')[:80]}...")
                print(f"   🔧 Backend: {backend.get('technology', 'None')}")  
                print(f"      💡 {backend.get('reasoning', '')[:80]}...")
                print(f"   🗄️ Database: {database.get('technology', 'None')}")
                print(f"      💡 {database.get('reasoning', '')[:80]}...")
                
                print(f"\n🎯 CONVERGENCE: {rationale[:100]}...")
                print(f"🧠 CONFIDENCE: {confidence:.1%}")
                
            else:
                print("❌ No result from LLM")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_multi_perspective_intelligence()
