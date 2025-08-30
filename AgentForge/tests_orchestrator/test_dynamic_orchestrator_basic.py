import os
from pathlib import Path
from orchestrator_v2.dynamic_orchestrator import DynamicOrchestrator
from orchestrator_v2.memory_store import MemoryStore


def test_basic_run(tmp_path):
    root = tmp_path / 'proj'
    root.mkdir()
    orch = DynamicOrchestrator(root, memory=MemoryStore())
    result = orch.run('Create a tiny api', 'mini')
    assert 'final_state' in result
    assert 'codegen' in result['final_state']
    assert isinstance(result.get('score'), (int, float))
    assert result['score'] >= 0
