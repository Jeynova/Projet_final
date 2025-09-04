"""
Progressive Code Generation Orchestrator (Refactored)

Main orchestrator for progressive, context-aware file generation
using the modular components (ContextManager, StepValidator, FileGenerator).
"""

from typing import Dict, List, Any, Optional, Tuple
from .context_manager import ContextManager
from .step_validator import StepValidator  
from .file_generator import FileGenerator
from core.base import Agent


class ProgressiveCodeGenV2(Agent):
    """
    Refactored Progressive Code Generation Agent
    
    Uses modular components for:
    - Context management and file dependency tracking
    - Progressive file-by-file generation with full context
    - Comprehensive validation with detailed feedback
    - Retry logic with validation-driven improvements
    """
    
    def __init__(self):
        super().__init__()
        self.context_manager = ContextManager()
        self.step_validator = StepValidator() 
        self.file_generator = FileGenerator(self.context_manager, self.step_validator)
        self.generation_log = []
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        """Check if this agent can run with the current state"""
        # Require basic state components
        return (
            'prompt' in state and 
            'architecture' in state and
            isinstance(state['prompt'], str) and
            len(state['prompt'].strip()) > 10
        )
        
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for progressive code generation"""
        
        try:
            # Extract required parameters
            phase_name = state.get('phase_name', 'code_generation')
            prompt = state.get('prompt', 'web application')
            architecture = state.get('architecture', {})
            contract = state.get('contract', {})
            tech_stack = state.get('tech_stack', {})
            
            print(f"🚀 PROGRESSIVE V2: Starting {phase_name} generation")
            
            # Define generation steps based on architecture
            steps = self._plan_generation_steps(architecture, contract, tech_stack)
            
            all_generated_files = {}
            step_results = []
            
            # Execute each step progressively
            for step_idx, step in enumerate(steps):
                step_name = step['name']
                print(f"\n🔄 STEP {step_idx + 1}/{len(steps)}: {step_name}")
                
                # Generate files for this step
                step_files, step_result = self._execute_step(
                    step, prompt, all_generated_files, architecture, contract, tech_stack
                )
                
                # Add to cumulative results
                all_generated_files.update(step_files)
                step_results.append(step_result)
                
                # Update context for next steps
                self.context_manager.add_step_summary(step_name, step_files, step_result)
                
                print(f"✅ STEP COMPLETE: {step_name} - {len(step_files)} files, score: {step_result['overall_score']:.1f}/10")
            
            # Final validation
            overall_result = self._validate_complete_generation(all_generated_files, step_results)
            
            # Log results
            self.generation_log.append({
                'phase_name': phase_name,
                'total_files': len(all_generated_files),
                'steps_completed': len(step_results),
                'overall_score': overall_result['overall_score'],
                'success': overall_result['is_valid']
            })
            
            return {
                'generated_code': all_generated_files,
                'step_results': step_results,
                'overall_result': overall_result,
                'generation_stats': self.file_generator.get_generation_stats()
            }
            
        except Exception as e:
            print(f"❌ PROGRESSIVE V2 ERROR: {e}")
            return {
                'generated_code': {},
                'error': str(e),
                'step_results': []
            }
    
    def _plan_generation_steps(self, architecture: Dict[str, Any], 
                              contract: Dict[str, Any], 
                              tech_stack: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan generation steps based on architecture and requirements"""
        
        # Extract file structure from architecture
        project_structure = architecture.get('project_structure', {})
        if not isinstance(project_structure, dict):
            # Fallback structure
            project_structure = {
                'api/': 'Backend API endpoints',
                'src/': 'Frontend components',
                'db/': 'Database schemas'
            }
        
        # Build file list from structure
        all_files = []
        for folder, description in project_structure.items():
            if folder.endswith('/'):
                # Generate typical files for this folder
                folder_files = self._generate_files_for_folder(folder, description, contract, tech_stack)
                all_files.extend(folder_files)
        
        # Group files into logical steps
        steps = [
            {
                'name': 'Backend API',
                'description': 'REST API endpoints and business logic',
                'files': [f for f in all_files if 'api/' in f or 'controller' in f or 'route' in f],
                'requirements': {
                    'min_lines': 100,
                    'min_logic_lines': 20,
                    'min_score': 6,
                    'min_files_per_step': 1,
                    'min_total_lines_per_step': 200
                }
            },
            {
                'name': 'Business Services',
                'description': 'Business logic and data processing',
                'files': [f for f in all_files if 'service' in f or 'logic' in f],
                'requirements': {
                    'min_lines': 150,
                    'min_logic_lines': 30,
                    'min_score': 6,
                    'min_files_per_step': 1,
                    'min_total_lines_per_step': 300
                }
            },
            {
                'name': 'Data Models',
                'description': 'Database schemas and data models',
                'files': [f for f in all_files if 'model' in f or 'schema' in f or 'db/' in f],
                'requirements': {
                    'min_lines': 80,
                    'min_logic_lines': 15,
                    'min_score': 6,
                    'min_files_per_step': 1,
                    'min_total_lines_per_step': 150
                }
            },
            {
                'name': 'Frontend Components',
                'description': 'User interface components',
                'files': [f for f in all_files if 'src/' in f or 'component' in f or f.endswith(('.tsx', '.jsx'))],
                'requirements': {
                    'min_lines': 120,
                    'min_logic_lines': 25,
                    'min_score': 6,
                    'min_files_per_step': 1,
                    'min_total_lines_per_step': 250
                }
            },
            {
                'name': 'Configuration & Deployment',
                'description': 'Configuration files and deployment scripts',
                'files': [f for f in all_files if 'docker' in f or 'config' in f or f.endswith(('.json', '.yml', '.yaml'))],
                'requirements': {
                    'min_lines': 50,
                    'min_logic_lines': 10,
                    'min_score': 5,
                    'min_files_per_step': 1,
                    'min_total_lines_per_step': 100
                }
            }
        ]
        
        # Filter out empty steps
        steps = [step for step in steps if step['files']]
        
        # Ensure we have at least one step
        if not steps:
            steps = [{
                'name': 'Default Generation',
                'description': 'Basic application files',
                'files': all_files[:5] if all_files else ['src/app.js', 'api/routes.js'],
                'requirements': {
                    'min_lines': 100,
                    'min_logic_lines': 20,
                    'min_score': 6,
                    'min_files_per_step': 1,
                    'min_total_lines_per_step': 200
                }
            }]
        
        return steps
    
    def _generate_files_for_folder(self, folder: str, description: str, 
                                 contract: Dict[str, Any], 
                                 tech_stack: Dict[str, Any]) -> List[str]:
        """Generate typical files for a folder based on its purpose"""
        
        files = []
        folder_lower = folder.lower()
        
        if 'api' in folder_lower:
            # Backend API files
            files.extend([
                f"{folder}auth.ts",
                f"{folder}users.ts", 
                f"{folder}tasks.ts",
                f"{folder}categories.ts",
                f"{folder}routes.ts",
                f"{folder}middleware.ts"
            ])
            
        elif 'src' in folder_lower or 'component' in folder_lower:
            # Frontend component files
            files.extend([
                f"{folder}App.tsx",
                f"{folder}components/TaskList.tsx",
                f"{folder}components/TaskForm.tsx",
                f"{folder}components/UserProfile.tsx",
                f"{folder}services/api.ts",
                f"{folder}hooks/useTasks.ts",
                f"{folder}styles/main.css"
            ])
            
        elif 'db' in folder_lower or 'model' in folder_lower:
            # Database/model files
            files.extend([
                f"{folder}schema.sql",
                f"{folder}user.model.ts",
                f"{folder}task.model.ts",
                f"{folder}category.model.ts",
                f"{folder}migrations.ts"
            ])
            
        elif 'service' in folder_lower:
            # Service files
            files.extend([
                f"{folder}user.service.ts",
                f"{folder}task.service.ts",
                f"{folder}auth.service.ts",
                f"{folder}notification.service.ts"
            ])
            
        else:
            # Generic files based on description
            base_name = folder.rstrip('/').split('/')[-1]
            files.extend([
                f"{folder}index.ts",
                f"{folder}{base_name}.ts",
                f"{folder}types.ts"
            ])
        
        return files[:8]  # Limit files per folder
    
    def _execute_step(self, step: Dict[str, Any], original_prompt: str,
                     existing_files: Dict[str, str], architecture: Dict[str, Any],
                     contract: Dict[str, Any], tech_stack: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Execute a generation step with progressive context"""
        
        step_name = step['name']
        step_files = step['files']
        requirements = step['requirements']
        
        generated_files = {}
        max_step_retries = 2
        step_retry = 0
        
        while step_retry <= max_step_retries:
            if step_retry > 0:
                print(f"🔄 STEP RETRY {step_retry}/{max_step_retries}: {step_name}")
            
            generated_files = {}
            
            # Generate each file in the step
            for file_idx, filename in enumerate(step_files):
                print(f"📄 Generating {filename} ({file_idx + 1}/{len(step_files)})")
                
                # Build context for this file
                context = self.context_manager.build_context_for_file(
                    target_file=filename,
                    original_prompt=original_prompt,
                    file_tree=step_files + list(existing_files.keys()),
                    generated_files={**existing_files, **generated_files},
                    tech_stack=tech_stack,
                    architecture=architecture,
                    step_name=step_name
                )
                
                # Generate the file
                file_content = self.file_generator.generate_file(
                    filename=filename,
                    context=context,
                    requirements=requirements,
                    max_retries=3
                )
                
                generated_files[filename] = file_content
            
            # Validate the step
            step_result = self.step_validator.validate_step(
                step_name=step_name,
                generated_files=generated_files,
                requirements=requirements
            )
            
            # Check if step passed validation
            if step_result['is_valid'] or not self.step_validator.should_retry_step(step_result):
                break
                
            step_retry += 1
            print(f"⚠️ Step validation failed, retrying... (issues: {len(step_result.get('step_issues', []))})")
        
        return generated_files, step_result
    
    def _validate_complete_generation(self, all_files: Dict[str, str], 
                                    step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate the complete generation across all steps"""
        
        overall_result = {
            'is_valid': True,
            'overall_score': 0,
            'total_files': len(all_files),
            'total_steps': len(step_results),
            'passed_steps': 0,
            'failed_steps': 0,
            'issues': [],
            'strengths': []
        }
        
        # Aggregate step results
        step_scores = []
        for step_result in step_results:
            if isinstance(step_result, dict):
                if step_result.get('is_valid', False):
                    overall_result['passed_steps'] += 1
                else:
                    overall_result['failed_steps'] += 1
                    overall_result['is_valid'] = False
                
                score = step_result.get('overall_score', 0)
                step_scores.append(score)
        
        # Calculate overall score
        if step_scores:
            overall_result['overall_score'] = sum(step_scores) / len(step_scores)
        
        # Overall validation criteria
        if overall_result['total_files'] < 5:
            overall_result['issues'].append(f"Too few files generated: {overall_result['total_files']}")
            overall_result['is_valid'] = False
        
        total_lines = 0
        substantial_files = 0
        
        for filename, content in all_files.items():
            if isinstance(content, str) and content.strip():
                lines = len(content.split('\n'))
                total_lines += lines
                
                if lines >= 50:
                    substantial_files += 1
        
        if total_lines < 1000:
            overall_result['issues'].append(f"Insufficient total content: {total_lines} lines")
        
        if substantial_files < 3:
            overall_result['issues'].append(f"Too few substantial files: {substantial_files}")
        
        # Add strengths
        if overall_result['total_files'] >= 10:
            overall_result['strengths'].append("Good file coverage")
        
        if overall_result['overall_score'] >= 7:
            overall_result['strengths'].append("High quality code generation")
        
        if overall_result['passed_steps'] > overall_result['failed_steps']:
            overall_result['strengths'].append("Most steps passed validation")
        
        return overall_result
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """Get summary of all generation attempts"""
        if not self.generation_log:
            return {"total_runs": 0}
        
        total_runs = len(self.generation_log)
        successful_runs = sum(1 for log in self.generation_log if log.get('success', False))
        total_files = sum(log.get('total_files', 0) for log in self.generation_log)
        avg_score = sum(log.get('overall_score', 0) for log in self.generation_log) / total_runs
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            "total_files_generated": total_files,
            "average_score": avg_score,
            "file_generation_stats": self.file_generator.get_generation_stats()
        }
