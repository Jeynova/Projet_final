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
        sys_p = """You are a SENIOR PROJECT MANAGER defining a comprehensive delivery contract.

Analyze the chosen technology stack and required capabilities to create a COMPLETE production contract.

**MANDATORY BASELINE (all projects):**
- docker-compose.yml: Multi-service orchestration (backend, frontend, database, cache)
- .env.example: ALL environment variables with descriptions
- README.md: Professional documentation (quickstart ≤3 commands, API docs, deployment)
- /api/health: Health check with database connectivity verification
- /docs: Complete API documentation (Swagger/OpenAPI)
- Build automation: Makefile or package.json with dev/build/test/deploy scripts
- Development: .devcontainer/devcontainer.json for consistent development environment

**PRODUCTION REQUIREMENTS (expand based on complexity):**

For AUTHENTICATION projects:
- User registration, login, logout, password reset endpoints
- JWT token management and refresh
- Role-based access control middleware
- Password hashing and validation

For CRUD applications:
- Complete CRUD endpoints for all entities
- Input validation and sanitization
- Database models with relationships
- Migration scripts and seed data

For COMPLEX projects (e-commerce, social, enterprise):
- Admin panel interfaces and endpoints
- Payment processing integration
- File upload and media management
- Email notification systems
- Real-time features (WebSocket endpoints)
- Analytics and reporting endpoints
- Advanced search and filtering

**DATABASE CONTRACT:**
- All entity tables with proper relationships
- Indexes for performance optimization
- Migration files for schema management
- Seed data for development and testing

**INFRASTRUCTURE CONTRACT:**
- Docker multi-stage production builds
- CI/CD configuration (GitHub Actions/GitLab CI)
- Environment-specific configurations
- Monitoring and logging setup
- Security configurations (CORS, rate limiting)

Return COMPREHENSIVE JSON contract:
{{
  "files": ["ALL files needed for production deployment"],
  "endpoints": [{{"method":"GET|POST|PUT|DELETE","path":"/api/path","description":"purpose"}}],
  "tables": [{{"name":"table_name","purpose":"business_purpose"}}],
  "infrastructure": ["docker-compose.yml", ".env.example", "Dockerfile", "CI/CD configs"],
  "security": ["authentication endpoints", "middleware files", "security configs"],
  "documentation": ["README.md", "API docs", "deployment guides"],
  "testing": ["test files", "fixtures", "test configurations"]
}}

Aim for 20-50 files for moderate complexity, 50+ for complex projects.
Match file extensions to chosen tech stack. Be COMPREHENSIVE - this is the delivery contract."""
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

