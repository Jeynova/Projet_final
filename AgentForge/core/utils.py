# agentforge/core/utils.py
"""
⚠️ DEPRECATED: Contract utilities moved to core/contracts.py
Import from core.contracts instead
"""

# Re-export for backward compatibility
from .contracts import is_contract_empty, merge_contract

__all__ = ['is_contract_empty', 'merge_contract']
