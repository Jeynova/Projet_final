#!/usr/bin/env python3
"""
🎭 ORGANIC INTELLIGENCE: Multi-Perspective Team + Learning Guidance
LLM-only contracts & validation (no hard-coded heuristics).
"""

import sys
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

sys.path.append('.')
from core.llm_client import LLMClient
from team_debate import run_debate, moderate

def track_llm_call(agent: str, operation: str):
    print(f"🔄 {agent} → {operation}")

# ──────────────────────────────────────────────────────────────────────────────
# 🔎 LIGHT CONTEXT ANALYSIS (guidance only, not prescriptive)
# ──────────────────────────────────────────────────────────────────────────────
class IntelligentDomainDetector:
    DOMAIN_PATTERNS = {
        'blog': ['blog', 'cms', 'content', 'article', 'post'],
        'ecommerce': ['shop', 'store', 'ecommerce', 'payment', 'cart'],
        'social': ['chat', 'social', 'message', 'real-time', 'live'],
        'enterprise': ['enterprise', 'corporate', 'business', 'document'],
        'analytics': ['analytics', 'data', 'dashboard', 'reporting'],
        'api': ['api', 'rest', 'endpoint', 'microservice', 'service'],
        'productivity': ['task', 'tasks', 'project', 'projects', 'kanban', 'scrum', 'team', 'teams', 'collaboration', 'assign', 'deadline']
    }
    def analyze_project(self, prompt: str) -> Dict[str, any]:
        p = (prompt or "").lower()
        scores = {d: sum(3 for w in ws if w in p) for d, ws in self.DOMAIN_PATTERNS.items()}
        best = max(scores.items(), key=lambda x: x[1]) if scores else ('general', 0)
        domain = best[0] if best[1] > 0 else 'general'
        complexity = 'simple' if any(w in p for w in ['simple','basic']) else 'moderate'
        if any(w in p for w in ['enterprise','complex','advanced']): complexity = 'complex'
        perf = 'low' if 'simple' in p else 'medium'
        if any(w in p for w in ['high-performance','fast','real-time']): perf = 'high'
        return {'domain': domain, 'complexity': complexity, 'performance_needs': perf, 'confidence': min(1.0, best[1]/10.0)}

# ──────────────────────────────────────────────────────────────────────────────
# 🧠 LLM MIXIN
# ──────────────────────────────────────────────────────────────────────────────
class LLMBackedMixin:
    def __init__(self):
        self.llm_client = LLMClient()
    def llm_json(self, system_prompt: str, user_prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = self.llm_client.extract_json(system_prompt, user_prompt)
            if not isinstance(result, dict) or not result:
                return fallback
            return {**fallback, **result}
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return fallback

# ──────────────────────────────────────────────────────────────────────────────
# 🔧 HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def _is_contract_empty(c: dict) -> bool:
    c = c or {}
    has_files = isinstance(c.get('files'), list) and len(c['files']) > 0
    has_eps   = isinstance(c.get('endpoints'), list) and len(c['endpoints']) > 0
    return not (has_files and has_eps)

# ──────────────────────────────────────────────────────────────────────────────
# 🔀 VALIDATION ROUTER (loop control)
# ──────────────────────────────────────────────────────────────────────────────
class ValidationRouter:
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
            print(f"📐 CONTRACT MISSING on iter {it} → derive contract and regenerate code (iter {it+1})")
            return result

        if missing_baseline and it < max_iters:
            result['redo_contract'] = True
            result['redo_codegen'] = True
            msg = ", ".join(missing_baseline[:4]) + ("…" if len(missing_baseline) > 4 else "")
            print(f"🧱 BASELINE MISSING ({msg}) → update contract & regenerate (iter {it+1})")
            return result

        # no code → retry if possible
        if status == 'no_code' and it < max_iters:
            result['redo_codegen'] = True
            print(f"⚠️ NO CODE on iter {it} → retry (iter {it+1})")
            return result

        # refine or stop
        if it < max_iters:
            result['redo_codegen'] = True
            print(f"🔄 REFINEMENT: Score {score}/10 < {threshold}/10 → iterate (iter {it+1})")
        else:
            result['goal_reached'] = True
            print(f"⏭️ MAX ITERATIONS: proceed with score {score}/10 after {it} attempts")
        return result

# ──────────────────────────────────────────────────────────────────────────────
# 🎓 LEARNING MEMORY
# ──────────────────────────────────────────────────────────────────────────────
class LearningMemoryAgent(LLMBackedMixin):
    id = "memory"
    def __init__(self, rag_store=None, experience_db=None):
        super().__init__()
        self.rag = rag_store
        self.detector = IntelligentDomainDetector()
        self.experience_db = experience_db or {}
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'memory' not in state
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
        all_hints = rag_hints + guidance.get('experience_hints', [])
        print("🧠 LEARNING MEMORY ANALYSIS:")
        print(f"   🎯 Domain: {analysis.get('domain')} (confidence: {analysis.get('confidence',0):.1%})")
        print(f"   📊 Complexity: {analysis.get('complexity')}")
        print(f"   ⚡ Performance: {analysis.get('performance_needs')}")
        if similar_cnt: print(f"   📚 RAG: {similar_cnt} similar projects found; conf {rag_conf:.1%}")
        if all_hints:
            print(f"   🎓 Total hints: {len(all_hints)}"); [print(f"      💡 {h}") for h in all_hints[:2]]
        if guidance.get('warnings'):
            print(f"   ⚠️ Warnings: {', '.join(guidance['warnings'][:2])}")

        res = {**analysis, **guidance, 'rag_hints': rag_hints, 'rag_confidence': rag_conf, 'similar_projects_count': similar_cnt}
        res['experience_hints'] = all_hints[:5]; res['hints'] = all_hints[:5]
        if guidance.get('complete_solution'):
            res.update(guidance['complete_solution']); print("   🚀 BYPASS: experience provides complete solution!")
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

# ──────────────────────────────────────────────────────────────────────────────
# 🎭 MULTI-PERSPECTIVE TECH TEAM
# ──────────────────────────────────────────────────────────────────────────────
class MultiPerspectiveTechAgent(LLMBackedMixin):
    id = "tech_team"
    def __init__(self): super().__init__()
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'tech_stack' not in state and any(k in state for k in ['domain','complexity','performance_needs'])
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🎭 MultiPerspectiveTechAgent", "parallel team debate decision")
        prompt = state.get('prompt',''); hints = state.get('experience_hints',[]); warnings = state.get('experience_warnings',[])
        domain, complexity, performance = state.get('domain','general'), state.get('complexity','moderate'), state.get('performance_needs','medium')
        debate_context = "\n".join([f"Project: {prompt}",
                                    f"Domain: {domain} (complexity: {complexity}, performance: {performance})",
                                    f"Experience: {'; '.join(hints) if hints else '—'}",
                                    f"Warnings: {'; '.join(warnings) if warnings else '—'}"])
        try:
            print("🎭 Starting parallel team debate for technology decision...")
            debate_results = run_debate(self.llm_client, "Technology Stack Decision", debate_context)
            print("⚖️ Moderating parallel perspectives into consensus...")
            team_consensus = moderate(self.llm_client, "Synthesize team perspectives", debate_results)
            extraction_prompt = """Extract one concrete stack from TEAM CONSENSUS.
Rules: Return exactly one concrete choice per category; do NOT use 'or', '/', 'either', or multiple options.
Return STRICT JSON:
{
  "backend": {"name": "chosen_backend", "reasoning": "why"},
  "frontend": {"name": "chosen_frontend", "reasoning": "why"},
  ️"database": {"name": "chosen_database", "reasoning": "why"},
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
        return {'tech_stack': tech_stack, 'team_decision_process': result}

# ──────────────────────────────────────────────────────────────────────────────
# 🧭 STACK RESOLVER (eliminate ambiguous "A or B")
# ──────────────────────────────────────────────────────────────────────────────
class StackResolverAgent(LLMBackedMixin):
    id = "stack_resolver"
    def _has_ambiguity(self, name: str) -> bool:
        n = (name or "").lower()
        return (" or " in n) or ("/" in n) or ("either" in n) or ("|" in n)
    def can_run(self, state):
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

# ──────────────────────────────────────────────────────────────────────────────
# 🧩 CAPABILITY AGENT
# ──────────────────────────────────────────────────────────────────────────────
class CapabilityAgent(LLMBackedMixin):
    id = "capabilities"
    def can_run(self, state: Dict[str, Any]) -> bool:
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

# ──────────────────────────────────────────────────────────────────────────────
# 📐 CONTRACT AGENT (LLM proposes files/endpoints/tables) — rerunnable
# ──────────────────────────────────────────────────────────────────────────────
class ContractAgent(LLMBackedMixin):
    id = "contract"
    def __init__(self): super().__init__()
    def can_run(self, state: Dict[str, Any]) -> bool:
        needs_redo = state.get('redo_contract', False)
        return (('contract' not in state) or needs_redo) and ('capabilities' in state) and ('tech_stack' in state)
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("📐 ContractAgent", "derive delivery contract")
        _ = state.pop('redo_contract', False)
        tech_stack = state.get('tech_stack', [])
        caps = state.get('capabilities', {})
        sys_p = """Given the chosen stack and capabilities, propose a PRACTICAL delivery CONTRACT.

Baseline boilerplate ALL web projects should ship (stack-agnostic):
- docker-compose.yml with backend, frontend and db (or stub)
- .env.example with required vars
- README.md with Quickstart (≤3 commands), health URL, Docker run
- Makefile or scripts for dev/build/test
- /api/health endpoint
- /docs (Swagger/OpenAPI or docs page)
- scripts/dev.sh, scripts/build.sh, scripts/test.sh (or npm equivalents)
- .devcontainer/devcontainer.json (optional; include or state "omitted")

Return STRICT JSON:
{
  "files": ["backend/app.*", "backend/routes/*.js", "frontend/src/App.*", "docker-compose.yml", ".env.example", "README.md", "Makefile", ".devcontainer/devcontainer.json", "scripts/dev.sh", "scripts/build.sh", "scripts/test.sh"],
  "endpoints": [{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],
  "tables": [{"name":"users"}]
}
Keep ≤ 30 files. Match file extensions to the chosen backend."""
        user_p = f"TECH_STACK:\n{tech_stack}\n\nCAPABILITIES:\n{caps}\n"
        fallback = {
            "files":["backend/app.js","frontend/src/App.js","docker-compose.yml",".env.example","README.md","Makefile"],
            "endpoints":[{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],
            "tables":[{"name":"users"}]
        }
        contract = self.llm_json(sys_p, user_p, fallback)
        contract['source'] = 'llm'
        if _is_contract_empty(contract):
            print("⚠️ ContractAgent produced an empty contract – downstream will draft a minimal one.")
        return {"contract": contract}

# ──────────────────────────────────────────────────────────────────────────────
# 🛡️ CONTRACT PRESENCE GUARD (ensure contract exists before codegen)
# ──────────────────────────────────────────────────────────────────────────────
class ContractPresenceGuard(LLMBackedMixin):
    id = "contract_guard"
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'tech_stack' not in state: return False
        return ('contract' not in state) or _is_contract_empty(state.get('contract', {}))
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🛡️ ContractPresenceGuard", "ensure minimal contract exists")
        tech_stack = state.get('tech_stack', [])
        caps = state.get('capabilities', {})
        sys_p = """Draft a MINIMAL but runnable CONTRACT for the chosen stack+capabilities.
Respect the baseline boilerplate (docker-compose, .env.example, README.md, Makefile/scripts, /api/health, /docs).

Return STRICT JSON:
{"files":["backend/app.*","frontend/src/App.*","docker-compose.yml",".env.example","README.md"],"endpoints":[{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],"tables":[{"name":"users"}]}
"""
        user_p = f"STACK:\n{tech_stack}\nCAPABILITIES:\n{caps}\nKeep ≤ 20 files."
        fallback = {"files":["backend/app.js","frontend/src/App.js","docker-compose.yml",".env.example","README.md"],"endpoints":[{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],"tables":[{"name":"users"}]}
        contract = self.llm_json(sys_p, user_p, fallback)
        contract['source'] = 'guard'
        print("🛡️ ContractPresenceGuard: drafted minimal contract.")
        return {"contract": contract}

# ──────────────────────────────────────────────────────────────────────────────
# 🏗️ ARCHITECTURE AGENT
# ──────────────────────────────────────────────────────────────────────────────
class ArchitectureAgent(LLMBackedMixin):
    id = "architecture"
    def can_run(self, state: Dict[str, Any]) -> bool:
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

# ──────────────────────────────────────────────────────────────────────────────
# 💾 CODE GENERATION AGENT
# ──────────────────────────────────────────────────────────────────────────────
class CodeGenAgent(LLMBackedMixin):
    id = "codegen"
    def can_run(self, state):
        if 'architecture' not in state or 'tech_stack' not in state:
            return False
        needs_rerun = state.get('redo_codegen', False)
        not_done = 'generated_code' not in state or needs_rerun
        max_iters = state.get('max_codegen_iters', 4)
        return not_done and state.get('codegen_iters', 0) < max_iters

    def run(self, state):
        track_llm_call("💾 CodeGenAgent", "intelligent multi-language generation")
        _ = state.pop('redo_codegen', False)
        prior_issues = state.get('validation', {}).get('issues', [])
        suggestions   = state.get('validation', {}).get('suggestions', [])
        missing_files = state.get('contract_missing_files', []) or []
        missing_eps   = state.get('contract_missing_endpoints', []) or []

        prompt = state.get('prompt',''); tech_stack = state.get('tech_stack',[]); architecture = state.get('architecture',{})
        backend = next((t for t in tech_stack if t.get('role')=='backend'),{})
        frontend = next((t for t in tech_stack if t.get('role')=='frontend'),{})
        database = next((t for t in tech_stack if t.get('role')=='database'),{})
        contract = state.get('contract',{}) or {}
        mode = state.get('file_contract_mode','guided')  # 'free'|'guided'|'strict'

        # draft a minimal contract inline if still missing
        if _is_contract_empty(contract):
            print("🛠️ CodeGen: no contract provided → drafting minimal contract inline.")
            sys_cp = """Propose a minimal CONTRACT (files/endpoints/tables) suitable for immediate implementation with the chosen stack.
Include docker-compose.yml, .env.example, README.md, /api/health, /docs.
Return STRICT JSON like:
{"files":["backend/app.*","frontend/src/App.*","docker-compose.yml",".env.example","README.md"],"endpoints":[{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],"tables":[{"name":"users"}]}"""
            user_cp = f"STACK:\n{tech_stack}\nARCHITECTURE:\n{architecture}\nKeep ≤ 20 files."
            mini = self.llm_json(sys_cp, user_cp, {"files":["backend/app.js","frontend/src/App.js","docker-compose.yml",".env.example","README.md"],"endpoints":[{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],"tables":[{"name":"users"}]})
            mini['source'] = 'codegen_inline'
            contract = mini

        system_prompt = f"""You are an expert full-stack developer. Generate COMPLETE, WORKING code consistent with the chosen stack.

Quality guardrails:
- proper structure & separation
- error handling & logging
- auth & authorization when requested
- env vars, validation, CORS, rate limits
- responsive UI with feedback
- docs + setup + realistic sample data

Return STRICT JSON:
{{
  "files": {{"path":"content", "...":"..."}},
  "setup_instructions": ["..."],
  "run_commands": ["..."],
  "deployment_notes": ["..."]
}}"""

        fb = []
        if prior_issues or suggestions: fb += [*prior_issues[:5], *suggestions[:5]]
        if missing_files: fb.append("Missing files last iteration: " + ", ".join(missing_files[:20]))
        if missing_eps:   fb.append("Missing endpoints last iteration: " + ", ".join(missing_eps[:20]))
        feedback_block = ("\n\nFix these before anything else:\n- " + "\n- ".join(fb)) if fb else ""

        contract_block = ""
        if contract:
            req_files = "\n".join(f"- {p}" for p in (contract.get('files') or [])[:60])
            req_eps   = "\n".join(f"- {e.get('method','GET')} {e.get('path','')}" for e in (contract.get('endpoints') or [])[:60])
            req_tabs  = "\n".join(f"- {t.get('name','')}" for t in (contract.get('tables') or [])[:40])
            contract_block = f"""
### IMPLEMENT THIS CONTRACT (mode={mode}, source={contract.get('source','llm')})
REQUIRED FILES:
{req_files}

REQUIRED ENDPOINTS:
{req_eps}

REQUIRED TABLES:
{req_tabs}
"""
        strict_line = "\nYou MUST output every required file and implement every required endpoint." if mode == 'strict' else ""

        user_prompt = f"""Project: {prompt}

🎯 TEAM DECISIONS:
{chr(10).join([f"- {t.get('role','?')}: {t.get('name','?')} (Reason: {t.get('reasoning','')})" for t in tech_stack])}

🏗️ ARCHITECTURE:
Structure: {architecture.get('project_structure',{})}
Key Components: {', '.join(architecture.get('key_components',[]))}

{contract_block}{strict_line}{feedback_block}

Deliver COMPLETE, runnable code in the JSON format specified."""
        fallback_code = {
            "files":{
                "backend/app.js":"// minimal backend placeholder\nconst express=require('express');const app=express();app.get('/api/health',(_,res)=>res.json({status:'ok'}));app.listen(5000);",
                "frontend/src/App.js":"import React from 'react';export default function App(){return <h1>App</h1>;}",
                "database/schema.sql":"-- minimal",
                "README.md":"# App\n\nHow to run...",
                "docker-compose.yml":"version: '3'\nservices:{}"
            },
            "setup_instructions":["install deps","run dev"],
            "run_commands":["npm start"],
            "deployment_notes":["use env vars"]
        }
        result = self.llm_json(system_prompt, user_prompt, fallback_code)

        print(f"\n💾 INTELLIGENT CODE GENERATION:")
        files = result.get('files',{}) or {}
        print(f"   📝 Generated {len(files) if isinstance(files,dict) else len(files or [])} files")
        for f in (list(files.keys())[:3] if isinstance(files,dict) else []): print(f"   📄 {f}")
        if result.get('setup_instructions'): print(f"   ⚙️ Setup steps: {len(result['setup_instructions'])}")

        prev = state.get('generated_code',{})
        if not files and isinstance(prev,dict) and prev.get('files'):
            print("⚠️ No files returned; preserving previous generated_code.")
            result = {**prev}

        iters = state.get('codegen_iters',0) + 1
        result['codegen_iters'] = iters
        return {'generated_code': result, 'codegen_iters': iters, 'redo_codegen': False, 'contract': contract}

# ──────────────────────────────────────────────────────────────────────────────
# 🗄️ DATABASE AGENT
# ──────────────────────────────────────────────────────────────────────────────
class DatabaseAgent(LLMBackedMixin):
    id = "database"
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'database_schema' not in state and 'tech_stack' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🗄️ DatabaseAgent", "schema design")
        prompt = state.get('prompt',''); tech_stack = state.get('tech_stack',[])
        database = next((t for t in tech_stack if t.get('role')=='database'),{}); dbn = database.get('name','Unknown')
        sys_p = f"""Design an optimal schema for {dbn}. Return STRICT JSON:
{{
  "tables": {{"table_name": {{"columns": {{"col":"type"}}, "indexes":["..."], "relationships":["..."]}}}},
  "optimization_notes":"..."
}}"""
        user_p = f"Project: {prompt}\nDB: {dbn} ({database.get('reasoning','')})"
        fallback = {"tables":{"users":{"columns":{"id":"PRIMARY KEY","email":"VARCHAR"},"indexes":["email"],"relationships":[]}},
                    "optimization_notes":"basic"}
        result = self.llm_json(sys_p, user_p, fallback)
        print("\n🗄️ INTELLIGENT DATABASE DESIGN:")
        tables = result.get('tables',{}); print(f"   📊 Tables: {', '.join(list(tables.keys())[:3])}")
        if result.get('optimization_notes'): print(f"   ⚡ Optimizations: {result['optimization_notes'][:50]}...")
        return {'database_schema': result}

# ──────────────────────────────────────────────────────────────────────────────
# 🚀 DEPLOYMENT AGENT
# ──────────────────────────────────────────────────────────────────────────────
class DeploymentAgent(LLMBackedMixin):
    id = "deployment"
    def can_run(self, state: Dict[str, Any]) -> bool:
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

# ──────────────────────────────────────────────────────────────────────────────
# ✅ VALIDATION AGENT (baseline + contract coverage)
# ──────────────────────────────────────────────────────────────────────────────
class ValidateAgent(LLMBackedMixin):
    id = "validate"
    def can_run(self, state):
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
        contract_empty = _is_contract_empty(contract)

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
            'contract_empty': contract_empty
        }

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

# ──────────────────────────────────────────────────────────────────────────────
# 🎯 ORCHESTRATOR
# ──────────────────────────────────────────────────────────────────────────────
class PureIntelligenceOrchestrator:
    """LLM-only contract + validation pipeline (no local heuristics)"""
    def __init__(self, rag_store=None):
        self.agents = [
            LearningMemoryAgent(rag_store),
            MultiPerspectiveTechAgent(),
            StackResolverAgent(),       # resolve "A or B"
            CapabilityAgent(),
            ContractAgent(),
            ContractPresenceGuard(),    # ensure a contract exists
            ArchitectureAgent(),
            CodeGenAgent(),
            DatabaseAgent(),
            DeploymentAgent(),
            ValidateAgent(),
            ValidationRouter(),
            EvaluationAgent()
        ]
        self.learning_memory = self.agents[0]

    def run_pipeline(self, prompt: str) -> Dict[str, Any]:
        print(f"🎭 PURE INTELLIGENCE PIPELINE: {prompt[:50]}...")
        state = {
            'prompt': prompt,
            'max_codegen_iters': 4,       # demo-friendly
            'validation_threshold': 7,    # demo-friendly
            'file_contract_mode': 'strict',  # make contract/baseline coverage matter
        }
        for agent in self.agents:
            try:
                if agent.can_run(state):
                    print(f"\n🔄 Running {agent.__class__.__name__}")
                    result = agent.run(state); state.update(result)
                else:
                    print(f"⏭️ Skipping {agent.__class__.__name__} - conditions not met")
            except Exception as e:
                print(f"❌ {agent.__class__.__name__} failed: {e}")
                import traceback; traceback.print_exc(); continue

        if 'evaluation' in state and 'tech_stack' in state:
            overall = state['evaluation'].get('overall_score', 5)
            print(f"\n🎓 LEARNING FROM OUTCOME ({overall}/10)")
            self.learning_memory.learn_from_outcome(prompt, state['tech_stack'], overall)
        print("\n🎉 PURE INTELLIGENCE COMPLETE!")
        return state

    def save_generated_project(self, state: Dict[str, Any], project_name: str) -> str:
        generated_code = state.get('generated_code', {}); files = generated_code.get('files', {})
        if not files: print("❌ No files to save"); return ""
        output_dir = Path(tempfile.mkdtemp()) / project_name; output_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            fp = output_dir / filename; fp.parent.mkdir(parents=True, exist_ok=True); fp.write_text(content, encoding='utf-8')
        print(f"💾 Project saved to: {output_dir}"); return str(output_dir)

# ──────────────────────────────────────────────────────────────────────────────
# 🧪 LOCAL TEST
# ──────────────────────────────────────────────────────────────────────────────
def test_organic_intelligence():
    orch = PureIntelligenceOrchestrator()
    tests = [
        "Create a simple blog platform for a small business",
        "Build a real-time chat application",
        "Develop a task management system for teams with roles and due dates"
    ]
    print("🧪 TESTING ORGANIC MULTI-PERSPECTIVE INTELLIGENCE"); print("="*60)
    for i, p in enumerate(tests, 1):
        print(f"\n🔬 TEST {i}: {p}"); print("-"*40)
        state = orch.run_pipeline(p)
        tech_stack = state.get('tech_stack', [])
        print(f"\n🎭 TEAM'S ORGANIC CHOICES:")
        for t in tech_stack: print(f"   {t.get('role','?')}: {t.get('name','?')}")
        print("\n" + "="*60)

if __name__ == "__main__":
    test_organic_intelligence()
