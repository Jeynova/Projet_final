"""
Test script for the clean agentic system
"""

import sys
import os
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

# Test imports
try:
    from agentic.simple_agentic_graph import SimpleAgenticGraph
    from agentic.agents.base_agent import SimpleAgent
    from agentic.memory.memory_agent import MemoryAgent
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_agentic_system():
    """Test the clean agentic system"""
    
    print("\n🧪 Testing Clean Agentic System...")
    
    # Test 1: Create system
    try:
        agentic = SimpleAgenticGraph("test_clean_output")
        print("✅ System creation successful")
    except Exception as e:
        print(f"❌ System creation failed: {e}")
        return False
    
    # Test 2: Memory agent
    try:
        memory_stats = agentic.memory_agent.get_memory_stats()
        print(f"✅ Memory agent working: {memory_stats['total_patterns']} patterns")
    except Exception as e:
        print(f"❌ Memory agent failed: {e}")
        return False
    
    # Test 3: Agent stats
    try:
        stats = agentic.get_agent_stats()
        print(f"✅ Agent stats working: {len(stats)} agents")
    except Exception as e:
        print(f"❌ Agent stats failed: {e}")
        return False
    
    # Test 4: Small generation pipeline
    try:
        print("\n🚀 Running small pipeline test...")
        result = agentic.run_agentic_pipeline(
            "Simple Python calculator app",
            "test_calculator"
        )
        
        if result['success']:
            print(f"✅ Pipeline successful: {result['files_generated']} files generated")
            print(f"   Score: {result['overall_score']}/10")
        else:
            print("❌ Pipeline failed")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Clean agentic system is working.")
    return True

if __name__ == "__main__":
    # Set environment variable for testing
    os.environ['AGENTFORGE_LLM'] = 'ollama'
    
    success = test_agentic_system()
    
    if success:
        print("\n🎯 Ready for production use!")
        print("   - Use: python agentic/simple_agentic_graph.py")
        print("   - Or:  python agentic/webapp/app_agentic.py")
    else:
        print("\n❌ Tests failed. Check configuration.")
        sys.exit(1)
