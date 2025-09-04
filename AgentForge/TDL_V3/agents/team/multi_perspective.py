#!/usr/bin/env python3
"""
🎭 MULTI-PERSPECTIVE TECH TEAM
Honors memory; can be re-invoked via events
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call
from core.events import has_event_type, filter_events_by_type
from adaptaters.team_debate import run_debate, moderate


# ──────────────────────────────────────────────────────────────────────────────
# 🎭 MULTI-PERSPECTIVE TECH TEAM (honors memory; can be re-invoked via events)
# ──────────────────────────────────────────────────────────────────────────────
class MultiPerspectiveTechAgent(LLMBackedMixin):
    id = "tech_team"
    def __init__(self): super().__init__()
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
        
        # initial selection
        if 'tech_stack' not in state and any(k in state for k in ['domain','complexity','performance_needs']):
            return True
        
        # re-run only on explicit reasons
        for ev in state.get('events', []):
            if ev.get('type') == 'need_debate' and ev.get('meta', {}).get('reason') in {
                'stack_mismatch', 'perf_regression', 'security_gap'
            }:
                return True
        return False
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🎭 MultiPerspectiveTechAgent", "parallel team debate decision")
        prompt = state.get('prompt','')
        hints = state.get('experience_hints',[])
        warnings = state.get('experience_warnings',[])
        mem = state.get('memory_policy', {}) or {}
        prefer, avoid = mem.get('prefer',{}), mem.get('avoid',{})
        coach_notes = state.get('coach_notes',[])

        domain, complexity, performance = state.get('domain','general'), state.get('complexity','moderate'), state.get('performance_needs','medium')
        debate_context = "\n".join([
            f"Project: {prompt}",
            f"Domain: {domain} (complexity: {complexity}, performance: {performance})",
            f"Experience: {'; '.join(hints) if hints else '—'}",
            f"Warnings: {'; '.join(warnings) if warnings else '—'}",
            f"Memory Prefer: {prefer}",
            f"Memory Avoid: {avoid}",
            f"Coach Notes: {coach_notes[:3]}"
        ])
        try:
            print("🎭 Starting parallel team debate for technology decision...")
            debate_results = run_debate(self.llm_client, "Technology Stack Decision", debate_context)
            print("⚖️ Moderating parallel perspectives into consensus...")
            team_consensus = moderate(self.llm_client, "Synthesize team perspectives", debate_results)
            extraction_prompt = """Extract one concrete stack from TEAM CONSENSUS.
Honor Memory Prefer/Avoid if reasonable.
Rules: Return exactly one concrete choice per category; do NOT use 'or', '/', 'either', or multiple options.
Return STRICT JSON:
{
  "backend": {"name": "chosen_backend", "reasoning": "why"},
  "frontend": {"name": "chosen_frontend", "reasoning": "why"},
  "database": {"name": "chosen_database", "reasoning": "why"},
  "deployment": {"name": "chosen_deployment", "reasoning": "why"},
  "team_discussion": "short summary",
  "debate_method": "concurrent_parallel_execution"
}"""
            fallback_team = { "team_discussion": team_consensus, "debate_method":"concurrent_parallel_execution" }
            result = self.llm_json(extraction_prompt, team_consensus, fallback_team)
            result['parallel_debate_results'] = debate_results; result['concurrent_roles'] = ['PM','DEV','PO','CONSULTANT','USER']
        except Exception as e:
            print(f"⚠️ Team debate system error: {e}")
            result = {"team_discussion":"LLM failure; no decision","debate_method":"single_llm_fallback"}

        print(f"\n🎭 TEAM TECHNOLOGY DECISION:")
        print(f"   🖥️ Backend: {result.get('backend',{}).get('name','?')}")
        print(f"   🎨 Frontend: {result.get('frontend',{}).get('name','?')}")
        print(f"   🗄️ Database: {result.get('database',{}).get('name','?')}")
        print(f"   🚀 Deploy: {result.get('deployment',{}).get('name','?')}")
        if isinstance(result.get('team_discussion',''), str):
            print(f"   💬 Team process: {result.get('team_discussion')[:100]}...")

        tech_stack = []
        for role, details in result.items():
            if role != 'team_discussion' and isinstance(details, dict) and 'name' in details:
                tech_stack.append({'role': role, 'name': details.get('name','Unknown'), 'reasoning': details.get('reasoning','Team decision')})

        # clear only consumed trigger events - use standardized event filtering
        state['events'] = [e for e in state.get('events', []) if e.get('type') != 'need_debate']
        return {'tech_stack': tech_stack, 'team_decision_process': result}