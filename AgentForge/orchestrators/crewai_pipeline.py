"""
CrewAI Version - Using CrewAI for agent orchestration
Requires: pip install crewai
"""

try:
    from crewai import Agent, Task, Crew
    from crewai.process import Process
except ImportError:
    print("❌ CrewAI not installed. Run: pip install crewai")
    print("📄 Using simplified graph instead...")
    from .simple_graph_pipeline import SimpleGraphPipeline
    
    class CrewAIPipeline:
        def __init__(self, save_folder="crewai_generated"):
            self.simple_pipeline = SimpleGraphPipeline(save_folder)
        
        def run(self, prompt: str, project_name: str = "CrewAIProject"):
            return self.simple_pipeline.run(prompt, project_name)
else:
    from typing import Dict, Any
    import json
    from pathlib import Path


    class CrewAIPipeline:
        """CrewAI implementation maintaining successful patterns"""
        
        def __init__(self, save_folder: str = "crewai_generated"):
            self.save_folder = save_folder
            self.setup_agents()
        
        def setup_agents(self):
            """Initialize CrewAI agents"""
            
            # Memory Agent
            self.memory_agent = Agent(
                role='Memory Analyst',
                goal='Analyze past patterns and provide context for the current project',
                backstory='You are an expert at learning from past successful projects and applying those patterns.',
                verbose=True,
                allow_delegation=False
            )
            
            # Architecture Agent
            self.architect = Agent(
                role='System Architect',
                goal='Design comprehensive system architecture and tech stack',
                backstory='You are a senior architect who designs scalable, maintainable systems.',
                verbose=True,
                allow_delegation=False
            )
            
            # Developer Agent  
            self.developer = Agent(
                role='Senior Developer',
                goal='Generate high-quality, production-ready code',
                backstory='You are a senior developer who writes clean, efficient, well-documented code.',
                verbose=True,
                allow_delegation=False
            )
            
            # Quality Agent
            self.quality_agent = Agent(
                role='Quality Assurance',
                goal='Validate code quality and ensure project requirements are met',
                backstory='You are a QA expert who ensures high standards and catches potential issues.',
                verbose=True,
                allow_delegation=False
            )
        
        def run(self, prompt: str, project_name: str = "CrewAIProject") -> Dict[str, Any]:
            """Run CrewAI pipeline"""
            
            print(f"🚀 CREWAI PIPELINE: {prompt[:50]}...")
            
            # Memory Analysis Task
            memory_task = Task(
                description=f"""
                Analyze the project request: "{prompt}"
                
                Extract:
                1. Domain and complexity assessment
                2. Similar patterns from past projects
                3. Technology recommendations
                4. Potential challenges and solutions
                
                Provide context for the architecture team.
                """,
                agent=self.memory_agent,
                expected_output="Domain analysis, complexity assessment, and technology recommendations"
            )
            
            # Architecture Task
            architecture_task = Task(
                description=f"""
                Design system architecture for: "{prompt}"
                Project name: {project_name}
                
                Based on the memory analysis, create:
                1. Technology stack selection with reasoning
                2. System components and their interactions
                3. File structure and organization
                4. Database schema if needed
                5. API design if applicable
                
                Provide detailed architectural decisions.
                """,
                agent=self.architect,
                expected_output="Complete system architecture with tech stack, components, and file structure"
            )
            
            # Development Task
            development_task = Task(
                description=f"""
                Generate production-ready code for: "{prompt}"
                
                Based on the architecture design, create:
                1. All necessary source files
                2. Configuration files
                3. Documentation
                4. Setup instructions
                
                Ensure code is:
                - Well-structured and modular
                - Properly documented
                - Following best practices
                - Ready for deployment
                
                Generate substantial, complete implementations.
                """,
                agent=self.developer,
                expected_output="Complete codebase with all necessary files and documentation"
            )
            
            # Quality Task
            quality_task = Task(
                description=f"""
                Validate the generated project for: "{prompt}"
                
                Review:
                1. Code quality and completeness
                2. Architecture compliance
                3. Best practices adherence
                4. Documentation quality
                5. Overall project coherence
                
                Provide a quality score (1-10) and improvement recommendations.
                """,
                agent=self.quality_agent,
                expected_output="Quality assessment with score and recommendations"
            )
            
            # Create crew
            crew = Crew(
                agents=[self.memory_agent, self.architect, self.developer, self.quality_agent],
                tasks=[memory_task, architecture_task, development_task, quality_task],
                process=Process.sequential,
                verbose=2
            )
            
            # Execute
            try:
                result = crew.kickoff()
                
                # Parse and process results
                generated_files = self._extract_code_from_result(result)
                quality_score = self._extract_quality_score(result)
                
                # Save files
                saved_count = self._save_files(generated_files, project_name)
                
                print(f"\n🎉 CREWAI COMPLETE!")
                print(f"📊 Quality Score: {quality_score}/10")
                print(f"📁 Files Generated: {saved_count}")
                
                return {
                    'best_validation_score': quality_score,
                    'generated_code': generated_files,
                    'crew_result': str(result),
                    'achieved_target': quality_score >= 6.0,
                    'saved_files_count': saved_count
                }
                
            except Exception as e:
                print(f"❌ CrewAI execution failed: {e}")
                return {
                    'best_validation_score': 0,
                    'generated_code': {},
                    'error': str(e),
                    'achieved_target': False
                }
        
        def _extract_code_from_result(self, result) -> Dict[str, str]:
            """Extract code files from CrewAI result"""
            # This would need to be customized based on how your agents output code
            # For now, return a simple structure
            
            result_text = str(result)
            generated_files = {}
            
            # Look for code blocks in the result
            import re
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', result_text, re.DOTALL)
            
            for i, (language, code) in enumerate(code_blocks):
                if len(code.strip()) > 100:  # Only substantial code blocks
                    extension = self._get_extension(language)
                    filename = f"generated_file_{i+1}.{extension}"
                    generated_files[filename] = code.strip()
            
            return generated_files
        
        def _get_extension(self, language: str) -> str:
            """Get file extension for language"""
            extensions = {
                'python': 'py',
                'javascript': 'js', 
                'typescript': 'ts',
                'html': 'html',
                'css': 'css',
                'sql': 'sql',
                'json': 'json'
            }
            return extensions.get(language.lower(), 'txt')
        
        def _extract_quality_score(self, result) -> float:
            """Extract quality score from result"""
            result_text = str(result).lower()
            
            # Look for score patterns
            import re
            score_matches = re.findall(r'score[:\s]+(\d+(?:\.\d+)?)', result_text)
            
            if score_matches:
                try:
                    return float(score_matches[-1])  # Take the last score found
                except:
                    pass
            
            # Default score based on result quality
            if len(result_text) > 1000:
                return 7.0
            elif len(result_text) > 500:
                return 5.0
            else:
                return 3.0
        
        def _save_files(self, generated_files: Dict[str, str], project_name: str) -> int:
            """Save generated files to disk"""
            output_dir = Path(self.save_folder) / project_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            saved_count = 0
            for filename, content in generated_files.items():
                if isinstance(content, str) and content.strip():
                    file_path = output_dir / filename
                    
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
                'project_name': project_name,
                'files_count': saved_count,
                'output_dir': str(output_dir.absolute())
            }
            
            with open(output_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📊 Saved {saved_count} files to: {output_dir.absolute()}")
            return saved_count


def create_crewai_pipeline(save_folder: str = "crewai_generated") -> CrewAIPipeline:
    """Factory function"""
    return CrewAIPipeline(save_folder)
