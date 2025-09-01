#!/usr/bin/env python3
"""
Test to verify agentic loop with events works correctly
"""

import sys
from pathlib import Path

# Add the project root to the path
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

def test_agentic_event_flow():
    """Test that events trigger proper agent re-runs"""
    print("🧪 Testing agentic event flow...")
    
    from phase2_pure_intelligence import LearningMemoryAgent, ValidateAgent, ValidationRouter
    
    # Test 1: LearningMemory can_run with events
    memory = LearningMemoryAgent()
    
    # Initial run - should work
    state1 = {'prompt': 'test project'}
    assert memory.can_run(state1) == True, "❌ Memory should run initially"
    print("✅ Memory can_run: initial run works")
    
    # After initial run - should not run
    state2 = {'prompt': 'test project', 'memory': True}
    assert memory.can_run(state2) == False, "❌ Memory should not run again without events"
    print("✅ Memory can_run: blocks re-run without events")
    
    # With validation_completed event - should run again
    state3 = {
        'prompt': 'test project', 
        'memory': True,
        'events': ['validation_completed'],
        'memory_after_validation_done': False
    }
    assert memory.can_run(state3) == True, "❌ Memory should run on validation_completed event"
    print("✅ Memory can_run: triggers on validation_completed event")
    
    # With refinement event - should run again
    state4 = {
        'prompt': 'test project', 
        'memory': True,
        'events': ['refinement_triggered'],
        'memory_after_validation_done': False
    }
    assert memory.can_run(state4) == True, "❌ Memory should run on refinement_triggered event"
    print("✅ Memory can_run: triggers on refinement_triggered event")
    
    # After memory runs and sets the flag - should not run again
    state5 = {
        'prompt': 'test project', 
        'memory': True,
        'events': ['validation_completed'],
        'memory_after_validation_done': True
    }
    assert memory.can_run(state5) == False, "❌ Memory should not thrash after handling event"
    print("✅ Memory can_run: prevents thrashing with flag")
    
    # Test 2: ValidateAgent returns events
    validate = ValidateAgent()
    mock_state = {
        'generated_code': {'files': {'test.js': 'console.log("test");'}},
        'tech_stack': [{'role': 'backend', 'name': 'Node.js'}],
        'codegen_iters': 1,
        'last_validated_iter': 0,
        'events': []
    }
    
    # Mock the LLM call to return a simple validation
    def mock_llm_json(self, sys_prompt, user_prompt, fallback):
        return {
            'status': 'issues', 'score': 5, 'technical_score': 5, 
            'security_score': 5, 'architecture_score': 5, 'ux_score': 5,
            'issues': ['test issue'], 'suggestions': [], 'strengths': [],
            'missing_files': [], 'missing_endpoints': [], 'missing_baseline': [],
            'coverage': {'files_percent': 60, 'endpoints_percent': 50}
        }
    
    validate.llm_json = mock_llm_json.__get__(validate, ValidateAgent)
    
    result = validate.run(mock_state)
    assert 'validation_completed' in result.get('events', []), "❌ ValidateAgent should emit validation_completed event"
    print("✅ ValidateAgent: emits validation_completed event")
    
    # Test 3: ValidationRouter returns events on refinement
    router = ValidationRouter()
    router_state = {
        'validation': {'score': 5, 'status': 'issues'},
        'last_validated_iter': 1,
        'routed_after_iter': 0,
        'validation_threshold': 7,
        'max_codegen_iters': 4,
        'events': []
    }
    
    router_result = router.run(router_state)
    assert 'refinement_triggered' in router_result.get('events', []), "❌ ValidationRouter should emit refinement_triggered event"
    print("✅ ValidationRouter: emits refinement_triggered event")
    
    return True

if __name__ == "__main__":
    print("🚀 TESTING AGENTIC EVENT FLOW")
    print("=" * 50)
    
    try:
        success = test_agentic_event_flow()
        if success:
            print("\n🎉 ALL AGENTIC TESTS PASSED!")
            print("💡 The learn → teach → act loop is now fully wired")
        else:
            print("\n⚠️ Some tests failed")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
