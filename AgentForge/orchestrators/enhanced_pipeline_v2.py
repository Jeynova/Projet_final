# orchestrators/enhanced_pipeline_v2.py
from typing import Dict, Any
from agents.memory.learning_memory import LearningMemoryAgent
from agents.product.architecture import ArchitectureAgent
from agents.product.progressive_codegen_v2 import ProgressiveCodeGenV2  # New modular version
from agents.product.validate import ValidateAgent
from agents.product.capability import CapabilityAgent
from agents.product.contract import ContractAgent
from adaptaters.optimized_team_debate import OptimizedTeamDebate
import json

class EnhancedPipelineV2:
    """
    Enhanced Super-LLM Pipeline V2 with:
    - Optimized team debate (different models for different roles)
    - Progressive code generation with component validation
    - Iterative refinement until acceptable results
    - Proper file saving and extraction
    """
    
    def __init__(self, rag_store=None, save_to_folder="gen2_files", 
                 max_iterations=3, target_score=7.0):
        self.learning_memory = LearningMemoryAgent(rag_store)
        self.save_folder = save_to_folder
        self.team_debate = OptimizedTeamDebate()
        self.max_iterations = max_iterations
        self.target_score = target_score
        
        self.agents = [
            self.learning_memory,
            CapabilityAgent(),
            ContractAgent(),
            ArchitectureAgent(), 
            ProgressiveCodeGenV2(),  # New modular progressive agent
            ValidateAgent()
        ]
        
        print("🚀 Enhanced Super-LLM Pipeline V2 initialized:")
        print("   🎭 Optimized team debate (multi-model)")
        print("   🏗️ Progressive code generation")
        print("   ✅ Component-wise validation")
        print("   🔄 Iterative refinement until acceptable results")
        print("   💾 Proper file extraction and saving")
        print(f"   🎯 Target quality score: {target_score}/10")
        print(f"   🔁 Max refinement iterations: {max_iterations}")
    
    def run_pipeline(self, prompt: str, project_name: str = None) -> Dict[str, Any]:
        """Run the enhanced pipeline with iterative refinement until acceptable results"""
        
        print(f"🚀 ENHANCED PIPELINE V2: {prompt[:50]}...")
        
        best_result = None
        best_score = 0.0
        iteration_history = []
        
        for iteration in range(1, self.max_iterations + 1):
            print(f"\n🔄 === ITERATION {iteration}/{self.max_iterations} ===")
            
            # Initialize state with previous context if available
            state = {
                'prompt': prompt,
                'project_name': project_name or 'generated_project',
                'max_codegen_iters': 1,
                'validation_threshold': 6.0,
                'iteration': iteration,
                'previous_attempts': iteration_history
            }
            
            try:
                # Run the pipeline phases
                state = self._run_pipeline_phases(state)
                
                # Evaluate results
                final_score = state.get('best_validation_score', 0)
                final_validation = state.get('final_validation', {})
                overall_score = final_validation.get('overall_score', final_score)
                
                print(f"📊 Iteration {iteration} Score: {overall_score}/10")
                
                # Track this attempt
                iteration_history.append({
                    'iteration': iteration,
                    'score': overall_score,
                    'issues': final_validation.get('critical_issues', []),
                    'files_generated': len(state.get('generated_code', {}))
                })
                
                # Check if this is the best result so far
                if overall_score > best_score:
                    best_result = state.copy()
                    best_score = overall_score
                    print(f"✅ New best result! Score: {best_score}/10")
                
                # Check if we've reached acceptable quality
                if overall_score >= self.target_score:
                    print(f"🎉 TARGET ACHIEVED! Score {overall_score}/10 >= {self.target_score}/10")
                    best_result = state
                    break
                    
                elif iteration < self.max_iterations:
                    print(f"🔄 Score {overall_score}/10 < target {self.target_score}/10. Refining...")
                    # Add refinement context for next iteration
                    self._add_refinement_context(state, iteration_history)
                    
            except Exception as e:
                print(f"❌ Iteration {iteration} failed: {e}")
                iteration_history.append({
                    'iteration': iteration,
                    'error': str(e),
                    'score': 0,
                    'failed': True
                })
        
        # Use best result found
        final_result = best_result or state
        final_result['iteration_history'] = iteration_history
        final_result['final_iteration_count'] = len(iteration_history)
        final_result['achieved_target'] = best_score >= self.target_score
        
        print(f"\n🎯 FINAL RESULT: Score {best_score}/10 after {len(iteration_history)} iterations")
        if best_score >= self.target_score:
            print("✅ Target quality achieved!")
        else:
            print(f"⚠️ Target not reached. Best attempt: {best_score}/10")
        
        # Save the best result
        print("🔄 Phase 7: Extracting and Saving Generated Files")
        self._save_generated_files(final_result)
        
        # Phase 8: Memory Learning (for successful projects)
        if best_score >= 7.0:  # Learn from successful projects
            print("🔄 Phase 8: Memory Learning - Storing successful patterns")
            try:
                project_data = {
                    'prompt': state.get('prompt', ''),
                    'tech_stack': final_result.get('tech_stack', {}),
                    'generated_code': final_result.get('generated_code', {}),
                    'architecture': final_result.get('architecture', {}),
                    'domain': final_result.get('domain_info', {})
                }
                self.learning_memory.learn_from_successful_project(project_data, best_score)
            except Exception as e:
                print(f"⚠️ Memory learning failed: {e}")
        
        print("🎉 ENHANCED PIPELINE V2 COMPLETE!")
        return final_result
    
    def _run_pipeline_phases(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the core pipeline phases"""
        
        # Phase 1: Learning & Memory
        print("🔄 Phase 1: Learning & Memory Analysis")
        if self.learning_memory.can_run(state):
            memory_result = self.learning_memory.run(state)
            if memory_result:
                state.update(memory_result)
        
        # Phase 2: Optimized Team Debate
        print("🔄 Phase 2: Optimized Team Technology Debate")
        try:
            prompt_text = state.get('prompt', '')
            context_text = state.get('experience_hints', '')
            
            print(f"🔍 DEBUG: prompt_text = '{prompt_text[:50]}...'")
            print(f"🔍 DEBUG: state keys = {list(state.keys())}")
            
            if not prompt_text:
                raise ValueError(f"No prompt found in state. Keys: {list(state.keys())}")
                
            tech_decision = self.team_debate.run_smart_debate(prompt_text, context_text)
            state['tech_stack'] = tech_decision.get('final_decision', {})
            state['team_debate_process'] = tech_decision.get('process', '')
            
        except Exception as e:
            print(f"❌ Team debate failed: {e}")
            # Fallback tech stack
            state['tech_stack'] = {
                "backend": {"name": "Node.js", "reasoning": "Popular backend choice"},
                "frontend": {"name": "React", "reasoning": "Popular frontend choice"},
                "database": {"name": "PostgreSQL", "reasoning": "Reliable database choice"},
                "deployment": {"name": "Docker", "reasoning": "Standard containerization"}
            }
            state['team_debate_process'] = 'fallback_due_to_error'
        
        # Phase 3: Capabilities & Contract
        print("🔄 Phase 3: Capabilities & Contract Definition")
        for agent in [CapabilityAgent(), ContractAgent()]:
            if agent.can_run(state):
                result = agent.run(state)
                if result:
                    state.update(result)
        
        # Phase 4: Architecture Design
        print("🔄 Phase 4: Architecture Design")
        arch_agent = ArchitectureAgent()
        if arch_agent.can_run(state):
            result = arch_agent.run(state)
            if result:
                state.update(result)
        
        # Phase 5: Progressive Code Generation
        print("🔄 Phase 5: Progressive Code Generation")
        codegen_agent = ProgressiveCodeGenV2()
        if codegen_agent.can_run(state):
            # Pass memory agent to enable pattern serving
            state['memory'] = self.learning_memory
            result = codegen_agent.run(state)
            if result:
                state.update(result)
        
        # Phase 6: Final Validation
        print("🔄 Phase 6: Final System Validation")
        validate_agent = ValidateAgent()
        if validate_agent.can_run(state):
            result = validate_agent.run(state)
            if result:
                state.update(result)
        
        return state
    
    def _add_refinement_context(self, state: Dict[str, Any], history: list):
        """Add context for refinement in next iteration"""
        
        # Extract key issues from previous attempts
        all_issues = []
        for attempt in history:
            if 'issues' in attempt:
                all_issues.extend(attempt['issues'])
        
        # Add refinement guidance
        refinement_context = f"""
REFINEMENT CONTEXT - Iteration {len(history) + 1}:

Previous attempts and issues identified:
{chr(10).join(f"- Iteration {a['iteration']}: Score {a.get('score', 0)}/10" for a in history)}

Common issues to address:
{chr(10).join(f"- {issue}" for issue in set(all_issues[:5]))}

FOCUS ON: Addressing these specific issues in the next iteration.
"""
        
        state['refinement_context'] = refinement_context
        state['previous_issues'] = list(set(all_issues))
        
        print("🔍 Added refinement context for next iteration")
    
    def _save_generated_files(self, state: Dict[str, Any]):
        """Save generated files to disk"""
        import os
        from pathlib import Path
        
        output_dir = Path(self.save_folder)
        output_dir.mkdir(exist_ok=True)
        
        generated_files = state.get('generated_code', {})
        if not generated_files:
            print("⚠️ No generated files to save")
            return
        
        saved_count = 0
        for filename, content in generated_files.items():
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
        
        # Save project metadata
        metadata = {
            'project_name': state.get('project_name'),
            'prompt': state.get('prompt'),
            'tech_stack': state.get('tech_stack'),
            'architecture': state.get('architecture'),
            'validation_score': state.get('best_validation_score'),
            'progressive_validation': state.get('progressive_validation'),
            'final_validation': state.get('final_validation'),
            'generation_method': state.get('generation_method'),
            'files_count': saved_count
        }
        
        metadata_file = output_dir / "project_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📊 Saved {saved_count} files and metadata to: {output_dir.absolute()}")
        
        # Show summary
        validation_score = state.get('best_validation_score', 'N/A')
        progressive_scores = state.get('progressive_validation', {})
        
        print(f"\n📈 GENERATION SUMMARY:")
        print(f"   📄 Files Generated: {saved_count}")
        print(f"   🎯 Final Validation: {validation_score}/10")
        
        if progressive_scores:
            print(f"   🔄 Component Scores:")
            for component, score_data in progressive_scores.items():
                score = score_data.get('score', 'N/A')
                print(f"      {component}: {score}/10")
        
        return output_dir

# Factory function for easy usage
def create_enhanced_pipeline_v2(save_folder="gen2_files"):
    """Create enhanced pipeline V2 with optimizations"""
    return EnhancedPipelineV2(save_to_folder=save_folder)
