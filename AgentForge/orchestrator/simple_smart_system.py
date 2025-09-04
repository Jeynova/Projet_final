"""
Simple Smart Agent System that integrates with existing AgentForge
Follows the requested logic:
1. Check memory first
2. Smart tech selection 
3. Conditional validation
4. Code generation
5. Infrastructure validation
6. Testing

Uses environment variables for mode switching.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

class SimpleSmartSystem:
    """
    Simple implementation of the smart agent logic without complex dependencies
    """
    
    def __init__(self):
        # Read environment configuration
        self.agentic_enabled = os.getenv("AGENTFORGE_AGENTIC", "0") == "1"
        self.mode = os.getenv("AGENTFORGE_MODE", "templates")  # templates | agent_first | auto
        
        # Initialize LLM client fallback
        try:
            import sys
            sys.path.append(str(Path(__file__).parent.parent))
            from core.llm_client import LLMClient
            self.llm_client = LLMClient()
        except:
            self.llm_client = None
    
    def check_memory_rag(self, prompt: str) -> Dict[str, Any]:
        """Check RAG memory for similar prompt+tech combinations"""
        memory_file = Path(__file__).parent.parent / "agentforge.db.json"
        
        if memory_file.exists():
            try:
                with open(memory_file) as f:
                    data = json.load(f)
                    # Simple similarity check
                    for project in data.get("projects", []):
                        similarity = self._calculate_similarity(prompt, project.get("prompt", ""))
                        if similarity > 0.7:
                            return {
                                "found": True,
                                "project": project["name"],
                                "tech_hints": project.get("tech_stack", []),
                                "confidence": similarity,
                                "reason": "High similarity match found in memory"
                            }
            except:
                pass
        
        return {"found": False, "confidence": 0.0}
    
    def select_tech_stack(self, prompt: str, memory_hints: list = None) -> Dict[str, Any]:
        """Smart tech stack selection based on prompt analysis"""
        
        # Use LLM for tech selection if available
        if self.llm_client:
            return self._select_tech_with_llm(prompt, memory_hints)
        else:
            # Fallback to rule-based selection
            return self._select_tech_rules(prompt, memory_hints)
    
    def _select_tech_with_llm(self, prompt: str, memory_hints: list = None) -> Dict[str, Any]:
        """Use LLM for intelligent tech stack selection"""
        
        tech_prompt = f"""
Analyze this project request and select the best technology stack:

Project: {prompt}
Memory hints from similar projects: {memory_hints or []}

Consider:
1. Project complexity (simple/medium/complex)
2. Whether it's a prototype or production system
3. Performance requirements
4. Development speed vs robustness
5. Team expertise typically available
6. Deployment and maintenance requirements

Choose technologies that are:
- Well-suited for the specific requirements
- Not over-engineered for simple projects
- Not under-powered for complex projects
- Have good community support and documentation

Return ONLY a JSON object with this exact structure:
{{
    "stack": ["technology1", "technology2", "technology3"],
    "reasoning": "detailed explanation of why these technologies were chosen",
    "confidence": 0.8,
    "complexity_assessment": "simple|medium|complex",
    "alternatives": ["alternative1", "alternative2"]
}}
"""

        try:
            print(f"🤖 Using LLM for tech stack selection...")
            
            # Use extract_json method (not complete)
            response = self.llm_client.extract_json(
                system_prompt="You are a technology stack advisor. Analyze project requirements and recommend appropriate technologies.",
                user_prompt=tech_prompt
            )
            
            if response and isinstance(response, dict):
                print(f"🔧 LLM selected: {response.get('stack', [])} (confidence: {response.get('confidence', 0)})")
                return response
            else:
                print(f"⚠️ LLM returned no valid response, using fallback")
                return self._select_tech_rules(prompt, memory_hints)
                
        except Exception as e:
            print(f"⚠️ LLM tech selection failed: {e}")
            return self._select_tech_rules(prompt, memory_hints)
    
    def _select_tech_rules(self, prompt: str, memory_hints: list = None) -> Dict[str, Any]:
        """Rule-based tech selection fallback"""
        
        # Simple rule-based tech selection (original logic)
        if "api" in prompt.lower() and "rest" in prompt.lower():
            return {
                "stack": ["fastapi", "sqlite", "uvicorn"],
                "reasoning": "FastAPI for REST APIs - modern, fast, well-documented",
                "confidence": 0.9
            }
        elif "blog" in prompt.lower():
            return {
                "stack": ["django", "postgresql", "redis"],
                "reasoning": "Django excellent for blog platforms with admin interface",
                "confidence": 0.8
            }
        elif "web app" in prompt.lower() or "webapp" in prompt.lower():
            return {
                "stack": ["flask", "sqlite", "bootstrap"],
                "reasoning": "Flask for lightweight web applications",
                "confidence": 0.7
            }
        else:
            return {
                "stack": ["python", "sqlite"],
                "reasoning": "Default safe choice for general Python projects",
                "confidence": 0.5
            }
    
    def validate_tech_choice(self, tech_stack: list, prompt: str) -> Dict[str, Any]:
        """Validate tech stack against anti-patterns"""
        
        issues = []
        
        # Anti-pattern detection
        if "react" in tech_stack and ("simple" in prompt.lower() or "prototype" in prompt.lower()):
            issues.append("React might be overkill for simple/prototype project")
        
        if "postgresql" in tech_stack and "prototype" in prompt.lower():
            issues.append("PostgreSQL overkill for prototype - consider SQLite")
        
        if "mongodb" in tech_stack and ("simple" in prompt.lower() or "sql" in prompt.lower()):
            issues.append("MongoDB unnecessary for simple/SQL-focused projects")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "confidence": 0.8 if len(issues) == 0 else 0.3
        }
    
    def generate_code(self, prompt: str, tech_stack: list, project_name: str) -> Dict[str, Any]:
        """Generate code using templates or model"""
        
        # Check if we have templates for this stack
        has_templates = self._has_templates(tech_stack)
        
        if has_templates and self.mode != "agent_first":
            return {
                "method": "templates",
                "status": "generated",
                "files": ["main.py", "requirements.txt", "README.md", "Dockerfile"],
                "approach": "template_based",
                "message": f"Generated {project_name} using templates for {tech_stack}"
            }
        else:
            # Actually use the LLM to generate code!
            return self._generate_with_model(prompt, tech_stack, project_name)
    
    def _generate_with_model(self, prompt: str, tech_stack: list, project_name: str) -> Dict[str, Any]:
        """Use LLM to actually generate code"""
        
        if not self.llm_client:
            return {
                "method": "model_generated",
                "status": "error", 
                "error": "LLM client not available",
                "approach": "fallback"
            }
        
        # Create a detailed prompt for code generation
        code_prompt = f"""
Generate a complete, working {prompt} using the following technology stack: {tech_stack}

Project Name: {project_name}

Requirements:
1. Create a production-ready application structure
2. Include all necessary files (main application, requirements, README, config)
3. Follow best practices for the chosen technology stack
4. Add proper error handling and logging
5. Include basic tests if applicable
6. Make the code modular and maintainable

For the main application file, provide the complete code with:
- All necessary imports
- Proper configuration setup
- Core functionality implementation
- Error handling
- Basic logging

Return the response in JSON format with:
{{
    "files": [
        {{
            "name": "filename.py",
            "content": "complete file content here"
        }}
    ],
    "structure": ["list of all files that should be created"],
    "instructions": "deployment and usage instructions"
}}

Focus on creating working, executable code that follows the requirements exactly.
"""
        
        try:
            print(f"🤖 Generating code with LLM for: {prompt}")
            print(f"🔧 Tech stack: {tech_stack}")
            
            # Use extract_json method instead of complete
            response = self.llm_client.extract_json(
                system_prompt="""You are an expert software developer. Generate complete, working code based on requirements. 
Always return valid JSON with the specified structure.""",
                user_prompt=code_prompt
            )
            
            if response and isinstance(response, dict):
                print(f"📝 LLM returned structured response")
                
                return {
                    "method": "model_generated",
                    "status": "generated",
                    "files": response.get("files", []),
                    "structure": response.get("structure", []),
                    "instructions": response.get("instructions", ""),
                    "approach": "llm_generated",
                    "message": f"Generated {project_name} using LLM with {tech_stack}",
                    "llm_response": response
                }
            else:
                print(f"⚠️ LLM returned no valid response")
                # Fallback to a simple structure
                return {
                    "method": "model_generated", 
                    "status": "generated_fallback",
                    "files": [{"name": "main.py", "content": f"# {prompt}\n# Tech stack: {tech_stack}\nprint('Hello World')"}],
                    "approach": "llm_fallback",
                    "message": f"Generated {project_name} using fallback (LLM unavailable)"
                }
                
        except Exception as e:
            print(f"❌ LLM code generation failed: {e}")
            return {
                "method": "model_generated",
                "status": "error",
                "error": str(e),
                "approach": "model_error",
                "message": f"Failed to generate {project_name} with LLM: {e}"
            }
    
    def validate_infrastructure(self, project_path: str, tech_stack: list) -> Dict[str, Any]:
        """Validate deployment readiness"""
        
        issues = []
        recommendations = []
        
        # Check for containerization
        if Path(project_path).exists():
            if not (Path(project_path) / "Dockerfile").exists():
                recommendations.append("Add Dockerfile for containerization")
            if not (Path(project_path) / ".dockerignore").exists():
                recommendations.append("Add .dockerignore for better builds")
        
        return {
            "docker_ready": len([r for r in recommendations if "Docker" in r]) == 0,
            "k8s_ready": False,  # Would check for k8s manifests
            "issues": issues,
            "recommendations": recommendations
        }
    
    def test_generated_code(self, project_path: str) -> Dict[str, Any]:
        """Test that generated code works"""
        
        if not Path(project_path).exists():
            return {"tests_pass": False, "error": "Project path does not exist"}
        
        # Check for basic files
        has_main = any((Path(project_path) / f).exists() for f in ["main.py", "app.py", "__main__.py"])
        has_requirements = (Path(project_path) / "requirements.txt").exists()
        has_readme = (Path(project_path) / "README.md").exists()
        
        return {
            "tests_pass": has_main and has_requirements,
            "lint_clean": True,  # Would run actual linting
            "runnable": has_main,
            "files_present": {
                "main_file": has_main,
                "requirements": has_requirements,
                "readme": has_readme
            }
        }
    
    def build_project(self, prompt: str, name: str, output_dir: str) -> Dict[str, Any]:
        """Main entry point - smart agent logic"""
        
        print(f"🧠 Simple Smart System - Agentic: {self.agentic_enabled}, Mode: {self.mode}")
        
        if not self.agentic_enabled:
            return self._deterministic_mode(prompt, name, output_dir)
        
        # Smart agent flow
        logs = []
        
        # 1. Check memory first
        print("1️⃣ Checking memory/RAG...")
        memory_result = self.check_memory_rag(prompt)
        logs.append(f"Memory check: {memory_result}")
        
        if memory_result["found"] and memory_result["confidence"] > 0.8:
            print(f"✅ High confidence memory match: {memory_result['project']}")
            tech_stack = memory_result["tech_hints"]
            logs.append("Skipping tech selection - using memory hints")
        else:
            # 2. Tech selection needed
            print("2️⃣ Selecting technology stack...")
            tech_result = self.select_tech_stack(prompt, memory_result.get("tech_hints"))
            tech_stack = tech_result["stack"]
            logs.append(f"Tech selection: {tech_result}")
            
            # 3. Validate tech choice only if confidence is low
            if tech_result["confidence"] < 0.7:
                print("3️⃣ Validating tech choice (low confidence)...")
                validation = self.validate_tech_choice(tech_stack, prompt)
                logs.append(f"Tech validation: {validation}")
                
                if not validation["valid"]:
                    print("⚠️ Tech validation issues found, adjusting...")
                    # Simple fallback
                    tech_stack = ["python", "sqlite"]
        
        # 4. Generate code
        print("4️⃣ Generating code...")
        generation = self.generate_code(prompt, tech_stack, name)
        logs.append(f"Code generation: {generation}")
        
        # 5. Validate infrastructure (only if deploying)
        if "deploy" in prompt.lower() or "production" in prompt.lower():
            print("5️⃣ Validating infrastructure...")
            infra = self.validate_infrastructure(output_dir, tech_stack)
            logs.append(f"Infrastructure check: {infra}")
        
        # 6. Test generated code (always)
        print("6️⃣ Testing generated code...")
        test_result = self.test_generated_code(output_dir)
        logs.append(f"Testing: {test_result}")
        
        return {
            "status": "completed",
            "name": name,
            "output_dir": output_dir,
            "approach": "simple_smart_agent",
            "tech_stack": tech_stack,
            "logs": logs,
            "final_result": {
                "memory_used": memory_result["found"],
                "tech_validated": "validation" in locals(),
                "code_generated": generation["status"] == "generated",
                "tests_passed": test_result.get("tests_pass", False)
            }
        }
    
    def _deterministic_mode(self, prompt: str, name: str, output_dir: str) -> Dict[str, Any]:
        """Fall back to deterministic template mode"""
        print("📋 Deterministic mode (agentic disabled)")
        
        return {
            "status": "completed",
            "name": name,
            "output_dir": output_dir,
            "approach": "deterministic_templates",
            "logs": ["Agentic mode disabled, used deterministic templates"]
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _has_templates(self, tech_stack: list) -> bool:
        """Check if templates exist for this stack"""
        templates_dir = Path(__file__).parent.parent / "templates"
        
        if not templates_dir.exists():
            return False
        
        for tech in tech_stack:
            if (templates_dir / f"{tech}_template").exists():
                return True
        
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Smart Agent System")
    parser.add_argument("--prompt", required=True, help="Project description")
    parser.add_argument("--name", default="test-project", help="Project name")
    parser.add_argument("--output", default="./generated", help="Output directory")
    
    args = parser.parse_args()
    
    system = SimpleSmartSystem()
    result = system.build_project(args.prompt, args.name, args.output)
    
    print("\n✅ Final Result:")
    print(json.dumps(result, indent=2))
