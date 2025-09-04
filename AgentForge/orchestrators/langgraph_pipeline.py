"""
LangGraph Version - Using proper LangGraph for graph execution
Requires: pip install langgraph
"""

try:
    from langgraph.graph import Graph
    from langgraph.checkpoint.memory import MemorySaver
    from typing_extensions import TypedDict
except ImportError:
    print("❌ LangGraph not installed. Run: pip install langgraph")
    print("📄 Using simplified graph instead...")
    from .simple_graph_pipeline import SimpleGraphPipeline
    
    class LangGraphPipeline:
        def __init__(self, save_folder="langgraph_generated"):
            self.simple_pipeline = SimpleGraphPipeline(save_folder)
        
        def run(self, prompt: str, project_name: str = "LangGraphProject"):
            return self.simple_pipeline.run(prompt, project_name)
else:
    from typing import Dict, Any, List
    import json
    from pathlib import Path


    class AgentState(TypedDict):
        """LangGraph state definition"""
        prompt: str
        project_name: str
        iteration: int
        max_iterations: int
        target_score: float
        best_score: float
        
        # Generated content
        tech_stack: Dict[str, Any]
        architecture: Dict[str, Any] 
        generated_code: Dict[str, str]
        validation_score: float
        
        # Control
        should_iterate: bool
        is_complete: bool
        messages: List[str]


    class LangGraphPipeline:
        """LangGraph implementation of the successful pipeline"""
        
        def __init__(self, save_folder: str = "langgraph_generated"):
            self.save_folder = save_folder
            self.setup_agents()
            self.build_graph()
        
        def setup_agents(self):
            """Initialize all agents"""
            from agents.memory.learning_memory import LearningMemoryAgent
            from adaptaters.optimized_team_debate import OptimizedTeamDebate
            from agents.product.architecture import ArchitectureAgent
            from agents.product.capability import CapabilityAgent
            from agents.product.contract import ContractAgent
            from agents.product.progressive_codegen_v2 import ProgressiveCodeGenV2
            from agents.product.validate import ValidateAgent
            
            self.memory_agent = LearningMemoryAgent()
            self.team_debate = OptimizedTeamDebate(demo_mode=False)
            self.arch_agent = ArchitectureAgent()
            self.cap_agent = CapabilityAgent()
            self.contract_agent = ContractAgent()
            self.codegen_agent = ProgressiveCodeGenV2()
            self.validate_agent = ValidateAgent()
        
        def memory_node(self, state: AgentState) -> AgentState:
            """Memory and learning analysis"""
            print("🧠 LangGraph: Memory analysis...")
            
            try:
                agent_state = {
                    'prompt': state['prompt'],
                    'project_name': state['project_name']
                }
                
                if self.memory_agent.can_run(agent_state):
                    result = self.memory_agent.run(agent_state)
                    if result:
                        # Store hints in messages for next nodes
                        hints = result.get('experience_hints', '')
                        state['messages'].append(f"MEMORY_HINTS: {hints}")
                        
            except Exception as e:
                state['messages'].append(f"MEMORY_ERROR: {str(e)}")
            
            return state
        
        def debate_node(self, state: AgentState) -> AgentState:
            """Technology debate"""
            print("🎭 LangGraph: Team debate...")
            
            try:
                # Extract memory hints
                memory_hints = ""
                for msg in state['messages']:
                    if msg.startswith("MEMORY_HINTS:"):
                        memory_hints = msg.replace("MEMORY_HINTS:", "").strip()
                        break
                
                tech_decision = self.team_debate.run_smart_debate(
                    state['prompt'], memory_hints
                )
                state['tech_stack'] = tech_decision.get('final_decision', {})
                
            except Exception as e:
                state['messages'].append(f"DEBATE_ERROR: {str(e)}")
                # Fallback
                state['tech_stack'] = {
                    "backend": {"name": "Node.js", "reasoning": "Default choice"},
                    "frontend": {"name": "React", "reasoning": "Default choice"}
                }
            
            return state
        
        def architecture_node(self, state: AgentState) -> AgentState:
            """Architecture design"""
            print("🏗️ LangGraph: Architecture design...")
            
            agent_state = {
                'prompt': state['prompt'],
                'tech_stack': state['tech_stack'],
                'project_name': state['project_name']
            }
            
            try:
                # Capabilities
                if self.cap_agent.can_run(agent_state):
                    cap_result = self.cap_agent.run(agent_state)
                    if cap_result:
                        agent_state.update(cap_result)
                
                # Contract
                if self.contract_agent.can_run(agent_state):
                    contract_result = self.contract_agent.run(agent_state)
                    if contract_result:
                        agent_state.update(contract_result)
                
                # Architecture
                if self.arch_agent.can_run(agent_state):
                    arch_result = self.arch_agent.run(agent_state)
                    if arch_result:
                        state['architecture'] = arch_result.get('architecture', {})
                        
            except Exception as e:
                state['messages'].append(f"ARCH_ERROR: {str(e)}")
                state['architecture'] = {"files": ["src/app.js", "src/api.js"]}
            
            return state
        
        def generation_node(self, state: AgentState) -> AgentState:
            """Code generation"""
            print("⚡ LangGraph: Code generation...")
            
            agent_state = {
                'prompt': state['prompt'],
                'project_name': state['project_name'],
                'tech_stack': state['tech_stack'],
                'architecture': state['architecture'],
                'phase_name': 'code_generation'
            }
            
            try:
                if self.codegen_agent.can_run(agent_state):
                    gen_result = self.codegen_agent.run(agent_state)
                    if gen_result:
                        state['generated_code'] = gen_result.get('generated_code', {})
                        
            except Exception as e:
                state['messages'].append(f"GEN_ERROR: {str(e)}")
            
            return state
        
        def validation_node(self, state: AgentState) -> AgentState:
            """Validation"""
            print("✅ LangGraph: Validation...")
            
            agent_state = {
                'generated_code': state['generated_code'],
                'architecture': state['architecture'],
                'tech_stack': state['tech_stack'],
                'prompt': state['prompt']
            }
            
            try:
                if self.validate_agent.can_run(agent_state):
                    val_result = self.validate_agent.run(agent_state)
                    if val_result:
                        final_validation = val_result.get('final_validation', {})
                        state['validation_score'] = final_validation.get('overall_score', 0)
                        
            except Exception as e:
                state['messages'].append(f"VAL_ERROR: {str(e)}")
                state['validation_score'] = 0
            
            return state
        
        def decision_node(self, state: AgentState) -> AgentState:
            """Decision logic"""
            print(f"🎯 LangGraph: Decision - Score {state['validation_score']}/10")
            
            # Update best score
            if state['validation_score'] > state['best_score']:
                state['best_score'] = state['validation_score']
            
            # Check completion
            if state['validation_score'] >= state['target_score']:
                print(f"🎉 Target achieved: {state['validation_score']}/10")
                state['is_complete'] = True
                state['should_iterate'] = False
            elif state['iteration'] >= state['max_iterations']:
                print(f"⏰ Max iterations reached")
                state['is_complete'] = True
                state['should_iterate'] = False
            else:
                print(f"🔄 Iterating... ({state['iteration']}/{state['max_iterations']})")
                state['iteration'] += 1
                state['should_iterate'] = True
            
            return state
        
        def save_node(self, state: AgentState) -> AgentState:
            """Save files"""
            print("💾 LangGraph: Saving files...")
            
            output_dir = Path(self.save_folder)
            output_dir.mkdir(exist_ok=True)
            
            saved_count = 0
            for filename, content in state['generated_code'].items():
                if isinstance(content, str) and content.strip():
                    file_path = output_dir / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        saved_count += 1
                        print(f"✅ Saved: {filename}")
                    except Exception as e:
                        print(f"❌ Failed to save {filename}: {e}")
            
            # Save metadata
            metadata = {
                'project_name': state['project_name'],
                'prompt': state['prompt'],
                'final_score': state['best_score'],
                'iterations': state['iteration'],
                'files_count': saved_count
            }
            
            with open(output_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📊 Saved {saved_count} files to: {output_dir.absolute()}")
            return state
        
        def should_continue(self, state: AgentState) -> str:
            """Routing logic for the graph"""
            if state['is_complete']:
                return "save"
            elif state['should_iterate']:
                return "memory"  # Loop back for next iteration
            else:
                return "save"
        
        def build_graph(self):
            """Build the LangGraph workflow"""
            
            # Create graph
            workflow = Graph()
            
            # Add nodes
            workflow.add_node("memory", self.memory_node)
            workflow.add_node("debate", self.debate_node)
            workflow.add_node("architecture", self.architecture_node)
            workflow.add_node("generation", self.generation_node)
            workflow.add_node("validation", self.validation_node)
            workflow.add_node("decision", self.decision_node)
            workflow.add_node("save", self.save_node)
            
            # Add edges
            workflow.add_edge("memory", "debate")
            workflow.add_edge("debate", "architecture") 
            workflow.add_edge("architecture", "generation")
            workflow.add_edge("generation", "validation")
            workflow.add_edge("validation", "decision")
            
            # Conditional edge for iteration
            workflow.add_conditional_edges(
                "decision",
                self.should_continue,
                {
                    "memory": "memory",  # Continue iteration
                    "save": "save"       # Complete
                }
            )
            
            # Set entry point
            workflow.set_entry_point("memory")
            
            # Compile
            self.graph = workflow.compile(checkpointer=MemorySaver())
        
        def run(self, prompt: str, project_name: str = "LangGraphProject") -> Dict[str, Any]:
            """Run the LangGraph pipeline"""
            
            print(f"🚀 LANGGRAPH PIPELINE: {prompt[:50]}...")
            
            # Initial state
            initial_state = {
                "prompt": prompt,
                "project_name": project_name,
                "iteration": 1,
                "max_iterations": 3,
                "target_score": 6.0,
                "best_score": 0.0,
                "tech_stack": {},
                "architecture": {},
                "generated_code": {},
                "validation_score": 0.0,
                "should_iterate": True,
                "is_complete": False,
                "messages": []
            }
            
            # Execute graph
            config = {"configurable": {"thread_id": "1"}}
            final_state = self.graph.invoke(initial_state, config)
            
            print(f"\n🎉 LANGGRAPH COMPLETE!")
            print(f"📊 Final Score: {final_state['best_score']}/10")
            print(f"📁 Files: {len(final_state['generated_code'])}")
            
            return {
                'best_validation_score': final_state['best_score'],
                'generated_code': final_state['generated_code'],
                'final_iteration_count': final_state['iteration'],
                'achieved_target': final_state['best_score'] >= final_state['target_score'],
                'messages': final_state['messages']
            }


def create_langgraph_pipeline(save_folder: str = "langgraph_generated") -> LangGraphPipeline:
    """Factory function"""
    return LangGraphPipeline(save_folder)
