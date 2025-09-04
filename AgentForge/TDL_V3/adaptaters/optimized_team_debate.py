# optimized_team_debate.py  
from typing import Dict, Any, List
from core.llm_client import LLMClient

class OptimizedTeamDebate:
    """
    Optimized team debate that uses different models for different roles
    and reduces unnecessary parallel calls to the same model
    """
    
    def __init__(self, demo_mode=False):
        """
        Initialize optimized team debate
        demo_mode: Use single LLM call for faster demo processing
        """
        self.demo_mode = demo_mode
        
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
        Run optimized debate with different models or demo mode
        """
        if self.demo_mode:
            return self._run_demo_mode(prompt, context)
        
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
    
    def _run_demo_mode(self, prompt: str, context: str) -> Dict[str, Any]:
        """Fast demo mode with single LLM call simulating entire team"""
        print("🎭 DEMO MODE: Simulation accélérée de l'équipe technique")
        
        try:
            client = LLMClient()
            demo_prompt = f"""SIMULATION ÉQUIPE TECHNIQUE COMPLÈTE

PROJET: {prompt}
CONTEXTE: {context}

Simule les 5 rôles suivants et leurs recommandations de stack:

1. PROJECT MANAGER: Focus timeline, budget, risques
2. LEAD DEVELOPER: Focus implémentation, maintenabilité, performance
3. PRODUCT OWNER: Focus UX, fonctionnalités, business value  
4. TECH CONSULTANT: Focus best practices, architectures éprouvées
5. SYSTEM ARCHITECT: Focus scalabilité, sécurité, intégration

Retourne le consensus final en JSON:
{{
  "backend": {{"name": "technologie choisie", "reasoning": "justification détaillée"}},
  "frontend": {{"name": "technologie choisie", "reasoning": "justification détaillée"}},
  "database": {{"name": "technologie choisie", "reasoning": "justification détaillée"}}, 
  "deployment": {{"name": "technologie choisie", "reasoning": "justification détaillée"}},
  "team_consensus": "synthèse des points clés et compromis de l'équipe"
}}"""

            result = client.extract_json(
                "Tu es une équipe technique complète avec expertise variée",
                demo_prompt
            )
            
            if result:
                return {
                    "proposals": {"DEMO_TEAM": result},
                    "final_decision": result,
                    "process": "demo_mode_simulation"
                }
        
        except Exception as e:
            print(f"❌ Demo mode failed: {e}")
        
        # Fallback
        return {
            "proposals": {},
            "final_decision": {
                "backend": {"name": "Node.js", "reasoning": "Stack moderne et populaire"},
                "frontend": {"name": "React", "reasoning": "Interface utilisateur moderne"},
                "database": {"name": "PostgreSQL", "reasoning": "Base de données robuste"},
                "deployment": {"name": "Docker", "reasoning": "Containerisation standard"},
                "team_consensus": "Configuration par défaut - demo mode"
            },
            "process": "demo_mode_fallback"
        }

# Factory function for backward compatibility
def run_optimized_debate(llm_client, prompt: str, context: str) -> Dict[str, Any]:
    """Optimized debate with intelligent model allocation"""
    debate = OptimizedTeamDebate()
    return debate.run_smart_debate(prompt, context)
