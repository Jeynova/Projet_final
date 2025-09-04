#!/usr/bin/env python3
"""
🗄️ DATABASE AGENT
Schema design and optimization
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call


# ──────────────────────────────────────────────────────────────────────────────
# 🗄️ DATABASE AGENT
# ──────────────────────────────────────────────────────────────────────────────
class DatabaseAgent(LLMBackedMixin):
    id = "database"
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
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
