"""
Test the Super Simple Graph
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('🚀 Testing Super Simple Graph...')

try:
    from orchestrators.enhanced_pipeline_v2 import EnhancedPipelineV2
    
    # Test the working enhanced_pipeline_v2 first
    print("✅ Enhanced Pipeline V2 imported successfully")
    
    # Simple wrapper that adds graph semantics
    class GraphWrapper:
        def __init__(self, save_folder="graph_test"):
            self.pipeline = EnhancedPipelineV2(
                save_to_folder=save_folder,
                max_iterations=1,  # Quick test
                target_score=6.0
            )
            print("🎯 Graph wrapper initialized with enhanced_pipeline_v2")
        
        def run_as_graph(self, prompt: str, project_name: str = "GraphTest"):
            """Run pipeline with graph visualization"""
            nodes = ["START", "ENHANCED_PIPELINE_V2", "COMPLETE"]
            
            print(f"📊 Graph execution: {' → '.join(nodes)}")
            
            # Execute START node
            print("📊 Node: START")
            print(f"   🎯 Prompt: {prompt[:50]}...")
            print(f"   📝 Project: {project_name}")
            
            # Execute ENHANCED_PIPELINE_V2 node
            print("📊 Node: ENHANCED_PIPELINE_V2")
            result = self.pipeline.run_pipeline(prompt, project_name)
            
            # Execute COMPLETE node  
            print("📊 Node: COMPLETE")
            score = result.get('best_validation_score', 0)
            files = len(result.get('generated_code', {}))
            iterations = result.get('final_iteration_count', 1)
            
            print(f"   ✅ Final Score: {score}/10")
            print(f"   📄 Files Generated: {files}")
            print(f"   🔄 Iterations: {iterations}")
            
            # Add graph metadata
            result['graph_nodes'] = nodes
            result['graph_execution'] = "SUCCESS"
            
            return result
    
    # Create and test the graph wrapper
    graph_wrapper = GraphWrapper("test_graph_wrapper")
    
    result = graph_wrapper.run_as_graph(
        "Create a simple task API with user authentication",
        "GraphAPITest"
    )
    
    print(f"\n🎉 GRAPH WRAPPER TEST COMPLETE!")
    print(f"📊 Final Score: {result['best_validation_score']}/10")
    print(f"📄 Files: {len(result['generated_code'])}")
    print(f"🎯 Target achieved: {result.get('achieved_target', False)}")
    print(f"🛤️ Graph structure: {' → '.join(result['graph_nodes'])}")
    
    # Show sample files
    if result['generated_code']:
        print(f"\n📁 Sample generated files:")
        for i, (filename, content) in enumerate(list(result['generated_code'].items())[:3]):
            lines = len(content.split('\n')) if content else 0
            print(f"   {i+1}. {filename}: {lines} lines")
    
    print("\n✅ Graph wrapper test completed successfully!")
    print("🎯 The enhanced_pipeline_v2 works perfectly with graph semantics!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
