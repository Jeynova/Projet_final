#!/usr/bin/env python3
"""
✅ VALIDATION AGENT
Baseline + contract coverage validation
Emits events & schedules follow-up agents
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call
from core.contracts import is_contract_empty
from core.events import emit_event


# ──────────────────────────────────────────────────────────────────────────────
# ✅ VALIDATION AGENT (baseline + contract coverage) — emits events & schedules
# ──────────────────────────────────────────────────────────────────────────────
class ValidateAgent(LLMBackedMixin):
    id = "validate"
    def can_run(self, state):
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        if 'generated_code' not in state: return False
        return state.get('last_validated_iter', -1) < state.get('codegen_iters', 0)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("✅ ValidateAgent", "intelligent code validation")
        generated_code = state.get('generated_code', {}) or {}
        tech_stack = state.get('tech_stack', []) or []
        files_dict = generated_code.get('files', {}) or {}
        if not files_dict:
            return {'validation': {'status': 'no_code', 'score': 0}, 'last_validated_iter': state.get('codegen_iters', 0)}

        backend = next((t for t in tech_stack if t.get('role')=='backend'), {})
        contract = state.get('contract', {}) or {}
        mode = state.get('file_contract_mode','guided')  # 'free'|'guided'|'strict'

        manifest = sorted(list(files_dict.keys()))
        sample_names = manifest[:12]
        
        # Stack mismatch detection
        chosen = (backend.get('name','') or '').lower()
        is_node = 'node' in chosen or 'express' in chosen
        is_python = 'python' in chosen or 'django' in chosen or 'flask' in chosen

        found_py = any(p.startswith('backend/') and p.endswith('.py') for p in manifest)
        found_js_ts = any(p.startswith('backend/') and (p.endswith('.js') or p.endswith('.ts')) for p in manifest)

        events = state.get('events', [])
        
        if is_node and found_py:
            events.append({"type":"need_debate","meta":{"reason":"stack_mismatch","detail":"Node chosen but Python files in backend"}})
        elif is_python and found_js_ts:
            events.append({"type":"need_debate","meta":{"reason":"stack_mismatch","detail":"Python chosen but Node files in backend"}})
        
        previews = {}
        for name in sample_names:
            try:
                content = files_dict[name]
                previews[name] = (content[:1500] if isinstance(content, str) else str(content)[:1500])
            except Exception:
                previews[name] = ""

        system_prompt = f"""You are a senior reviewer. Validate the generated project.

BASELINE REQUIREMENTS (stack-agnostic):
- docker-compose.yml present & references (or stubs) backend/frontend/db services
- .env.example present with all env vars referenced by code/compose
- README.md includes Quickstart (≤3 commands), health URL, Docker run
- Makefile or scripts (or equivalent npm scripts) for dev/build/test
- /api/health endpoint reachable in backend code
- /docs route (Swagger/OpenAPI or docs page)
- .devcontainer/devcontainer.json (optional but preferred)

CONTRACT (if present): verify declared files & endpoints exist.

Return STRICT JSON:
{{
  "status": "valid|issues|invalid",
  "score": 0-10,
  "technical_score": 0-10,
  "security_score": 0-10,
  "architecture_score": 0-10,
  "ux_score": 0-10,
  "issues": ["..."],
  "suggestions": ["..."],
  "strengths": ["..."],
  "missing_files": ["paths required by the contract that are missing"],
  "missing_endpoints": ["METHOD /path"],
  "missing_baseline": ["docker-compose.yml",".env.example","README.md","/api/health","/docs","Makefile|scripts",".devcontainer/devcontainer.json"],
  "coverage": {{"files_percent": 0-100, "endpoints_percent": 0-100}}
}}

Rules:
- Be STRICT: only score ≥8 if production-ready and baseline satisfied.
- If CONTRACT is non-empty, prefer manifest-based verification. Use previews when helpful to infer endpoints/files.
- If uncertain an endpoint/file exists, list it as missing rather than assume.
"""

        user_prompt = f"""BACKEND: {backend.get('name','Unknown')}

CONTRACT (may be empty):
{{
  "files": {contract.get('files', [])[:60]},
  "endpoints": {contract.get('endpoints', [])[:60]},
  "tables": {contract.get('tables', [])[:40]}
}}

MANIFEST ({len(manifest)} files):
{manifest[:120]}

SAMPLED PREVIEWS ({len(previews)} files, truncated):
{ {k: (v[:300] + '...') for k,v in previews.items()} }
"""

        fallback_validation = {
            "status":"issues","score":6,"technical_score":6,"security_score":5,"architecture_score":6,"ux_score":6,
            "issues":["Limited error handling","No auth flow"],"suggestions":["Add auth","Add tests"],
            "strengths":["Clean structure"],"missing_files":[],"missing_endpoints":[],"missing_baseline":[],
            "coverage":{"files_percent":50,"endpoints_percent":40}
        }
        result = self.llm_json(system_prompt, user_prompt, fallback_validation)

        # contract/baseline flags
        mf = result.get('missing_files') or []
        me = result.get('missing_endpoints') or []
        mb = result.get('missing_baseline') or []
        contract_empty = is_contract_empty(contract)

        if mode == 'strict' and (mf or me):
            result['status'] = 'invalid'
            result['score'] = min(result.get('score',0), 5)

        print(f"\n✅ INTELLIGENT VALIDATION:")
        print(f"   📊 Overall: {result.get('score',0)}/10  ({result.get('status','unknown')})")
        print(f"   🔧 Technical: {result.get('technical_score',0)}/10  🔒 Security: {result.get('security_score',0)}/10")
        print(f"   🧱 Architecture: {result.get('architecture_score',0)}/10  📱 UX: {result.get('ux_score',0)}/10")
        if result.get('issues'): 
            print(f"   ⚠️ Issues ({len(result['issues'])}):"); [print(f"      • {i}") for i in result['issues'][:3]]
        if mf or me or mb:
            if mf: print(f"   📂 Missing files: {len(mf)} (e.g., {', '.join(mf[:3])})")
            if me: print(f"   🔗 Missing endpoints: {len(me)} (e.g., {', '.join(me[:3])})")
            if mb: print(f"   🧱 Missing baseline: {', '.join(mb[:5])}{'…' if len(mb)>5 else ''}")

        # Emit reactive events + schedule agents
        nexts = []
        if mf or me:
            emit_event(state, {"type":"expand_contract","missing_files": mf, "missing_endpoints": me, "source":"validate"})
            nexts.extend(['contract','codegen'])
        if result.get('technical_score',0) <= 4 or result.get('architecture_score',0) <= 3:
            emit_event(state, {"type":"need_debate","reason":"low_quality_after_validation"})
            nexts.append('tech_team')

        current_iter = state.get('codegen_iters', 0)
        best_score = state.get('best_validation_score', -1)
        if result.get('score',0) > best_score:
            state['best_validation_score'] = result.get('score',0)
            state['best_generated_code'] = state.get('generated_code', {})

        return {
            'validation': result,
            'last_validated_iter': current_iter,
            'best_validation_score': state.get('best_validation_score', -1),
            'best_generated_code': state.get('best_generated_code', {}),
            'contract_missing_files': mf,
            'contract_missing_endpoints': me,
            'missing_baseline': mb,
            'contract_empty': contract_empty,
            'next_agents': nexts,
            'events': events + [{"type": "validation_completed", "meta": {"score": result.get('score', 0), "status": result.get('status', 'unknown'), "iteration": current_iter}}],
            'memory_after_validation_done': False  # Reset memory gate
        }
