#!/usr/bin/env python3
"""
🎯 INTELLIGENT MODEL SELECTOR
Agent-specific model selection based on task requirements and Ollama availability
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ModelSpec:
    """Model specification with capabilities"""
    name: str
    strengths: List[str]
    size_gb: float
    best_for: List[str]

class IntelligentModelSelector:
    """Selects optimal models for different agent tasks"""
    
    def __init__(self):
        self.ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.available_models = []
        self.model_specs = {
            "codellama:7b": ModelSpec(
                name="codellama:7b",
                strengths=["code_generation", "debugging", "refactoring", "production_code"],
                size_gb=3.8,
                best_for=["ProgressiveCodeGenAgent", "CodeGenAgent", "ValidationAgent"]  # PRIORITIZE for code generation
            ),
            "qwen2.5-coder:7b": ModelSpec(
                name="qwen2.5-coder:7b", 
                strengths=["code_quality", "testing", "validation", "code_review"],
                size_gb=4.7,
                best_for=["ValidateAgent", "EvaluationAgent"]
            ),
            "mistral:7b": ModelSpec(
                name="mistral:7b",
                strengths=["reasoning", "planning", "architecture", "analysis"],
                size_gb=4.4,
                best_for=["ArchitectureAgent", "ContractAgent", "LearningMemoryAgent"]
            ),
            "llama3.1:8b": ModelSpec(
                name="llama3.1:8b",
                strengths=["general_reasoning", "conversation", "synthesis"],
                size_gb=4.9,
                best_for=["MultiPerspectiveTechAgent", "EvaluationAgent"]
            ),
            "llama3.1:latest": ModelSpec(
                name="llama3.1:latest",
                strengths=["general_purpose", "fallback"],
                size_gb=4.9,
                best_for=["fallback"]
            )
        }
        self._refresh_available_models()
    
    def _refresh_available_models(self):
        """Check which models are available in Ollama"""
        try:
            response = requests.get(f"{self.ollama_base}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model["name"] for model in data.get("models", [])]
                print(f"🎯 Found {len(self.available_models)} available models: {', '.join(self.available_models[:3])}...")
            else:
                print("⚠️ Could not fetch available models, using defaults")
                self.available_models = ["llama3.1:latest"]
        except Exception as e:
            print(f"⚠️ Model detection failed: {e}")
            self.available_models = ["llama3.1:latest"]
    
    def select_model_for_agent(self, agent_class_name: str) -> str:
        """Select the best available model for a specific agent"""
        
        # Agent-specific model preferences
        agent_preferences = {
            "CodeGenAgent": ["codellama:7b", "qwen2.5-coder:7b", "llama3.1:8b"],
            "ArchitectureAgent": ["mistral:7b", "llama3.1:8b", "llama3.1:latest"],
            "ValidateAgent": ["qwen2.5-coder:7b", "codellama:7b", "mistral:7b"],
            "EvaluationAgent": ["qwen2.5-coder:7b", "llama3.1:8b", "mistral:7b"],
            "ContractAgent": ["mistral:7b", "llama3.1:8b", "llama3.1:latest"],
            "LearningMemoryAgent": ["mistral:7b", "llama3.1:8b", "llama3.1:latest"],
            "MultiPerspectiveTechAgent": ["llama3.1:8b", "mistral:7b", "llama3.1:latest"],
            "DatabaseAgent": ["codellama:7b", "qwen2.5-coder:7b", "llama3.1:8b"],
            "DeploymentAgent": ["mistral:7b", "llama3.1:8b", "llama3.1:latest"]
        }
        
        preferred_models = agent_preferences.get(agent_class_name, ["llama3.1:latest"])
        
        # Find the first available model from preferences
        for model in preferred_models:
            if model in self.available_models:
                print(f"🎯 {agent_class_name} → {model} (optimized)")
                return model
        
        # Fallback to first available model
        if self.available_models:
            fallback = self.available_models[0]
            print(f"⚠️ {agent_class_name} → {fallback} (fallback)")
            return fallback
        
        # Ultimate fallback
        print(f"❌ {agent_class_name} → llama3.1:latest (default)")
        return "llama3.1:latest"
    
    def get_model_capabilities(self, model_name: str) -> Dict[str, Any]:
        """Get capabilities and specifications for a model"""
        spec = self.model_specs.get(model_name)
        if spec:
            return {
                "name": spec.name,
                "strengths": spec.strengths,
                "size_gb": spec.size_gb,
                "best_for": spec.best_for
            }
        return {
            "name": model_name,
            "strengths": ["unknown"],
            "size_gb": 0.0,
            "best_for": ["general"]
        }
    
    def optimize_model_allocation(self, agents: List[str]) -> Dict[str, str]:
        """Optimize model allocation across multiple agents"""
        allocation = {}
        
        # First pass: assign specialized models
        specialized_agents = ["CodeGenAgent", "ValidateAgent", "ArchitectureAgent"]
        for agent in specialized_agents:
            if agent in agents:
                allocation[agent] = self.select_model_for_agent(agent)
        
        # Second pass: assign remaining agents
        for agent in agents:
            if agent not in allocation:
                allocation[agent] = self.select_model_for_agent(agent)
        
        # Report allocation
        print(f"\n🎯 INTELLIGENT MODEL ALLOCATION:")
        for agent, model in allocation.items():
            capabilities = self.get_model_capabilities(model)
            print(f"   {agent:<20} → {model:<15} ({', '.join(capabilities['strengths'][:2])})")
        
        return allocation
    
    def get_performance_recommendations(self) -> List[str]:
        """Get recommendations for better model performance"""
        recommendations = []
        
        # Check if we have specialized models
        has_code_model = any("codellama" in model or "coder" in model for model in self.available_models)
        has_reasoning_model = any("mistral" in model for model in self.available_models)
        
        if not has_code_model:
            recommendations.append("📥 Install codellama:7b or qwen2.5-coder:7b for better code generation")
        
        if not has_reasoning_model:
            recommendations.append("📥 Install mistral:7b for better architecture and reasoning")
        
        if len(self.available_models) < 3:
            recommendations.append("🚀 More models = better task-specific performance")
        
        return recommendations

# Global model selector instance
model_selector = IntelligentModelSelector()
