#!/usr/bin/env python3
"""
🛡️ CONTRACT PRESENCE GUARD
Ensure contract exists before codegen
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call
from core.contracts import is_contract_empty


# ──────────────────────────────────────────────────────────────────────────────
# 🛡️ CONTRACT PRESENCE GUARD (ensure contract exists before codegen)
# ──────────────────────────────────────────────────────────────────────────────
class ContractPresenceGuard(LLMBackedMixin):
    id = "contract_guard"
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        if 'tech_stack' not in state: return False
        return ('contract' not in state) or is_contract_empty(state.get('contract', {}))
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
        
        contract['source'] = 'guard'
        print("🛡️ ContractPresenceGuard: drafted minimal contract.")
        return {"contract": contract}