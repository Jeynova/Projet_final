#!/usr/bin/env python3
"""
🔀 VALIDATION ROUTER
Loop control and iteration management
"""

from typing import Dict, Any


# ──────────────────────────────────────────────────────────────────────────────
# 🔀 VALIDATION ROUTER (loop control)
# ──────────────────────────────────────────────────────────────────────────────
class ValidationRouter:
    id = "ValidationRouter"
    name = "ValidationRouter"
    def can_run(self, state):
        return ('validation' in state and state.get('routed_after_iter', -1) < state.get('last_validated_iter', -1))
    def run(self, state):
        val = state.get('validation', {}) or {}
        score = val.get('score', 0)
        status = val.get('status', '')
        threshold = state.get('validation_threshold', 7)
        it = state.get('last_validated_iter', 0)     # completed codegen+validate cycles so far
        max_iters = state.get('max_codegen_iters', 4)

        result = {'routed_after_iter': it}
        require_valid = state.get('require_valid_status', False)

        # success
        if score >= threshold and (not require_valid or (status == 'valid')):
            result['goal_reached'] = True
            print(f"🎯 QUALITY GOAL REACHED: Score {score}/10 ≥ {threshold}/10" + (" and status=valid" if require_valid else ""))
            return result

        # contract / baseline gaps → fix first
        contract_empty = state.get('contract_empty', False)
        missing_baseline = state.get('missing_baseline', []) or []

        if contract_empty and it < max_iters:
            result['redo_contract'] = True
            result['redo_codegen'] = True
            result['next_agents'] = ['contract','codegen']
            result['events'] = state.get('events', []) + [{"type": "refinement_triggered", "meta": {"reason": "contract_missing", "iteration": it+1}}]
            print(f"📐 CONTRACT MISSING on iter {it} → derive contract and regenerate code (iter {it+1})")
            return result

        if missing_baseline and it < max_iters:
            result['redo_contract'] = True
            result['redo_codegen'] = True
            result['next_agents'] = ['contract','codegen']
            result['events'] = state.get('events', []) + [{"type": "refinement_triggered", "meta": {"reason": "baseline_missing", "missing_items": missing_baseline, "iteration": it+1}}]
            msg = ", ".join(missing_baseline[:4]) + ("…" if len(missing_baseline) > 4 else "")
            print(f"🧱 BASELINE MISSING ({msg}) → update contract & regenerate (iter {it+1})")
            return result

        # no code → retry if possible
        if status == 'no_code' and it < max_iters:
            result['redo_codegen'] = True
            result['next_agents'] = ['codegen']
            result['events'] = state.get('events', []) + [{"type": "refinement_triggered", "meta": {"reason": "no_code", "iteration": it+1}}]
            print(f"⚠️ NO CODE on iter {it} → retry (iter {it+1})")
            return result

        # refine or stop
        if it < max_iters:
            result['redo_codegen'] = True
            result['next_agents'] = ['codegen']
            result['events'] = state.get('events', []) + [{"type": "refinement_triggered", "meta": {"reason": "quality_improvement", "score": score, "threshold": threshold, "iteration": it+1}}]
            print(f"🔄 REFINEMENT: Score {score}/10 < {threshold}/10 → iterate (iter {it+1})")
        else:
            result['goal_reached'] = True
            print(f"⏭️ MAX ITERATIONS: proceed with score {score}/10 after {it} attempts")
        return result