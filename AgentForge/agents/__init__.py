# agents/__init__.py
"""Public agent API: easy imports, registry, and default pipeline wiring."""
from typing import Dict, Type, List

# Re-export individual agents (clean imports elsewhere)
from .memory.learning_memory import LearningMemoryAgent
from .team.multi_perspective import MultiPerspectiveTechAgent
from .team.stack_resolver import StackResolverAgent

from .product.capability import CapabilityAgent
from .product.contract import ContractAgent
from .product.contract_guard import ContractPresenceGuard
from .product.architecture import ArchitectureAgent
from .product.codegen import CodeGenAgent
from .product.database import DatabaseAgent
from .product.deployment import DeploymentAgent
from .product.validate import ValidateAgent
from .product.validation_router import ValidationRouter
from .product.evaluation import EvaluationAgent

__all__ = [
    # memory / team
    "LearningMemoryAgent",
    "MultiPerspectiveTechAgent",
    "StackResolverAgent",
    # product
    "CapabilityAgent",
    "ContractAgent",
    "ContractPresenceGuard",
    "ArchitectureAgent",
    "CodeGenAgent",
    "DatabaseAgent",
    "DeploymentAgent",
    "ValidateAgent",
    "ValidationRouter",
    "EvaluationAgent",
    # helpers
    "AGENT_CLASSES",
    "AGENT_REGISTRY",
    "load_default_pipeline",
]

# Ordered list used by your orchestrator (same order as your pipeline)
AGENT_CLASSES: List[Type] = [
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
]

# Quick lookup by agent id (e.g., "memory", "tech_team", "codegen", ...)
AGENT_REGISTRY: Dict[str, Type] = {cls.id: cls for cls in AGENT_CLASSES if hasattr(cls, "id")}

def load_default_pipeline(*, rag_store=None) -> List[object]:
    """
    Instantiate the default pipeline in the canonical order.
    Only LearningMemoryAgent needs rag_store; the rest have no required args.
    """
    return [
        LearningMemoryAgent(rag_store=rag_store),
        MultiPerspectiveTechAgent(),
        StackResolverAgent(),
        CapabilityAgent(),
        ContractAgent(),
        ContractPresenceGuard(),
        ArchitectureAgent(),
        CodeGenAgent(),
        DatabaseAgent(),
        DeploymentAgent(),
        ValidateAgent(),
        ValidationRouter(),
        EvaluationAgent(),
    ]