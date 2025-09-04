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
    def __init__(self, llm_client=None, agent_class_name=None):
        from core.llm_client import LLMClient
        from core.model_selector import model_selector
        
        # Determine agent class name for model selection
        if agent_class_name is None:
            agent_class_name = self.__class__.__name__
        
        # Select optimal model for this agent
        optimal_model = model_selector.select_model_for_agent(agent_class_name)
        
        # Create specialized LLM client for this agent
        self.llm_client = llm_client or LLMClient(preferred_model=optimal_model)
        self.agent_class_name = agent_class_name
        self.assigned_model = optimal_model
        self.forced_model = None
        
    def force_model(self, model_name: str):
        """Force a specific model for this agent (for retry logic)"""
        self.forced_model = model_name
        self.llm_client.preferred_model = model_name
        
    def get_optimal_model(self) -> str:
        """Get the optimal model for this agent"""
        return self.assigned_model
        
    def llm_json(self, system_prompt, user_prompt, fallback, challenge_with_models=True):
        try:
            # Enhanced prompting for specialized models
            if "codellama" in self.assigned_model or "coder" in self.assigned_model:
                # Code-focused prompting
                system_prompt = f"You are an expert code architect. {system_prompt}"
            elif "mistral" in self.assigned_model:
                # Reasoning-focused prompting  
                system_prompt = f"You are a senior system architect with deep reasoning capabilities. {system_prompt}"
            
            r = self.llm_client.extract_json(system_prompt, user_prompt)
            return {**fallback, **r} if isinstance(r, dict) and r else fallback
        except Exception as e:
            print(f"⚠️ {self.agent_class_name} LLM call failed with {self.assigned_model}: {e}")
            return fallback
