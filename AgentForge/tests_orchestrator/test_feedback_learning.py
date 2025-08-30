from orchestrator_v2.memory_store import MemoryStore


def test_feedback_adjusts_success_rate(tmp_path):
    m = MemoryStore(tmp_path / 'mem.json')
    # Simulate at least one invocation to establish baseline stats
    m.record_agent_invocation('codegen', True)
    before = m.success_rate('codegen')
    m.apply_feedback(['codegen','architecture'], final_score=90, baseline=50)
    after = m.success_rate('codegen')
    assert after >= before
