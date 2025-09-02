#!/usr/bin/env python3
"""
🎯 REACTIVE ORCHESTRATOR
Event/queue loop pipeline for organic intelligence
"""

import tempfile
from pathlib import Path
from typing import Dict, Any

# Import all agents
from agents.memory.learning_memory import LearningMemoryAgent
from agents.team.multi_perspective import MultiPerspectiveTechAgent
from agents.team.stack_resolver import StackResolverAgent
from agents.product.capability import CapabilityAgent
from agents.product.contract import ContractAgent
from agents.product.contract_guard import ContractPresenceGuard
from agents.product.architecture import ArchitectureAgent
from agents.product.codegen import CodeGenAgent
from agents.product.database import DatabaseAgent
from agents.product.deployment import DeploymentAgent
from agents.product.validate import ValidateAgent
from agents.product.validation_router import ValidationRouter
from agents.product.evaluation import EvaluationAgent

# Import utilities
from core.scheduling import schedule_agents


# ──────────────────────────────────────────────────────────────────────────────
# 🎯 REACTIVE ORCHESTRATOR (event/queue loop)
# ──────────────────────────────────────────────────────────────────────────────
class PureIntelligenceOrchestrator:
    """LLM-only contract + validation pipeline with reactive agent scheduling"""
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
        # registry by id and by class name (for ValidationRouter)
        self.registry = {a.id: a for a in self.agents}
        for a in self.agents:
            self.registry[a.__class__.__name__] = a
        self.learning_memory = self.agents[0]

    def run_pipeline(self, prompt: str) -> Dict[str, Any]:
        print(f"🎭 PURE INTELLIGENCE PIPELINE: {prompt[:50]}...")
        state = {
            'prompt': prompt,
            'max_codegen_iters': 4,
            'validation_threshold': 7,
            'file_contract_mode': 'guided',
            'events': [],
            'next_agents': ['memory','tech_team','stack_resolver','capabilities','contract','contract_guard','architecture','codegen','database','deployment','validate','ValidationRouter','evaluation']
        }

        step, max_steps = 0, 60
        while state.get('next_agents') and step < max_steps and not state.get('goal_reached', False):
            step += 1
            agent_id = state['next_agents'].pop(0)
            agent = self.registry.get(agent_id)
            if not agent:
                continue
            try:
                if agent.can_run(state):
                    print(f"\n🔄 Running {agent.__class__.__name__}")
                    result = agent.run(state) or {}
                    # merge state
                    state.update(result)
                    # schedule follow-ups returned by agent
                    if 'next_agents' in result:
                        schedule_agents(state, result['next_agents'], front=False)
                else:
                    # silently skip if conditions not met
                    pass
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