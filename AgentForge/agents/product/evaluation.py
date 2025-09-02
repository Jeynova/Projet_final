#!/usr/bin/env python3
"""
📊 EVALUATION AGENT
Project evaluation and final assessment
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call


# ──────────────────────────────────────────────────────────────────────────────
# 📊 EVALUATION AGENT
# ──────────────────────────────────────────────────────────────────────────────
class EvaluationAgent(LLMBackedMixin):
    id = "evaluation"
    def can_run(self, state: Dict[str, Any]) -> bool:
        return ('validation' in state) and state.get('goal_reached', False) and ('evaluation' not in state)
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("📊 EvaluationAgent", "project evaluation")
        prompt = state.get('prompt',''); tech_stack = state.get('tech_stack',[]); validation=state.get('validation',{}); architecture=state.get('architecture',{})
        sys_p = """Evaluate overall success: technology fit, code quality (validation), architecture soundness, user satisfaction, dev efficiency.
Return STRICT JSON:
{"overall_score":0-10,"technology_fit":0-10,"code_quality":0-10,"user_satisfaction":0-10,"feedback":"..."}"""
        user_p = f"Request: {prompt}\nTech:\n" + "\n".join([f"- {t.get('role')}: {t.get('name')} ({t.get('reasoning','')})" for t in tech_stack]) + \
                 f"\nValidation: {validation.get('status','unknown')} ({validation.get('score',0)}/10)\n" + \
                 f"Architecture components: {len(architecture.get('key_components',[]))}"
        fallback = {"overall_score":7,"technology_fit":7,"code_quality":validation.get('score',7),"user_satisfaction":7,"feedback":"Solid with room to improve"}
        result = self.llm_json(sys_p, user_p, fallback)
        print("\n📊 PROJECT EVALUATION:")
        print(f"   🎯 Overall: {result.get('overall_score',0)}/10  🔧 Tech Fit: {result.get('technology_fit',0)}/10  ✨ Quality: {result.get('code_quality',0)}/10")
        return {'evaluation': result}
