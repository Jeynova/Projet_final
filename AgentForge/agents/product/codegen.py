#!/usr/bin/env python3
"""
💾 CODE GENERATION AGENT
Intelligent multi-language generation
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call
from core.contracts import is_contract_empty


# ──────────────────────────────────────────────────────────────────────────────
# 💾 CODE GENERATION AGENT
# ──────────────────────────────────────────────────────────────────────────────
class CodeGenAgent(LLMBackedMixin):
    id = "codegen"
    def can_run(self, state):
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
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
        coach_notes = state.get('coach_notes', [])

        # Memory coaching block
        mem = state.get('memory_policy', {}) or {}
        prefer = ", ".join(str(p) for role_prefs in mem.get('prefer', {}).values() for p in (role_prefs if isinstance(role_prefs, list) else []))
        avoid  = ", ".join(str(a) for role_avoids in mem.get('avoid', {}).values() for a in (role_avoids if isinstance(role_avoids, list) else []))
        coach  = "\n".join(f"- {n}" for n in state.get('coach_notes', []))

        memory_block = f"""
### MEMORY COACHING
Prefer: {prefer or '—'}
Avoid: {avoid or '—'}
Coaching:
{coach or '—'}
"""

        # draft a minimal contract inline if still missing
        if is_contract_empty(contract):
            print("🛠️ CodeGen: no contract provided → drafting minimal contract inline.")
            sys_cp = """Propose a minimal CONTRACT (files/endpoints/tables) suitable for immediate implementation with the chosen stack.
Include docker-compose.yml, .env.example, README.md, /api/health, /docs.
Return STRICT JSON like:
{"files":["backend/app.*","frontend/src/App.*","docker-compose.yml",".env.example","README.md"],"endpoints":[{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],"tables":[{"name":"users"}]}"""
            user_cp = f"STACK:\n{tech_stack}\nARCHITECTURE:\n{architecture}\nKeep ≤ 20 files."
            mini = self.llm_json(sys_cp, user_cp, {"files":["backend/app.js","frontend/src/App.js","docker-compose.yml",".env.example","README.md"],"endpoints":[{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],"tables":[{"name":"users"}]})
            mini['source'] = 'codegen_inline'
            contract = mini

        system_prompt = f"""You are a SENIOR FULL-STACK ARCHITECT. Generate COMPLETE, PRODUCTION-READY applications.

CRITICAL REQUIREMENTS:
- COMPREHENSIVE implementation (50-200+ lines per file)
- Full authentication & authorization systems
- Complete error handling & logging
- Input validation & sanitization  
- Database models with relationships
- API endpoints with full CRUD operations
- Responsive UI with state management
- Security middleware (CORS, helmet, rate limiting)
- Environment configuration
- Docker containerization
- Comprehensive documentation
- Test suites and fixtures

QUALITY STANDARDS:
- Code should be IMMEDIATELY DEPLOYABLE
- Include ALL necessary files for production
- Generate 15-35 files minimum for moderate complexity
- Each file should contain COMPLETE, WORKING implementation
- No placeholders or "TODO" comments

Return STRICT JSON:
{{
  "files": {{"path":"complete_working_code", "...":"..."}},
  "setup_instructions": ["detailed_setup_steps"],
  "run_commands": ["actual_run_commands"],
  "deployment_notes": ["production_deployment_guide"]
}}"""

        fb = []
        if prior_issues or suggestions: fb += [*prior_issues[:5], *suggestions[:5]]
        if missing_files: fb.append("Missing files last iteration: " + ", ".join(missing_files[:20]))
        if missing_eps:   fb.append("Missing endpoints last iteration: " + ", ".join(missing_eps[:20]))
        feedback_block = ("\n\nFix these before anything else:\n- " + "\n- ".join(fb)) if fb else ""

        targeted_files = state.get('contract_missing_files', [])
        targeted_eps   = state.get('contract_missing_endpoints', [])
        target_block = ""
        if targeted_files or targeted_eps:
            target_block = "\n\n# TARGETED FIXES\n" + \
                (f"- Implement missing files: {', '.join(targeted_files[:20])}\n" if targeted_files else "") + \
                (f"- Implement missing endpoints: {', '.join(targeted_eps[:20])}\n" if targeted_eps else "")

        contract_block = ""
        if contract:
            req_files = "\n".join(f"- {p}" for p in (contract.get('files') or [])[:60])
            
            # Handle endpoints safely - could be list of dicts or list of strings
            endpoints = contract.get('endpoints') or []
            req_eps_list = []
            for e in endpoints[:60]:
                if isinstance(e, dict):
                    # Standard format: {"method": "GET", "path": "/api/health"}
                    method = e.get('method', 'GET')
                    path = e.get('path', '')
                    req_eps_list.append(f"- {method} {path}")
                elif isinstance(e, str):
                    # String format: "GET /api/health" or just "/api/health"
                    req_eps_list.append(f"- {e}")
                else:
                    req_eps_list.append(f"- {str(e)}")
            req_eps = "\n".join(req_eps_list)
            
            # Handle tables safely
            tables = contract.get('tables') or []
            req_tabs_list = []
            for t in tables[:40]:
                if isinstance(t, dict):
                    req_tabs_list.append(f"- {t.get('name', str(t))}")
                else:
                    req_tabs_list.append(f"- {str(t)}")
            req_tabs = "\n".join(req_tabs_list)
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

        user_prompt = f"""SENIOR ARCHITECT TASK: Build a COMPLETE production application

PROJECT: {prompt}

🎯 TECHNOLOGY STACK DECISIONS:
{chr(10).join([f"- {t.get('role','?')}: {t.get('name','?')} (Rationale: {t.get('reasoning','')})" for t in tech_stack])}

🏗️ DETAILED ARCHITECTURE REQUIREMENTS:
Project Structure: {architecture.get('project_structure',{})}
Core Components: {', '.join(architecture.get('key_components',[]))}
Required Files: {len(architecture.get('required_files', []))} minimum
Data Flow: {architecture.get('data_flow', 'Not specified')}

{memory_block}

🎯 PRODUCTION REQUIREMENTS - IMPLEMENT ALL:

**AUTHENTICATION & SECURITY:**
- Complete JWT-based auth system (login, register, logout, password reset)
- Role-based access control with middleware
- Input validation and sanitization on all endpoints
- CORS configuration, rate limiting, helmet security headers
- Password hashing with bcrypt/argon2

**DATABASE & MODELS:**
- Complete data models with relationships and constraints
- Database migrations and seed data
- Connection pooling and error handling
- Transaction management for complex operations

**API LAYER:**
- Full CRUD operations for all entities
- RESTful endpoints with proper HTTP status codes  
- Request/response validation with schemas
- Error handling middleware with structured responses
- API documentation (OpenAPI/Swagger)
- Health check and monitoring endpoints

**FRONTEND (if applicable):**
- Complete responsive UI with state management
- Loading states, error boundaries, notifications
- Form validation and user feedback
- Routing and navigation
- Component library with reusable elements

**INFRASTRUCTURE:**
- Docker multi-stage builds for production
- Environment configuration (.env files)
- Logging with structured output (Winston/Python logging)
- Error tracking and performance monitoring
- CI/CD configuration files

**TESTING & QUALITY:**
- Unit tests for core business logic
- Integration tests for API endpoints
- Test fixtures and mock data
- Code coverage reporting

**DEPLOYMENT:**
- Production-ready docker-compose.yml
- Kubernetes manifests (if complex)
- Environment-specific configurations
- Deployment scripts and documentation

MEMORY COACHING (implement these specific patterns):
{chr(10).join([f"- {note}" for note in coach_notes[:8]])}
{target_block}

{contract_block}{strict_line}{feedback_block}

🚀 IMPLEMENTATION STANDARDS:
- Each file should be 50-200+ lines of complete, working code
- NO placeholders, TODOs, or incomplete implementations
- Generate 15-35+ files for moderate complexity projects
- Include comprehensive error handling and logging
- Use production-quality patterns and best practices
- Code should be immediately deployable

CRITICAL: This is a SENIOR DEVELOPER task. Generate production-ready applications that teams can deploy immediately."""
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

        # Stack guard: fail fast if LLM generates wrong stack
        files = result.get('files', {}) or {}
        chosen = (backend.get('name','') or '').lower()
        is_node = 'node' in chosen or 'express' in chosen
        is_python = 'python' in chosen or 'django' in chosen or 'flask' in chosen

        found_py = any(k.startswith('backend/') and k.endswith('.py') for k in files.keys())
        found_js_ts = any(k.startswith('backend/') and (k.endswith('.js') or k.endswith('.ts')) for k in files.keys())

        if (is_node and found_py) or (is_python and found_js_ts):
            print("🛑 CodeGen stack guard tripped → regenerating to match chosen backend")
            return {'redo_codegen': True, 'generated_code': state.get('generated_code', {}), 'codegen_iters': state.get('codegen_iters',0)}

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
