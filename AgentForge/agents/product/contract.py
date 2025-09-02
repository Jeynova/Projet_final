#!/usr/bin/env python3
"""
📐 CONTRACT AGENT
LLM proposes files/endpoints/tables - rerunnable + merge
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call
from core.contracts import merge_contract
from core.events import has_event_type, filter_events_by_type


# ──────────────────────────────────────────────────────────────────────────────
# 📐 CONTRACT AGENT (LLM proposes files/endpoints/tables) — rerunnable + merge
# ──────────────────────────────────────────────────────────────────────────────
class ContractAgent(LLMBackedMixin):
    id = "contract"
    def __init__(self): super().__init__()
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        # Use standardized event checking
        events = state.get('events', [])
        needs_redo = state.get('redo_contract', False) or has_event_type(events, 'expand_contract')
        
        return (('contract' not in state) or needs_redo) and ('capabilities' in state) and ('tech_stack' in state)
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("📐 ContractAgent", "derive delivery contract")
        _ = state.pop('redo_contract', False)
        
        # clear expand_contract event if present - use standardized event filtering
        state['events'] = filter_events_by_type(state.get('events', []), 'expand_contract')

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
        proposed = self.llm_json(sys_p, user_p, fallback)
        proposed['source'] = 'llm'
        existing = state.get('contract', {})
        contract = merge_contract(existing, proposed) if existing else proposed
        
        # Force baseline into every contract
        required = {
            "files": [
                "docker-compose.yml",".env.example","README.md","Makefile",
                "scripts/dev.sh","scripts/build.sh","scripts/test.sh",
                "frontend/src/App.*","backend/app.*"
            ],
            "endpoints": [{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}]
        }
        
        files = set(contract.get('files', []))
        files.update(required["files"])
        endpoints = { (e["method"], e["path"]) for e in contract.get('endpoints', []) }
        for e in required["endpoints"]:
            endpoints.add((e["method"], e["path"]))
        contract["files"] = sorted(files)
        contract["endpoints"] = [{"method":m,"path":p} for (m,p) in sorted(endpoints)]
        
        print(f"📐 ContractAgent: merged → {len(contract.get('files',[]))} files, {len(contract.get('endpoints',[]))} endpoints")
        return {"contract": contract}

