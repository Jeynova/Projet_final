# optimized_team_debate.py  
from typing import Dict, Any, List
from core.llm_client import LLMClient

class OptimizedTeamDebate:
    """
    Optimized team debate that uses different models for different roles
    and reduces unnecessary parallel calls to the same model
    """
    
    def __init__(self):
        # Assign different models to different roles for diversity
        self.role_models = {
            "PM": "mistral:7b",           # Good for reasoning and planning
            "DEV": "codellama:7b",        # Best for technical decisions  
            "PO": "llama3.1:8b",         # Good for user-focused thinking
            "CONSULTANT": "qwen2.5-coder:7b",  # Good for best practices
            "ARCHITECT": "mistral:7b"     # Good for system design
        }
        
        self.role_prompts = {
            "PM": "You are a Project Manager focused on timeline, feasibility, and risk management.",
            "DEV": "You are a Lead Developer focused on implementation complexity, maintainability, and performance.",
            "PO": "You are a Product Owner focused on user experience, features, and business value.",
            "CONSULTANT": "You are a Technology Consultant focused on industry best practices and proven architectures.",
            "ARCHITECT": "You are a System Architect focused on scalability, security, and integration patterns."
        }

    def run_smart_debate(self, prompt: str, context: str) -> Dict[str, Any]:
        """
        Run optimized debate with different models for different perspectives
        """
        print("🎭 Starting optimized team debate with specialized models...")
        
        proposals = {}
        
        # Sequential calls with different models (more efficient than 5 parallel calls to same model)
        for role, model in self.role_models.items():
            print(f"🗣️ {role} ({model}) analyzing...")
            
            try:
                client = LLMClient(preferred_model=model)
                system_prompt = self.role_prompts[role]
                
                user_prompt = f"""Project: {prompt}

Context: {context}

As a {role}, propose a concrete technology stack and justify your choices:

Return JSON format:
{{
  "stack": {{
    "backend": "technology choice",
    "frontend": "technology choice", 
    "database": "technology choice",
    "deployment": "technology choice"
  }},
  "reasoning": {{
    "backend": "why this choice",
    "frontend": "why this choice",
    "database": "why this choice", 
    "deployment": "why this choice"
  }},
  "priority_concerns": ["concern1", "concern2", "concern3"]
}}"""

                result = client.extract_json(system_prompt, user_prompt)
                proposals[role] = result or {}
                
            except Exception as e:
                print(f"❌ {role} failed: {e}")
                proposals[role] = {"error": str(e)}
                
        # Moderate with the best reasoning model
        print("⚖️ Moderating with specialized reasoning model...")
        
        try:
            moderator_client = LLMClient(preferred_model="mistral:7b")
            
            moderation_prompt = f"""You are a neutral technical moderator. 

Project: {prompt}
Context: {context}

Team proposals:
{proposals}

Synthesize into ONE optimal stack considering all perspectives.

Return JSON:
{{
  "backend": {{"name": "chosen tech", "reasoning": "why chosen"}},
  "frontend": {{"name": "chosen tech", "reasoning": "why chosen"}}, 
  "database": {{"name": "chosen tech", "reasoning": "why chosen"}},
  "deployment": {{"name": "chosen tech", "reasoning": "why chosen"}},
  "team_consensus": "brief summary of decision process"
}}"""

            final_decision = moderator_client.extract_json(
                "You are an expert technical moderator focused on optimal technology selection.",
                moderation_prompt
            ) or {}
            
        except Exception as e:
            print(f"❌ Moderation failed: {e}")
            # Fallback decision
            final_decision = {
                "backend": {"name": "Node.js", "reasoning": "Popular and well-supported"},
                "frontend": {"name": "React", "reasoning": "Modern component-based architecture"},
                "database": {"name": "PostgreSQL", "reasoning": "Robust relational database"},
                "deployment": {"name": "Docker", "reasoning": "Containerization standard"},
                "team_consensus": "Fallback decision due to debate error"
            }
        
        return {
            "proposals": proposals,
            "final_decision": final_decision,
            "process": "optimized_multi_model_debate"
        }

# Factory function for backward compatibility
def run_optimized_debate(llm_client, prompt: str, context: str) -> Dict[str, Any]:
    """Optimized debate with intelligent model allocation"""
    debate = OptimizedTeamDebate()
    return debate.run_smart_debate(prompt, context)
