#!/usr/bin/env python3
"""
🧩 CAPABILITY AGENT
Infer features/capabilities from project requirements
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call


# ──────────────────────────────────────────────────────────────────────────────
# 🧩 CAPABILITY AGENT
# ──────────────────────────────────────────────────────────────────────────────
class CapabilityAgent(LLMBackedMixin):
    id = "capabilities"
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        return 'capabilities' not in state and 'prompt' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🧩 CapabilityAgent", "infer features/capabilities")
        sys_p = """Extract capabilities from the product request. Return STRICT JSON:
{
  "entities": ["User","Project","Task"],
  "features": ["CRUD","assign","status","due_date","labels","comments"],
  "auth": true,
  "roles": ["admin","manager","member"],
  "non_functional": ["performance: medium","security: standard"]
}
Only include capabilities that make sense for the request; keep it concise."""
        user_p = f"REQUEST:\n{state.get('prompt','')}\n\nExisting hints: {state.get('experience_hints',[])}"
        fallback = {
            "entities":["User","Project","Task"], "features":["CRUD"], "auth": True,
            "roles":["admin","member"], "non_functional":["performance: medium","security: standard"]
        }
        caps = self.llm_json(sys_p, user_p, fallback)
        return {"capabilities": caps}
