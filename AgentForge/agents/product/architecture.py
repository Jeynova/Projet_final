#!/usr/bin/env python3
"""
🏗️ ARCHITECTURE AGENT
Intelligent architecture design
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call


# ──────────────────────────────────────────────────────────────────────────────
# 🏗️ ARCHITECTURE AGENT
# ──────────────────────────────────────────────────────────────────────────────
class ArchitectureAgent(LLMBackedMixin):
    id = "architecture"
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        return 'architecture' not in state and 'tech_stack' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🏗️ ArchitectureAgent", "intelligent architecture design")
        prompt = state.get('prompt',''); tech_stack = state.get('tech_stack',[]); complexity = state.get('complexity','moderate')
        system_prompt = """Design an optimal project architecture consistent with the chosen technologies. Return STRICT JSON:
{
  "project_structure":{"src/":"main source","config/":"configs","tests/":"tests"},
  "key_components":["ComponentA","ComponentB"],
  "data_flow":"high level flow",
  "scalability_approach":"how it scales"
}"""
        user_prompt = f"Project: {prompt}\nChosen Technologies:\n" + "\n".join([f"- {t.get('role')}: {t.get('name')} ({t.get('reasoning','')})" for t in tech_stack]) + f"\nComplexity: {complexity}"
        fallback = {"project_structure":{"src/":"main source","config/":"config files","tests/":"test files"},
                    "key_components":["App","Database","API"],
                    "data_flow":"Client → API → DB → Response","scalability_approach":"Horiz scale + LB"}
        result = self.llm_json(system_prompt, user_prompt, fallback)
        print("\n🏗️ INTELLIGENT ARCHITECTURE:")
        for k,v in list(result.get('project_structure',{}).items())[:3]:
            print(f"   📁 {k}: {v}")
        comps = result.get('key_components',[]); 
        if comps: print(f"   🔧 Components: {', '.join(comps[:3])}")
        return {'architecture': result}
