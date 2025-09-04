"""
Simple Graph-Based Pipeline
A simplified graph approach that maintains the successful patterns from enhanced_pipeline_v2
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class GraphState:
    """Shared state that flows through the graph"""
    prompt: str = ""
    project_name: str = ""
    iteration: int = 1
    max_iterations: int = 3
    target_score: float = 6.0
    best_score: float = 0.0
    
    # Generated content
    tech_stack: Dict[str, Any] = None
    architecture: Dict[str, Any] = None
    generated_code: Dict[str, str] = None
    validation_score: float = 0.0
    
    # Context and memory
    context: Dict[str, Any] = None
    memory_hints: str = ""
    refinement_notes: List[str] = None
    
    # Control flow
    should_iterate: bool = True
    is_complete: bool = False
    error: str = ""
    
    def __post_init__(self):
        if self.tech_stack is None:
            self.tech_stack = {}
        if self.architecture is None:
            self.architecture = {}
        if self.generated_code is None:
            self.generated_code = {}
        if self.context is None:
            self.context = {}
        if self.refinement_notes is None:
            self.refinement_notes = []


class GraphNode:
    """Base class for graph nodes"""
    def __init__(self, name: str, next_nodes: List[str] = None):
        self.name = name
        self.next_nodes = next_nodes or []
    
    def execute(self, state: GraphState) -> GraphState:
        """Execute this node and return updated state"""
        raise NotImplementedError
    
    def get_next_nodes(self, state: GraphState) -> List[str]:
        """Determine which nodes to execute next"""
        return self.next_nodes


class MemoryNode(GraphNode):
    """Learning and memory analysis"""
    def __init__(self):
        super().__init__("memory", ["debate"])
        from agents.memory.learning_memory import LearningMemoryAgent
        self.memory_agent = LearningMemoryAgent()
    
    def execute(self, state: GraphState) -> GraphState:
        print("🧠 Memory: Learning & analysis...")
        
        try:
            agent_state = {
                'prompt': state.prompt,
                'project_name': state.project_name,
                'iteration': state.iteration
            }
            
            if self.memory_agent.can_run(agent_state):
                memory_result = self.memory_agent.run(agent_state)
                if memory_result:
                    state.memory_hints = memory_result.get('experience_hints', '')
                    state.context.update(memory_result)
                    
        except Exception as e:
            print(f"⚠️ Memory node failed: {e}")
            
        return state


class DebateNode(GraphNode):
    """Team technology debate"""
    def __init__(self):
        super().__init__("debate", ["architecture"])
        from adaptaters.optimized_team_debate import OptimizedTeamDebate
        self.team_debate = OptimizedTeamDebate(demo_mode=False)
    
    def execute(self, state: GraphState) -> GraphState:
        print("🎭 Debate: Technology selection...")
        
        try:
            tech_decision = self.team_debate.run_smart_debate(
                state.prompt, 
                state.memory_hints
            )
            state.tech_stack = tech_decision.get('final_decision', {})
            state.context['team_debate_process'] = tech_decision.get('process', '')
            
        except Exception as e:
            print(f"❌ Debate failed: {e}")
            # Fallback
            state.tech_stack = {
                "backend": {"name": "Node.js", "reasoning": "Reliable choice"},
                "frontend": {"name": "React", "reasoning": "Popular framework"}, 
                "database": {"name": "PostgreSQL", "reasoning": "Solid database"}
            }
            
        return state


class ArchitectureNode(GraphNode):
    """Architecture design"""
    def __init__(self):
        super().__init__("architecture", ["generation"])
        from agents.product.architecture import ArchitectureAgent
        from agents.product.capability import CapabilityAgent
        from agents.product.contract import ContractAgent
        
        self.arch_agent = ArchitectureAgent()
        self.cap_agent = CapabilityAgent() 
        self.contract_agent = ContractAgent()
    
    def execute(self, state: GraphState) -> GraphState:
        print("🏗️ Architecture: System design...")
        
        # Build agent state
        agent_state = {
            'prompt': state.prompt,
            'tech_stack': state.tech_stack,
            'project_name': state.project_name
        }
        agent_state.update(state.context)
        
        try:
            # Capabilities
            if self.cap_agent.can_run(agent_state):
                cap_result = self.cap_agent.run(agent_state)
                if cap_result:
                    agent_state.update(cap_result)
                    state.context.update(cap_result)
            
            # Contract
            if self.contract_agent.can_run(agent_state):
                contract_result = self.contract_agent.run(agent_state)
                if contract_result:
                    agent_state.update(contract_result)
                    state.context.update(contract_result)
            
            # Architecture
            if self.arch_agent.can_run(agent_state):
                arch_result = self.arch_agent.run(agent_state)
                if arch_result:
                    state.architecture = arch_result.get('architecture', {})
                    state.context.update(arch_result)
                    
        except Exception as e:
            print(f"❌ Architecture failed: {e}")
            state.architecture = {"files": ["src/app.js", "src/api.js", "src/db.js"]}
            
        return state


class GenerationNode(GraphNode):
    """Progressive code generation"""
    def __init__(self):
        super().__init__("generation", ["validation"])
        from agents.product.progressive_codegen_v2 import ProgressiveCodeGenV2
        self.codegen_agent = ProgressiveCodeGenV2()
    
    def execute(self, state: GraphState) -> GraphState:
        print("⚡ Generation: Progressive code creation...")
        
        # Build comprehensive agent state
        agent_state = {
            'prompt': state.prompt,
            'project_name': state.project_name,
            'tech_stack': state.tech_stack,
            'architecture': state.architecture,
            'phase_name': 'code_generation',
            'max_codegen_iters': 1,
            'validation_threshold': 6.0
        }
        agent_state.update(state.context)
        
        try:
            if self.codegen_agent.can_run(agent_state):
                gen_result = self.codegen_agent.run(agent_state)
                if gen_result:
                    state.generated_code = gen_result.get('generated_code', {})
                    state.context.update(gen_result)
                    
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            state.error = str(e)
            
        return state


class ValidationNode(GraphNode):
    """Validation and scoring"""
    def __init__(self):
        super().__init__("validation", ["decision"])
        from agents.product.validate import ValidateAgent
        self.validate_agent = ValidateAgent()
    
    def execute(self, state: GraphState) -> GraphState:
        print("✅ Validation: Quality assessment...")
        
        agent_state = {
            'generated_code': state.generated_code,
            'architecture': state.architecture,
            'tech_stack': state.tech_stack,
            'prompt': state.prompt
        }
        agent_state.update(state.context)
        
        try:
            if self.validate_agent.can_run(agent_state):
                val_result = self.validate_agent.run(agent_state)
                if val_result:
                    final_validation = val_result.get('final_validation', {})
                    state.validation_score = final_validation.get('overall_score', 0)
                    state.context.update(val_result)
                    
        except Exception as e:
            print(f"⚠️ Validation failed: {e}")
            state.validation_score = 0
            
        return state


class DecisionNode(GraphNode):
    """Decision: iterate or complete"""
    def __init__(self):
        super().__init__("decision", [])  # Next nodes determined dynamically
    
    def execute(self, state: GraphState) -> GraphState:
        print(f"🎯 Decision: Score {state.validation_score}/10, iteration {state.iteration}/{state.max_iterations}")
        
        # Update best score
        if state.validation_score > state.best_score:
            state.best_score = state.validation_score
            print(f"✅ New best score: {state.best_score}/10")
        
        # Check completion conditions
        if state.validation_score >= state.target_score:
            print(f"🎉 TARGET ACHIEVED! {state.validation_score}/10 >= {state.target_score}/10")
            state.is_complete = True
            state.should_iterate = False
        elif state.iteration >= state.max_iterations:
            print(f"⏰ Max iterations reached ({state.max_iterations})")
            state.is_complete = True
            state.should_iterate = False
        else:
            print(f"🔄 Score {state.validation_score}/10 < target {state.target_score}/10. Iterating...")
            state.iteration += 1
            state.should_iterate = True
            # Add refinement context for next iteration
            state.refinement_notes.append(f"Iteration {state.iteration-1}: Score {state.validation_score}/10")
            
        return state
    
    def get_next_nodes(self, state: GraphState) -> List[str]:
        if state.should_iterate and not state.is_complete:
            return ["memory"]  # Start next iteration
        else:
            return ["save"]  # Complete and save


class SaveNode(GraphNode):
    """Save generated files"""
    def __init__(self, save_folder: str = "graph_generated"):
        super().__init__("save", [])
        self.save_folder = save_folder
    
    def execute(self, state: GraphState) -> GraphState:
        print("💾 Save: Writing files to disk...")
        
        output_dir = Path(self.save_folder)
        output_dir.mkdir(exist_ok=True)
        
        saved_count = 0
        for filename, content in state.generated_code.items():
            if isinstance(content, str) and content.strip():
                file_path = output_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    lines = len(content.split('\n'))
                    print(f"✅ Saved: {filename} ({lines} lines)")
                    saved_count += 1
                    
                except Exception as e:
                    print(f"❌ Failed to save {filename}: {e}")
        
        # Save metadata
        metadata = {
            'project_name': state.project_name,
            'prompt': state.prompt,
            'final_score': state.best_score,
            'iterations': state.iteration,
            'files_count': saved_count,
            'tech_stack': state.tech_stack,
            'architecture': state.architecture
        }
        
        with open(output_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📊 Saved {saved_count} files to: {output_dir.absolute()}")
        state.context['saved_files'] = saved_count
        state.context['output_dir'] = str(output_dir.absolute())
        
        return state


class SimpleGraphPipeline:
    """
    Simple Graph Pipeline - maintains all successful patterns from enhanced_pipeline_v2
    but uses a clear graph structure for easier understanding and modification
    """
    
    def __init__(self, save_folder: str = "graph_generated", max_iterations: int = 3, target_score: float = 6.0):
        self.save_folder = save_folder
        self.max_iterations = max_iterations
        self.target_score = target_score
        
        # Initialize nodes
        self.nodes = {
            "memory": MemoryNode(),
            "debate": DebateNode(), 
            "architecture": ArchitectureNode(),
            "generation": GenerationNode(),
            "validation": ValidationNode(),
            "decision": DecisionNode(),
            "save": SaveNode(save_folder)
        }
        
        print("🚀 Simple Graph Pipeline initialized:")
        print("   📊 Graph structure: Memory → Debate → Architecture → Generation → Validation → Decision")
        print("   🔄 Iterative refinement with graph loops")
        print("   💾 Progressive code generation (from enhanced_pipeline_v2)")
        print(f"   🎯 Target score: {target_score}/10")
        print(f"   🔁 Max iterations: {max_iterations}")
    
    def run(self, prompt: str, project_name: str = "GraphProject") -> Dict[str, Any]:
        """Run the graph pipeline"""
        
        print(f"\n🚀 GRAPH PIPELINE: {prompt[:50]}...")
        
        # Initialize state
        state = GraphState(
            prompt=prompt,
            project_name=project_name,
            max_iterations=self.max_iterations,
            target_score=self.target_score
        )
        
        # Execute graph starting from memory node
        current_nodes = ["memory"]
        visited_path = []
        
        while current_nodes and not state.is_complete:
            # Execute current nodes
            next_nodes = []
            
            for node_name in current_nodes:
                if node_name not in self.nodes:
                    print(f"❌ Unknown node: {node_name}")
                    continue
                
                visited_path.append(f"{node_name}({state.iteration})")
                
                # Execute node
                try:
                    node = self.nodes[node_name]
                    state = node.execute(state)
                    
                    # Get next nodes
                    node_next = node.get_next_nodes(state)
                    next_nodes.extend(node_next)
                    
                except Exception as e:
                    print(f"❌ Node {node_name} failed: {e}")
                    state.error = f"{node_name}: {str(e)}"
                    break
            
            current_nodes = list(set(next_nodes))  # Remove duplicates
            
            # Safety check to prevent infinite loops
            if len(visited_path) > self.max_iterations * 10:
                print("⚠️ Safety break: too many node executions")
                break
        
        print(f"\n🎯 GRAPH COMPLETE!")
        print(f"📊 Final Score: {state.best_score}/10")
        print(f"🔄 Iterations: {state.iteration}")
        print(f"📁 Files Generated: {len(state.generated_code)}")
        print(f"🛤️ Execution Path: {' → '.join(visited_path)}")
        
        return {
            'best_validation_score': state.best_score,
            'generated_code': state.generated_code,
            'final_iteration_count': state.iteration,
            'achieved_target': state.best_score >= state.target_score,
            'execution_path': visited_path,
            'project_metadata': state.context,
            'output_dir': state.context.get('output_dir', ''),
            'saved_files_count': state.context.get('saved_files', 0)
        }


def create_simple_graph_pipeline(save_folder: str = "graph_generated") -> SimpleGraphPipeline:
    """Factory function to create the graph pipeline"""
    return SimpleGraphPipeline(save_folder=save_folder)


if __name__ == "__main__":
    # Quick test
    pipeline = create_simple_graph_pipeline("test_graph")
    result = pipeline.run("Create a simple task API with user authentication")
    print(f"Test complete! Score: {result['best_validation_score']}/10")
