# agents/product/progressive_codegen.py
from typing import Dict, Any
from core.base import Agent, LLMBackedMixin, track_llm_call

class ProgressiveCodeGenAgent(Agent, LLMBackedMixin):
    """
    Progressive code generation: Frontend → Backend → Database → Integration
    Validates each component before moving to the next
    """
    id = "progressive_codegen"
    
    def __init__(self):
        super().__init__()
        
    def can_run(self, state: Dict[str, Any]) -> bool:
        return state.get('architecture') is not None
        
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call(self.__class__.__name__, "progressive multi-component generation")
        
        architecture = state.get('architecture', {})
        contract = state.get('contract', {})
        tech_stack = state.get('tech_stack', {})
        
        # Progressive generation phases
        generated_files = {}
        validation_results = {}
        
        phases = [
            ("frontend", "Frontend Application"),
            ("backend", "Backend API"),
            ("database", "Database Schema"),
            ("integration", "Integration & Deployment")
        ]
        
        for phase_name, phase_description in phases:
            print(f"🔄 Phase: {phase_description}")
            
            # Generate component
            component_files = self._generate_component(
                phase_name, phase_description, architecture, contract, tech_stack, state
            )
            
            if component_files:
                generated_files.update(component_files)
                
                # Validate component
                validation = self._validate_component(
                    phase_name, component_files, architecture, contract
                )
                validation_results[phase_name] = validation
                
                # Check if component passes validation
                if validation.get('score', 0) < 6:
                    print(f"⚠️ {phase_description} validation failed (score: {validation.get('score', 0)}/10)")
                    print(f"   Issues: {validation.get('issues', [])[:3]}")
                    
                    # Optionally retry with improvements
                    if validation.get('score', 0) >= 4:  # Partial success
                        improved_files = self._improve_component(
                            phase_name, component_files, validation, architecture, contract
                        )
                        if improved_files:
                            generated_files.update(improved_files)
                            print(f"✅ {phase_description} improved")
                else:
                    print(f"✅ {phase_description} passed validation (score: {validation.get('score', 0)}/10)")
            
        # Final integration validation
        final_validation = self._validate_integration(generated_files, architecture, contract)
        
        return {
            **state,
            'generated_code': generated_files,
            'progressive_validation': validation_results,
            'final_validation': final_validation,
            'generation_method': 'progressive_with_validation'
        }
    
    def _generate_component(self, phase_name: str, phase_description: str, 
                          architecture: Dict, contract: Dict, tech_stack: Dict, 
                          state: Dict) -> Dict[str, str]:
        """Generate files for a specific component"""
        
        # Get files from architecture - check multiple possible keys
        files = architecture.get('files', [])
        if not files:
            files = architecture.get('required_files', [])
        if not files:
            # Extract from project_structure if available
            project_structure = architecture.get('project_structure', {})
            files = list(project_structure.keys())
        
        print(f"🔍 DEBUG {phase_name}: Available files = {files}")
        
        component_files = [f for f in files if self._belongs_to_phase(f, phase_name)]
        print(f"🔍 DEBUG {phase_name}: Component files = {component_files}")
        
        if not component_files:
            print(f"⚠️ No files found for {phase_name} phase, generating defaults")
            # Generate default files for this phase
            component_files = self._get_default_files_for_phase(phase_name, tech_stack)
            
        if not component_files:
            return {}
            
        # Determine technology for this component
        backend_tech = tech_stack.get('backend', {}).get('name', 'Node.js')
        frontend_tech = tech_stack.get('frontend', {}).get('name', 'React')
        database_tech = tech_stack.get('database', {}).get('name', 'PostgreSQL')
        
        print(f"🎯 Generating {len(component_files)} files for {phase_description}")
        
        system_prompt = f"""You are an expert {phase_name} developer specializing in {phase_description.lower()}.

CRITICAL REQUIREMENTS:
- Generate COMPLETE, production-ready code (50-200 lines per file)
- Include comprehensive error handling and validation
- Add detailed comments explaining functionality
- Follow modern best practices and security standards
- Ensure all files are fully functional and interconnected

Technology Stack:
- Backend: {backend_tech}
- Frontend: {frontend_tech}  
- Database: {database_tech}

Component Focus: {phase_description}
Required Files: {component_files}"""
- Add detailed comments explaining functionality
- Follow modern best practices and security standards
- Ensure all files are fully functional and interconnected

Technology Stack:
- Backend: {backend_tech}
- Frontend: {frontend_tech}  
- Database: {database_tech}

Component Focus: {phase_description}
Required Files: {component_files}"""

        user_prompt = f"""Generate complete {phase_description} code for this application:

Project Requirements:
{state.get('prompt', 'Web application')}

Architecture Overview:
{architecture.get('rationale', 'Standard web application architecture')}

Contract Endpoints:
{self._format_endpoints(contract.get('endpoints', []))}

Files to Generate: {component_files}

Return JSON format:
{{
  "files": {{
    "filename1.ext": "complete file content with full implementation",
    "filename2.ext": "complete file content with full implementation"
  }},
  "setup_instructions": ["step1", "step2"],
  "dependencies": ["package1", "package2"],
  "notes": "implementation details and considerations"
}}"""

        response = self.llm_json(system_prompt, user_prompt, {
            "files": {},
            "setup_instructions": [],
            "dependencies": [],
            "notes": f"Generated {phase_description} component"
        })
        
        return response.get('files', {})
    
    def _validate_component(self, phase_name: str, files: Dict[str, str], 
                          architecture: Dict, contract: Dict) -> Dict[str, Any]:
        """Validate a specific component"""
        
        system_prompt = f"""You are a senior code reviewer specializing in {phase_name} validation.

Validate the {phase_name} component for:
- Code completeness and functionality
- Best practices adherence
- Security considerations
- Performance optimization
- Integration compatibility"""

        user_prompt = f"""Review this {phase_name} component:

Files Generated: {list(files.keys())}
Total Content: {sum(len(content) for content in files.values())} characters

Sample Code:
{self._format_code_sample(files)}

Return JSON validation:
{{
  "score": 8,
  "completeness": 9,
  "quality": 8,
  "security": 7,
  "issues": ["specific issue 1", "specific issue 2"],
  "recommendations": ["improvement 1", "improvement 2"],
  "passes": true
}}"""

        return self.llm_json(system_prompt, user_prompt, {
            "score": 5,
            "completeness": 5,
            "quality": 5,
            "security": 5,
            "issues": ["Validation failed"],
            "recommendations": ["Review implementation"],
            "passes": False
        })
    
    def _improve_component(self, phase_name: str, files: Dict[str, str], 
                         validation: Dict, architecture: Dict, contract: Dict) -> Dict[str, str]:
        """Improve component based on validation feedback"""
        
        issues = validation.get('issues', [])[:3]  # Top 3 issues
        recommendations = validation.get('recommendations', [])[:3]
        
        system_prompt = f"""You are an expert {phase_name} developer focused on code improvement.

Address these specific issues:
{issues}

Apply these recommendations:
{recommendations}"""

        user_prompt = f"""Improve the {phase_name} component by fixing identified issues:

Current Implementation Issues:
{issues}

Improvement Recommendations:
{recommendations}

Files to Improve:
{self._format_code_sample(files)}

Return JSON with improved files:
{{
  "files": {{
    "filename.ext": "improved complete implementation"
  }},
  "fixes_applied": ["fix 1", "fix 2"],
  "remaining_concerns": ["concern if any"]
}}"""

        response = self.llm_json(system_prompt, user_prompt, {"files": files})
        return response.get('files', {})
    
    def _validate_integration(self, all_files: Dict[str, str], 
                            architecture: Dict, contract: Dict) -> Dict[str, Any]:
        """Final integration validation"""
        
        system_prompt = """You are a senior system architect reviewing full-stack integration.

Validate the complete system for:
- Component integration and communication
- End-to-end functionality
- Deployment readiness
- Production quality"""

        user_prompt = f"""Review complete system integration:

Generated Files: {len(all_files)}
Components: Frontend, Backend, Database, Deployment

Architecture Summary:
{architecture.get('rationale', 'Standard architecture')}

Return final validation JSON:
{{
  "overall_score": 8,
  "integration_score": 9,
  "deployment_readiness": 7,
  "production_quality": 8,
  "missing_components": ["component if any"],
  "critical_issues": ["critical issue if any"],
  "ready_for_deployment": true
}}"""

        return self.llm_json(system_prompt, user_prompt, {
            "overall_score": 5,
            "integration_score": 5,
            "deployment_readiness": 4,
            "production_quality": 5,
            "missing_components": ["Multiple components incomplete"],
            "critical_issues": ["Integration validation failed"],
            "ready_for_deployment": False
        })
    
    def _belongs_to_phase(self, filename: str, phase: str) -> bool:
        """Determine if a file belongs to a specific phase"""
        phase_patterns = {
            "frontend": ["client/", "frontend/", "public/", "src/components/", "ui/", ".html", ".css", ".js", ".jsx", ".ts", ".tsx"],
            "backend": ["server/", "backend/", "api/", "routes/", ".py", ".js", ".java", ".cs", ".go"],
            "database": ["db/", "database/", "migrations/", ".sql", "schema", "models/"],
            "integration": ["docker", "deploy", "config/", ".yml", ".yaml", ".json", "Dockerfile", "compose"]
        }
        
        patterns = phase_patterns.get(phase, [])
        return any(pattern in filename.lower() for pattern in patterns)
    
    def _format_endpoints(self, endpoints) -> str:
        """Format contract endpoints for prompt"""
        if not endpoints:
            return "No specific endpoints defined"
            
        formatted = []
        for ep in endpoints[:10]:  # Limit to 10 endpoints
            if isinstance(ep, dict):
                method = ep.get('method', 'GET')
                path = ep.get('path', '/')
                formatted.append(f"- {method} {path}")
            elif isinstance(ep, str):
                formatted.append(f"- {ep}")
        
        return "\n".join(formatted)
    
    def _format_code_sample(self, files: Dict[str, str]) -> str:
        """Format code sample for validation"""
        sample = ""
        for filename, content in list(files.items())[:2]:  # First 2 files
            sample += f"\n--- {filename} ---\n"
            sample += content[:500] + ("..." if len(content) > 500 else "")
        return sample
    
    def _get_default_files_for_phase(self, phase_name: str, tech_stack: Dict) -> List[str]:
        """Get default files when none are detected for a phase."""
        backend_tech = tech_stack.get('backend', {}).get('name', 'Node.js').lower()
        frontend_tech = tech_stack.get('frontend', {}).get('name', 'React').lower()
        
        defaults = {
            "frontend": [
                "frontend/src/App.js" if 'react' in frontend_tech else "frontend/index.html",
                "frontend/src/components/Header.js" if 'react' in frontend_tech else "frontend/style.css",
                "frontend/src/index.js" if 'react' in frontend_tech else "frontend/script.js"
            ],
            "backend": [
                "backend/server.js" if 'node' in backend_tech else "backend/app.py",
                "backend/routes/api.js" if 'node' in backend_tech else "backend/routes.py",
                "backend/package.json" if 'node' in backend_tech else "backend/requirements.txt"
            ],
            "database": [
                "database/schema.sql",
                "database/migrations.sql",
                "database/seeds.sql"
            ],
            "integration": [
                "docker-compose.yml",
                "Dockerfile",
                "README.md"
            ]
        }
        
        return defaults.get(phase_name, [f"{phase_name}/main.js"])
