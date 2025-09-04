#!/usr/bin/env python3
"""
🚀 DEPLOYMENT AGENT
Deployment strategy and configuration
"""

# ──────────────────────────────────────────────────────────────────────────────
#!/usr/bin/env python3
"""
🚀 DEPLOYMENT AGENT
Deployment strategy and configuration
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call


# TODO: Extract DeploymentAgent from phase2_pure_intelligence.py
# ──────────────────────────────────────────────────────────────────────────────
class DeploymentAgent(LLMBackedMixin):
    id = "deployment"
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        return 'deployment' not in state and 'tech_stack' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🚀 DeploymentAgent", "strategy")
        prompt = state.get('prompt',''); tech_stack = state.get('tech_stack',[]); complexity=state.get('complexity','moderate')
        sys_p = """Create a deployment plan consistent with the stack. Return STRICT JSON:
{"strategy":"...","containers":{"service":"..."},"environment":{"ENV":"value"},"scaling":"..."}"""
        user_p = f"Project: {prompt}\nTech Stack:\n" + "\n".join([f"- {t.get('role')}: {t.get('name')}" for t in tech_stack]) + f"\nComplexity: {complexity}"
        fallback = {"strategy":"Containers","containers":{"app":"main"},"environment":{"NODE_ENV":"production"},"scaling":"horizontal"}
        result = self.llm_json(sys_p, user_p, fallback)
        print("\n🚀 INTELLIGENT DEPLOYMENT:"); print(f"   📦 Strategy: {result.get('strategy','?')}")
        cont = result.get('containers',{}); 
        if cont: print(f"   🐳 Containers: {', '.join(list(cont.keys())[:2])}")
        return {'deployment': result}

