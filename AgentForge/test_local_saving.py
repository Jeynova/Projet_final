#!/usr/bin/env python3
"""
Test script for Simple Agentic Graph with local file saving
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent
sys.path.append(str(ROOT))

from simple_agentic_graph import SimpleAgenticGraph

def test_local_saving():
    """Test the agentic graph with local file saving"""
    
    print("🧪 TESTING LOCAL FILE SAVING")
    print("=" * 50)
    
    # Create agentic graph (will save to local_output/)
    graph = SimpleAgenticGraph()
    
    # Test prompt
    prompt = "Create a simple task management API with authentication"
    
    print(f"\n🚀 Testing with prompt: {prompt}")
    print(f"📁 Will save to: {graph.save_folder}")
    
    # Run the agentic generation
    result = graph.run_agentic(prompt, "TestTaskAPI")
    
    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"📊 Generated {result['files_count']} files")
        print(f"📁 Saved to: {graph.save_folder}/TestTaskAPI")
        print(f"🧠 Memory patterns: {result.get('memory_stats', {}).get('total_patterns', 0)}")
        
        # List generated files
        print(f"\n📄 Generated Files:")
        for filename in result['files'].keys():
            print(f"   - {filename}")
        
        # Check if files actually exist
        save_path = Path(graph.save_folder) / "TestTaskAPI"
        if save_path.exists():
            actual_files = list(save_path.rglob("*.py")) + list(save_path.rglob("*.js")) + list(save_path.rglob("*.json"))
            print(f"\n📂 Actual files on disk: {len(actual_files)}")
            for file_path in actual_files:
                print(f"   - {file_path.name}")
        else:
            print(f"⚠️ Save directory not found: {save_path}")
            
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    test_local_saving()
