#!/usr/bin/env python3
"""
🎓 LEARNING MEMORY
Learning → seeds/merges contract → teaches → acts
"""

from typing import Dict, Any, List
from datetime import datetime

from core.base import LLMBackedMixin
from core.domain_detection import IntelligentDomainDetector
from core.contracts import merge_contract
from core.events import has_event_type
from core.scheduling import schedule_agents


# ──────────────────────────────────────────────────────────────────────────────
# 🎓 LEARNING MEMORY (now: learns → seeds/merges contract → teaches → acts)
# ──────────────────────────────────────────────────────────────────────────────
class LearningMemoryAgent(LLMBackedMixin):
    id = "memory"
    def __init__(self, rag_store=None, experience_db=None):
        super().__init__()
        self.rag = rag_store
        self.detector = IntelligentDomainDetector()
        self.experience_db = experience_db or {}

    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        never_ran = 'memory' not in state
        post_validation = 'last_validated_iter' in state and state.get('memory_epoch', -1) < state.get('last_validated_iter', -1)
        
        # Use standardized event checking
        events = state.get('events', [])
        event_triggered = (has_event_type(events, 'validation_completed') or 
                          has_event_type(events, 'refinement_triggered')) and not state.get('memory_after_validation_done', False)
        
        return never_ran or post_validation or event_triggered

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = state.get('prompt', '')
        analysis = self.detector.analyze_project(prompt)
        rag_hints, rag_conf, similar_cnt = [], 0.0, 0
        if self.rag:
            try:
                sims = self.rag.get_similar_projects(prompt); similar_cnt = len(sims)
                if sims:
                    print(f"   📚 RAG found {len(sims)} similar projects")
                    for proj in sims:
                        if proj.get('success_score',0) > 7.0:
                            sim = proj.get('similarity',0)
                            if sim > 0.3:
                                for tech in proj.get('tech_stack', []):
                                    rag_hints.append(f"Similar project ({sim:.1%}) used {tech.get('name','?')} for {tech.get('role','?')}")
                            if sim > 0.7: rag_conf = max(rag_conf, sim)
                    if rag_conf > 0.7 and sims[0].get('success_score',0) > 8.0:
                        best = sims[0]
                        return {**analysis,'rag_hints':rag_hints,'rag_confidence':rag_conf,'similar_projects_count':similar_cnt,
                                'complete_solution': {'tech_stack':best.get('tech_stack',[]),'confidence':rag_conf,'source':'RAG_high_confidence_match'},
                                'experience_hints': rag_hints[:3],'experience_warnings': [],'successful_patterns':[f"RAG: {len(sims)} strong matches"],
                                'hints': rag_hints[:3],'warnings': []}
            except Exception as e:
                print(f"   ⚠️ RAG lookup failed: {e}")

        guidance = self._get_experience_guidance(prompt, analysis)
        all_hints = (guidance.get('experience_hints') or []) + rag_hints

        # compile a MEMORY POLICY (prefer/avoid/seed/validation/coach_notes)
        sys_policy = """Compile a MEMORY POLICY. Return STRICT JSON:
{
  "prefer": {"backend": [], "frontend": [], "database": [], "deployment": []},
  "avoid": {"backend": [], "frontend": [], "database": [], "deployment": []},
  "seed_contract": {
    "files": ["backend/app.*","frontend/src/App.*","docker-compose.yml",".env.example","README.md","Makefile"],
    "endpoints": [{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],
    "tables": [{"name":"users"}]
  },
  "validation": {"min_score": 7, "require_valid": false, "mode": "guided"},
  "coach_notes": ["short, practical build tips (10 words max each)"]
}
Only concrete names; seed must be runnable."""
        user_policy = f"Domain={analysis.get('domain')} perf={analysis.get('performance_needs')} hints={all_hints[:6]}"
        fallback_policy = {
            "prefer": {"backend": [], "frontend": [], "database": [], "deployment": []},
            "avoid": {"backend": [], "frontend": [], "database": [], "deployment": []},
            "seed_contract": {
                "files": ["backend/app.js","frontend/src/App.js","docker-compose.yml",".env.example","README.md","Makefile"],
                "endpoints": [{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],
                "tables": [{"name":"users"}]
            },
            "validation": {"min_score": 7, "require_valid": False, "mode": "guided"},
            "coach_notes": ["use env vars", "add health check"]
        }
        policy = self.llm_json(sys_policy, user_policy, fallback_policy)

        # apply policy: seed/merge contract + set validation knobs + coach notes
        existing = state.get('contract', {})
        seeded = policy.get('seed_contract') or {}
        if seeded:
            merged = merge_contract(existing, seeded) if existing else {**seeded, "source": "memory_seed"}
            print("📐 MEMORY → seeded/merged contract")
        else:
            merged = existing

        res = {
            **analysis,
            **guidance,
            "memory_policy": policy,
            "contract": merged,
            "contract_seeded_by_memory": bool(seeded),
            "validation_threshold": policy.get('validation', {}).get('min_score', state.get('validation_threshold', 7)),
            "require_valid_status": policy.get('validation', {}).get('require_valid', state.get('require_valid_status', False)),
            "file_contract_mode": policy.get('validation', {}).get('mode', state.get('file_contract_mode','guided')),
            "coach_notes": policy.get('coach_notes', []),
            "memory": True,
            "memory_epoch": state.get('last_validated_iter', state.get('memory_epoch', 0)),
            "memory_after_validation_done": True  # Prevent thrashing
        }

        # If post-validation gaps exist, escalate strictness and schedule fixes
        if 'validation' in state:
            val = state['validation']
            gaps = (val.get('missing_files') or []) + (val.get('missing_endpoints') or [])
            if gaps and state.get('file_contract_mode') != 'strict':
                print("🧠 MEMORY → escalating contract mode to 'strict' next round")
                res['file_contract_mode'] = 'strict'
                schedule_agents(state, ['contract','codegen'], front=True)

        # echo learning analysis
        print("🧠 LEARNING MEMORY ANALYSIS:")
        print(f"   🎯 Domain: {analysis.get('domain')} (confidence: {analysis.get('confidence',0):.1%})")
        print(f"   📊 Complexity: {analysis.get('complexity')}")
        print(f"   ⚡ Performance: {analysis.get('performance_needs')}")
        if similar_cnt: print(f"   📚 RAG: {similar_cnt} similar projects found; conf {rag_conf:.1%}")
        if all_hints:
            print(f"   🎓 Total hints: {len(all_hints)}")
            for h in all_hints[:2]: print(f"      💡 {h}")

        return res

    def _get_experience_guidance(self, prompt: str, analysis: Dict) -> Dict:
        hints, warnings, patterns, complete_solution = [], [], [], None
        domain = analysis.get('domain','general'); p = (prompt or '').lower()
        if self.rag:
            try:
                sh = self.rag.get_tech_suggestions(prompt)
                if sh: hints.extend(sh[:3]); print(f"   📚 RAG provided {len(sh)} hints")
            except Exception as e:
                print(f"   ⚠️ RAG lookup failed: {e}")
        if domain == 'productivity':
            hints.append("Task/Project tools benefit from relational data (ACID, joins, reporting)")
            patterns.append("PostgreSQL + strict schemas improved integrity & reporting")
            warnings.append("Document stores complicate cross-entity queries & reporting")
        elif 'real-time' in p or 'chat' in p:
            hints.append("Real-time features benefit from WS-native stack")
            patterns.append("JS/Node excelled for long-lived connections")
        return {'experience_hints':hints,'experience_warnings':warnings,'successful_patterns':patterns,
                'hints':hints,'warnings':warnings,'complete_solution':complete_solution}

    def learn_from_outcome(self, project_prompt: str, chosen_stack: List[Dict], outcome_score: float):
        domain = self.detector.analyze_project(project_prompt).get('domain')
        if self.rag:
            try:
                self.rag.store_project_outcome(project_prompt, chosen_stack, outcome_score)
                print(f"📚 RAG stored project outcome: {project_prompt[:30]}... (score: {outcome_score})")
            except Exception as e:
                print(f"⚠️ RAG storage failed: {e}")
        backend = next((t for t in chosen_stack if t.get('role')=='backend'), {})
        if outcome_score > 8.0 and backend:
            if domain not in self.experience_db: self.experience_db[domain] = {'successes':[], 'failures':[]}
            self.experience_db[domain]['successes'].append({'tech': backend.get('name'), 'score': outcome_score, 'timestamp': datetime.now().isoformat()})
            print(f"🎓 LEARNED SUCCESS: {backend.get('name')} worked well for {domain}")
        elif outcome_score < 6.0 and backend:
            if domain not in self.experience_db: self.experience_db[domain] = {'successes':[], 'failures':[]}
            self.experience_db[domain]['failures'].append({'tech': backend.get('name'), 'score': outcome_score, 'timestamp': datetime.now().isoformat()})
            print(f"⚠️ LEARNED WARNING: {backend.get('name')} struggled for {domain}")
