"""
AgentForge Agentic System

Clean, modular implementation of multi-agent collaboration system.
"""

from .simple_agentic_graph import SimpleAgenticGraph
from .agents.base_agent import BaseAgent, SimpleAgent
from .memory.memory_agent import MemoryAgent

__version__ = "2.0.0"
__all__ = ["SimpleAgenticGraph", "BaseAgent", "SimpleAgent", "MemoryAgent"]
