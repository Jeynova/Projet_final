# agentforge/core/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class Agent(ABC):
    id: str = "agent"
    @abstractmethod
    def can_run(self, state: Dict[str, Any]) -> bool: ...
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]: ...

def track_llm_call(agent: str, operation: str):
    print(f"🔄 {agent} → {operation}")

class LLMBackedMixin:
    def __init__(self, llm_client=None):
        from core.llm_client import LLMClient
        self.llm_client = llm_client or LLMClient()
    def llm_json(self, system_prompt, user_prompt, fallback):
        try:
            r = self.llm_client.extract_json(system_prompt, user_prompt)
            return {**fallback, **r} if isinstance(r, dict) and r else fallback
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return fallback
