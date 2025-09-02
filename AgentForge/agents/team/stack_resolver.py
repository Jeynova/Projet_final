#!/usr/bin/env python3
"""
🧭 STACK RESOLVER
Eliminate ambiguous "A or B" technology choices
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call


# ──────────────────────────────────────────────────────────────────────────────
# 🧭 STACK RESOLVER (eliminate ambiguous "A or B")
# ──────────────────────────────────────────────────────────────────────────────
class StackResolverAgent(LLMBackedMixin):
    id = "stack_resolver"
    def _has_ambiguity(self, name: str) -> bool:
        n = (name or "").lower()
        return (" or " in n) or ("/" in n) or ("either" in n) or ("|" in n)
    def can_run(self, state):
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        ts = state.get('tech_stack', [])
        if not ts: return False
        for t in ts:
            if isinstance(t, dict) and isinstance(t.get('name',''), str) and self._has_ambiguity(t['name']):
                return True
        return False
    def run(self, state):
        track_llm_call("🧭 StackResolverAgent", "resolve ambiguous tech stack")
        ts = state.get('tech_stack', [])
        sys_synth = """You are resolving ambiguous technology choices.
Output 3 CONCRETE candidates (no 'or', '/', 'either', or multiple choices).
Each candidate must contain exactly one backend, one frontend, one database, and one deployment.
Return STRICT JSON:
{
  "candidates": [
    {
      "backend": {"name":"...", "reasoning":"..."},
      "frontend": {"name":"...", "reasoning":"..."},
      "database": {"name":"...", "reasoning":"..."},
      "deployment": {"name":"...", "reasoning":"..."}
    },
    {...}, {...}
  ]
}"""
        user_synth = (
            "Project prompt:\n"
            f"{state.get('prompt','')}\n\n"
            f"Domain={state.get('domain','')}, complexity={state.get('complexity','')}, performance={state.get('performance_needs','')}\n"
            f"Current (possibly ambiguous) tech_stack={ts}\n"
            f"Hints={state.get('experience_hints', [])}\n"
            "Produce 3 distinct concrete candidates."
        )
        synth = self.llm_json(sys_synth, user_synth, fallback={"candidates": []})
        cands = synth.get("candidates") or []
        if not isinstance(cands, list) or not cands:
            print("🧭 Resolver: model failed to propose candidates → keeping original ambiguous stack.")
            return {"stack_resolved": False}

        sys_judge = """Choose the single best candidate for this project.
Selection criteria: fitness to prompt/domain/performance, maintainability, and coherence across layers.
Return STRICT JSON (no extra keys):
{
  "backend": {"name":"...", "reasoning":"..."},
  "frontend": {"name":"...", "reasoning":"..."},
  "database": {"name":"...", "reasoning":"..."},
  "deployment": {"name":"...", "reasoning":"..."},
  "rationale": "why this candidate was chosen over the others"
}
Rules:
- Must be one concrete choice per role.
- Do NOT write 'or', '/', or multiple alternatives.
"""
        user_judge = (
            "Project prompt:\n"
            f"{state.get('prompt','')}\n\n"
            f"Domain={state.get('domain','')}, complexity={state.get('complexity','')}, performance={state.get('performance_needs','')}\n"
            f"Hints={state.get('experience_hints', [])}\n"
            f"Candidates:\n{cands}"
        )
        judged = self.llm_json(sys_judge, user_judge, fallback={})
        roles = ("backend","frontend","database","deployment")
        ok = all(isinstance(judged.get(r,{}).get("name",""), str) and judged[r]["name"] for r in roles)
        if not ok:
            print("🧭 Resolver: judge failed to return a concrete stack → keeping original ambiguous stack.")
            return {"stack_resolved": False}

        new_stack = []
        for role in roles:
            d = judged.get(role, {})
            new_stack.append({"role": role, "name": d.get("name",""), "reasoning": d.get("reasoning","")})
        print("🧭 Resolver: ambiguity resolved by model.")
        return {"tech_stack": new_stack, "stack_resolved": True, "stack_resolution_rationale": judged.get("rationale","")}
