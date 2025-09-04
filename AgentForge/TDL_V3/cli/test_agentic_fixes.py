# intelligent_orchestrator.py
"""
Agent-selection facade:
- Decides which agents (and parameters) to use (fast/strict/dev)
- Builds the pipeline and delegates execution to pipeline.PureIntelligenceOrchestrator
- Lightweight “policy” that can evolve without touching the execution engine
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

# execution engine (multi-pass loop, materialization, best snapshot, etc.)
from pipeline import PureIntelligenceOrchestrator, OrchestratorConfig as EngineConfig

# agents “barrel”
from agents import (
    LearningMemoryAgent,
    MultiPerspectiveTechAgent,
    StackResolverAgent,
    CapabilityAgent,
    ContractAgent,
    ContractPresenceGuard,
    ArchitectureAgent,
    CodeGenAgent,
    DatabaseAgent,
    DeploymentAgent,
    ValidateAgent,
    ValidationRouter,
    EvaluationAgent,
)

# ──────────────────────────────────────────────────────────────────────────────
# Selection config
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SelectionConfig:
    """High-level knobs for the selection layer (orthogonal to engine config)."""
    mode: str = "strict"        # "strict" | "fast" | "dev"
    use_team_debate: bool = True
    use_stack_resolver: bool = True
    include_contract_guard: bool = True
    max_codegen_iters: int = 4
    validation_threshold: int = 7
    file_contract_mode: str = "strict"  # 'free'|'guided'|'strict'


# ──────────────────────────────────────────────────────────────────────────────
# Policy: choose agents + engine config from prompt/mode
# ──────────────────────────────────────────────────────────────────────────────

class AgentSelectionPolicy:
    def choose(
        self,
        prompt: str,
        cfg: SelectionConfig,
        *,
        rag_store: Optional[object] = None,
    ) -> Dict[str, Any]:
        """
        Returns:
          {
            'agents': [agent instances in order],
            'engine_config': EngineConfig,
            'initial_state': dict   # seeded into the engine's state
          }
        """
        # Base list (always start with memory to annotate state early)
        agents: List[object] = [LearningMemoryAgent(rag_store)]

        # Optional “thinking” agents
        if cfg.use_team_debate:
            agents.append(MultiPerspectiveTechAgent())
        if cfg.use_stack_resolver:
            agents.append(StackResolverAgent())

        # Capability → contract → guard
        agents.extend([
            CapabilityAgent(),
            ContractAgent(),
        ])
        if cfg.include_contract_guard:
            agents.append(ContractPresenceGuard())

        # Build → Validate → Route → Evaluate
        agents.extend([
            ArchitectureAgent(),
            CodeGenAgent(),
            DatabaseAgent(),
            DeploymentAgent(),
            ValidateAgent(),
            ValidationRouter(),
            EvaluationAgent(),
        ])

        # Heuristic tweaks based on prompt (non-binding; easy to extend)
        p = (prompt or "").lower()
        if "prototype" in p or "poC" in p or cfg.mode == "fast":
            # faster loop, lower bar, guided contract
            engine_conf = EngineConfig(
                max_outer_loops=3,
                validation_threshold=6,
                max_codegen_iters=min(cfg.max_codegen_iters, 3),
                file_contract_mode="guided",
                stop_on_first_valid=True,
            )
        elif cfg.mode == "dev":
            # relaxed, good for local hacking
            engine_conf = EngineConfig(
                max_outer_loops=6,
                validation_threshold=6,
                max_codegen_iters=cfg.max_codegen_iters,
                file_contract_mode="guided",
                stop_on_first_valid=False,  # let it iterate a bit more
            )
        else:
            # strict (default)
            engine_conf = EngineConfig(
                max_outer_loops=6,
                validation_threshold=cfg.validation_threshold,
                max_codegen_iters=cfg.max_codegen_iters,
                file_contract_mode=cfg.file_contract_mode,
                stop_on_first_valid=True,
            )

        initial_state = {
            "file_contract_mode": engine_conf.file_contract_mode,
            "validation_threshold": engine_conf.validation_threshold,
            "max_codegen_iters": engine_conf.max_codegen_iters,
        }

        return {
            "agents": agents,
            "engine_config": engine_conf,
            "initial_state": initial_state,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Facade orchestrator: public API
# ──────────────────────────────────────────────────────────────────────────────

class IntelligentOrchestrator:
    """
    Public facade:
      - Applies selection policy
      - Instantiates the execution engine with chosen agents/config
      - Delegates run/materialize
    """
    def __init__(
        self,
        *,
        selection_config: Optional[SelectionConfig] = None,
        rag_store: Optional[object] = None,
        logger=None,
    ) -> None:
        self.selection_config = selection_config or SelectionConfig()
        self.policy = AgentSelectionPolicy()
        self.rag_store = rag_store
        self.logger = logger

        # placeholders (filled on first run)
        self._engine: Optional[PureIntelligenceOrchestrator] = None

    def run(self, prompt: str, *, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pick = self.policy.choose(prompt, self.selection_config, rag_store=self.rag_store)
        agents = pick["agents"]
        engine_conf: EngineConfig = pick["engine_config"]

        # (Re)build engine when needed (e.g., config changed)
        self._engine = PureIntelligenceOrchestrator(
            agents=agents,
            config=engine_conf,
            rag_store=self.rag_store,
            logger=self.logger,
        )

        # merge initial state overrides
        merged_initial = {**pick["initial_state"], **(initial_state or {})}

        return self._engine.run(prompt, initial_state=merged_initial)

    def materialize_project(
        self,
        state: Dict[str, Any],
        *,
        project_name: str = "web-boilerplate",
        output_dir: Optional[str] = None,
        prefer_best: bool = True,
    ) -> str:
        if not self._engine:
            # create a default engine to reuse its materializer
            self._engine = PureIntelligenceOrchestrator()
        return self._engine.materialize_project(
            state,
            project_name=project_name,
            output_dir=output_dir,
            prefer_best=prefer_best,
        )