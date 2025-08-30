"""Agent abstractions for orchestrator_v2.

Minimal interface to keep things simple & extensible.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Protocol
import hashlib, json
from pathlib import Path

class Agent(Protocol):
    id: str
    def can_run(self, state: Dict[str, Any]) -> bool: ...
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]: ...

@dataclass
class AgentResult:
    agent_id: str
    success: bool
    output: Dict[str, Any]
    skipped: bool = False

class LLMBackedMixin:
    def llm_json(self, system: str, user: str, fallback: Dict[str, Any]):
        # Simple deterministic cache based on hash of system+user
        cache_file = Path(__file__).parent / "llm_cache.json"
        key_src = (system + "\n" + user)[:5000]
        key = hashlib.sha256(key_src.encode()).hexdigest()[:24]
        cache: Dict[str, Any] = {}
        if cache_file.exists():
            try:
                cache = json.loads(cache_file.read_text())
            except Exception:
                cache = {}
        if key in cache:
            print(f"        🔄 Using cached LLM response for {key[:8]}...")
            return cache[key]
        try:
            from core.llm_client import LLMClient  # lazy import
            if not hasattr(self, "_llm"):
                self._llm = LLMClient()
            print(f"        🤖 Calling LLM for {key[:8]}...")
            res = self._llm.extract_json(system_prompt=system, user_prompt=user)
            print(f"        ✅ LLM response: {str(res)[:100]}...")
            if isinstance(res, dict) and res:
                cache[key] = res
                try:
                    cache_file.write_text(json.dumps(cache, indent=2))
                except Exception:
                    pass
                return res
        except Exception as e:
            print(f"        ❌ LLM error: {e}")
            return fallback
        print(f"        ⚠️  LLM returned empty, using fallback")
        return fallback
