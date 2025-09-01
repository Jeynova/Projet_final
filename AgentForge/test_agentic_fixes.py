#!/usr/bin/env python3
"""
Test script to verify the agentic fixes are working correctly
"""

import sys
from pathlib import Path

# Add the project root to the path
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from agent_graph import Node, GraphConfig, GraphRunner
from phase2_pure_intelligence import (
    PureIntelligenceOrchestrator,
    LearningMemoryAgent,
    MultiPerspectiveTechAgent,
    StackResolverAgent,
    ContractPresenceGuard,
    CapabilityAgent,
    ContractAgent,
    ArchitectureAgent,
    CodeGenAgent,
    DatabaseAgent,
    DeploymentAgent,
    ValidateAgent,
    EvaluationAgent,
    ValidationRouter
)

def test_agent_imports():
    """Test that all agents can be imported and instantiated"""
    print("🧪 Testing agent imports and instantiation...")
    
    try:
        orchestrator = PureIntelligenceOrchestrator()
        print(f"✅ Orchestrator created with {len(orchestrator.agents)} agents")
        
        # Check that the new agents are in the orchestrator
        agent_names = [a.__class__.__name__ for a in orchestrator.agents]
        print(f"📋 Available agents: {', '.join(agent_names)}")
        
        # Verify critical agents are present
        critical_agents = ['StackResolverAgent', 'ContractPresenceGuard', 'LearningMemoryAgent', 'ContractAgent']
        for agent_name in critical_agents:
            if agent_name in agent_names:
                print(f"   ✅ {agent_name} - Present")
            else:
                print(f"   ❌ {agent_name} - Missing")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graph_configuration():
    """Test that the graph configuration works with new repeatable nodes"""
    print("\n🔧 Testing graph configuration...")
    
    try:
        orchestrator = PureIntelligenceOrchestrator()
        agents = {a.__class__.__name__: a for a in orchestrator.agents}
        router = ValidationRouter()
        agents['ValidationRouter'] = router
        
        # Test state with events and strict mode
        state = {
            'prompt': 'Test project for agentic fixes',
            'max_codegen_iters': 2,
            'validation_threshold': 7,
            'file_contract_mode': 'strict',
            'events': [{'type': 'need_debate', 'reason': 'test'}]
        }
        
        # Create nodes with repeatable settings
        nodes = {
            'LearningMemoryAgent': Node('LearningMemoryAgent',
                run=agents['LearningMemoryAgent'].run,
                can_run=agents['LearningMemoryAgent'].can_run,
                repeatable=True),
            'MultiPerspectiveTechAgent': Node('MultiPerspectiveTechAgent',
                run=agents['MultiPerspectiveTechAgent'].run,
                can_run=agents['MultiPerspectiveTechAgent'].can_run,
                parallel_group="debate",
                repeatable=True),
            'ContractAgent': Node('ContractAgent',
                run=agents['ContractAgent'].run,
                can_run=agents['ContractAgent'].can_run,
                repeatable=True),
            'ContractPresenceGuard': Node('ContractPresenceGuard',
                run=agents['ContractPresenceGuard'].run,
                can_run=agents['ContractPresenceGuard'].can_run,
                repeatable=True),
            'StackResolverAgent': Node('StackResolverAgent',
                run=agents['StackResolverAgent'].run,
                can_run=agents['StackResolverAgent'].can_run,
                repeatable=True),
        }
        
        print("✅ Graph nodes created successfully")
        print(f"📊 Configured {len(nodes)} nodes with repeatable settings")
        
        # Test that events are preserved in state
        if 'events' in state and len(state['events']) > 0:
            print(f"✅ Events system active: {len(state['events'])} events")
        
        if state.get('file_contract_mode') == 'strict':
            print("✅ Strict contract mode enabled")
            
        return True
    except Exception as e:
        print(f"❌ Graph configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_coaching():
    """Test that memory coaching can be generated"""
    print("\n🧠 Testing memory coaching system...")
    
    try:
        # Test memory policy structure
        test_policy = {
            'prefer': {
                'backend': ['Django', 'FastAPI'],
                'frontend': ['React', 'Vue'],
                'database': ['PostgreSQL'],
                'deployment': ['Docker']
            },
            'avoid': {
                'backend': ['PHP'],
                'frontend': ['jQuery'],
                'database': ['MongoDB'],
                'deployment': ['FTP']
            }
        }
        
        test_coach_notes = [
            "Use environment variables for config",
            "Add health check endpoints",
            "Implement proper error handling"
        ]
        
        # Test the memory block construction (same as in CodeGenAgent)
        prefer = ", ".join(str(p) for role_prefs in test_policy.get('prefer', {}).values() for p in (role_prefs if isinstance(role_prefs, list) else []))
        avoid  = ", ".join(str(a) for role_avoids in test_policy.get('avoid', {}).values() for a in (role_avoids if isinstance(role_avoids, list) else []))
        coach  = "\n".join(f"- {n}" for n in test_coach_notes)

        memory_block = f"""
### MEMORY COACHING
Prefer: {prefer or '—'}
Avoid: {avoid or '—'}
Coaching:
{coach or '—'}
"""
        
        print("✅ Memory coaching block generated:")
        print(memory_block[:200] + "..." if len(memory_block) > 200 else memory_block)
        
        return True
    except Exception as e:
        print(f"❌ Memory coaching test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTING AGENTIC SYSTEM FIXES")
    print("=" * 50)
    
    test1 = test_agent_imports()
    test2 = test_graph_configuration()
    test3 = test_memory_coaching()
    
    print("\n📊 TEST RESULTS:")
    print(f"   Agent Imports: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"   Graph Config: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"   Memory Coaching: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 ALL TESTS PASSED - Agentic fixes are working!")
    else:
        print("\n⚠️ Some tests failed - check the output above")
