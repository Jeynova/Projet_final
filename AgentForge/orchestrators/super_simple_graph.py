"""
Super Simple Graph Pipeline
Uses the working enhanced_pipeline_v2 but adds graph visualization and control
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass 
class GraphState:
    """Simple state for graph execution"""
    prompt: str
    project_name: str
    iteration: int = 1
    max_iterations: int = 3
    target_score: float = 6.0
    result: Dict[str, Any] = None
    is_complete: bool = False


class SuperSimpleGraph:
    """
    Super Simple Graph that wraps the successful enhanced_pipeline_v2
    Adds graph structure and visualization while keeping all the working logic
    """
    
    def __init__(self, save_folder: str = "super_simple_generated", max_iterations: int = 2, target_score: float = 6.0):
        self.save_folder = save_folder
        self.max_iterations = max_iterations
        self.target_score = target_score
        
        # Import the working pipeline
        from orchestrators.enhanced_pipeline_v2 import EnhancedPipelineV2
        self.pipeline = EnhancedPipelineV2(
            save_to_folder=save_folder,
            max_iterations=max_iterations,
            target_score=target_score
        )
        
        print("🚀 Super Simple Graph initialized:")
        print("   📊 Graph: Start → Enhanced Pipeline V2 → Complete")
        print("   💾 All successful patterns from enhanced_pipeline_v2 maintained")
        print(f"   🎯 Target score: {target_score}/10")
        print(f"   🔁 Max iterations: {max_iterations}")
        print(f"   💾 Save folder: {save_folder}")
    
    def start_node(self, state: GraphState) -> GraphState:
        """Initialize and start the process"""
        print(f"🚀 START: {state.prompt[:50]}...")
        print(f"📝 Project: {state.project_name}")
        return state
    
    def pipeline_node(self, state: GraphState) -> GraphState:
        """Execute the enhanced pipeline"""
        print("⚡ PIPELINE: Running enhanced_pipeline_v2...")
        
        try:
            # Run the working pipeline
            result = self.pipeline.run_pipeline(
                state.prompt, 
                state.project_name
            )
            
            state.result = result
            state.is_complete = True
            
            print(f"✅ Pipeline completed successfully!")
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            state.result = {'error': str(e), 'best_validation_score': 0, 'generated_code': {}}
            state.is_complete = True
        
        return state
    
    def complete_node(self, state: GraphState) -> GraphState:
        """Final completion and summary"""
        result = state.result or {}
        score = result.get('best_validation_score', 0)
        files_count = len(result.get('generated_code', {}))
        iterations = result.get('final_iteration_count', 1)
        
        print(f"🏁 COMPLETE!")
        print(f"   📊 Final Score: {score}/10")
        print(f"   📄 Files Generated: {files_count}")
        print(f"   🔄 Iterations: {iterations}")
        print(f"   🎯 Target Achieved: {score >= self.target_score}")
        
        return state
    
    def run(self, prompt: str, project_name: str = "SuperSimpleProject") -> Dict[str, Any]:
        """Run the super simple graph"""
        
        print(f"\n🚀 SUPER SIMPLE GRAPH: {prompt[:50]}...")
        
        # Initialize state
        state = GraphState(
            prompt=prompt,
            project_name=project_name,
            max_iterations=self.max_iterations,
            target_score=self.target_score
        )
        
        # Execute graph nodes in sequence
        execution_path = []
        
        try:
            # Node 1: Start
            execution_path.append("start")
            state = self.start_node(state)
            
            # Node 2: Pipeline (the magic happens here)
            execution_path.append("pipeline")
            state = self.pipeline_node(state)
            
            # Node 3: Complete
            execution_path.append("complete")
            state = self.complete_node(state)
            
        except Exception as e:
            print(f"❌ Graph execution failed: {e}")
            execution_path.append("error")
            
        # Extract results
        result = state.result or {}
        
        print(f"\n🎉 GRAPH EXECUTION COMPLETE!")
        print(f"🛤️ Execution Path: {' → '.join(execution_path)}")
        
        # Add graph metadata to result
        result['graph_execution_path'] = execution_path
        result['graph_project_name'] = state.project_name
        
        return result


def create_super_simple_graph(save_folder: str = "super_simple_generated") -> SuperSimpleGraph:
    """Factory function"""
    return SuperSimpleGraph(save_folder=save_folder)


# Alternative: Even simpler direct wrapper
class MinimalGraphWrapper:
    """Minimal graph wrapper - just adds graph semantics to enhanced_pipeline_v2"""
    
    def __init__(self, save_folder: str = "minimal_graph"):
        from orchestrators.enhanced_pipeline_v2 import EnhancedPipelineV2
        self.pipeline = EnhancedPipelineV2(save_to_folder=save_folder)
        self.save_folder = save_folder
        
        print("🎯 MINIMAL GRAPH: Enhanced Pipeline V2 with graph wrapper")
    
    def run_graph(self, prompt: str, project_name: str = "MinimalProject") -> Dict[str, Any]:
        """Run as graph with visualization"""
        nodes_executed = []
        
        print(f"📊 Graph Node: START")
        nodes_executed.append("start")
        
        print(f"📊 Graph Node: ENHANCED_PIPELINE_V2")  
        nodes_executed.append("enhanced_pipeline_v2")
        result = self.pipeline.run_pipeline(prompt, project_name)
        
        print(f"📊 Graph Node: COMPLETE")
        nodes_executed.append("complete")
        
        result['graph_nodes_executed'] = nodes_executed
        result['graph_structure'] = "START → ENHANCED_PIPELINE_V2 → COMPLETE"
        
        return result


if __name__ == "__main__":
    # Test both versions
    print("Testing Super Simple Graph...")
    
    graph = create_super_simple_graph("test_super_simple")
    result = graph.run("Create a simple API", "TestAPI")
    print(f"Result: {result.get('best_validation_score', 0)}/10")
    
    print("\n" + "="*50)
    print("Testing Minimal Graph Wrapper...")
    
    minimal = MinimalGraphWrapper("test_minimal") 
    result2 = minimal.run_graph("Create a simple API", "MinimalAPI")
    print(f"Result: {result2.get('best_validation_score', 0)}/10")
