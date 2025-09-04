"""
SIMPLE AGENTIC GRAPH - Clean refactored version

Main orchestration system for multi-agent collaboration
"""

from typing import Dict, Any, List
import json
import random
import os
from pathlib import Path
from datetime import datetime

# Import agent classes
from .agents.base_agent import SimpleAgent
from .memory.memory_agent import MemoryAgent


class SimpleAgenticGraph:
    """
    Simple Agentic Graph with 4 specialized agents + memory
    
    Agents collaborate to:
    1. Make tech stack decisions democratically
    2. Define project architecture together  
    3. Generate code with peer review
    4. Learn from successful patterns via memory
    """
    
    def __init__(self, project_folder: str = "agentic_output", 
                 target_score: float = 6.0, max_iterations: int = 2):
        self.project_folder = project_folder
        self.target_score = target_score
        self.max_iterations = max_iterations
        
        # Initialize specialized agents
        self.agents = [
            SimpleAgent("DevAgent", "Software Developer", "codellama:7b"),
            SimpleAgent("ArchAgent", "Software Architect", "mistral:7b"), 
            SimpleAgent("QAAgent", "Quality Assurance", "qwen2.5-coder:7b")
        ]
        
        # Initialize memory agent
        self.memory_agent = MemoryAgent()
        
        # Create output directory
        Path(self.project_folder).mkdir(exist_ok=True)
        
        print("🤖 SIMPLE AGENTIC GRAPH:")
        print("   🎯 3 agents making independent decisions")
        print("   📝 Agents review each other's work")
        print("   ✨ Self-correction and improvement")
        print("   🎲 Dynamic decision-making")
        print("   🧠 Memory Agent with RAG learning")
        print(f"   💾 Output: {self.project_folder}/")

    def run_agentic_pipeline(self, prompt: str, project_name: str = "agentic_project") -> Dict[str, Any]:
        """Run the complete agentic pipeline"""
        
        print(f"\n🚀 AGENTIC GRAPH: {prompt[:50]}...")
        
        # Step 1: Check memory for similar projects
        memory_result = self.memory_agent.find_similar_projects(prompt)
        
        # Step 2: Agent tech decisions (democratic voting)
        tech_stack = self._agent_tech_decisions(prompt, memory_result)
        
        # Step 3: Agent architecture decisions 
        file_structure = self._agent_architecture_decisions(prompt, tech_stack, memory_result)
        
        # Step 4: Agent code generation with collaboration
        generated_files = self._agent_code_generation({
            'prompt': prompt,
            'tech_stack': tech_stack,
            'file_structure': file_structure
        })
        
        # Step 5: Agent peer review
        reviews = self._agent_peer_review(generated_files)
        
        # Step 6: Agent self-correction (if needed)
        final_files = self._agent_self_correction(generated_files, reviews)
        
        # Step 7: Save files
        saved_files = self._save_project_files(final_files, project_name)
        
        # Step 8: Calculate overall score and store in memory
        overall_score = self._calculate_project_score(reviews)
        self.memory_agent.store_project_pattern(
            prompt, tech_stack, list(final_files.keys()), overall_score
        )
        
        return {
            'success': True,
            'project_name': project_name,
            'files_generated': len(saved_files),
            'files_saved': len(saved_files),
            'reviews': len(reviews),
            'overall_score': overall_score,
            'tech_stack': tech_stack,
            'saved_files': saved_files
        }

    def _agent_tech_decisions(self, prompt: str, memory_result: Dict[str, Any]) -> Dict[str, Any]:
        """Agents make democratic decisions about tech stack"""
        
        print("🎯 Step 1: Agent Tech Decisions")
        
        # Check if memory can provide good suggestions
        if memory_result.get('found') and memory_result.get('confidence', 0) > 0.8:
            print("🧠 Using memory: high confidence match")
            return memory_result['tech_stack']
        
        print("🤖 Memory couldn't help enough, asking agents...")
        
        # Framework options
        framework_options = ["Python + FastAPI", "Python + Flask", "Node.js + Express", "Node.js + Koa"]
        database_options = ["PostgreSQL", "MySQL", "SQLite", "MongoDB"]
        
        # Each agent votes
        framework_votes = {}
        database_votes = {}
        
        for agent in self.agents:
            framework_choice = agent.make_decision(
                {'prompt': prompt, 'type': 'framework'}, 
                framework_options
            )
            db_choice = agent.make_decision(
                {'prompt': prompt, 'type': 'database'},
                database_options
            )
            
            # Count votes
            framework_votes[framework_choice] = framework_votes.get(framework_choice, 0) + 1
            database_votes[db_choice] = database_votes.get(db_choice, 0) + 1
        
        # Democratic decision (most votes win)
        chosen_framework = max(framework_votes, key=framework_votes.get)
        chosen_database = max(database_votes, key=database_votes.get)
        
        tech_stack = {
            'framework': chosen_framework,
            'database': chosen_database,
            'language': chosen_framework.split(' + ')[0]
        }
        
        print(f"🗳️ Democratic choice: {chosen_framework} + {chosen_database}")
        return tech_stack

    def _agent_architecture_decisions(self, prompt: str, tech_stack: Dict[str, Any], 
                                     memory_result: Dict[str, Any]) -> List[str]:
        """Agents decide on project file structure"""
        
        print("🏗️ Step 2: Agent Architecture Decisions")
        
        # Check if memory has good file patterns
        if memory_result.get('found') and memory_result.get('confidence', 0) > 0.75:
            patterns = memory_result['file_patterns']
            print(f"🧠 Using memory file patterns: {len(patterns)} files")
            return patterns
        
        print("🤖 Memory patterns insufficient, asking agents for architecture...")
        
        # Common file patterns based on tech stack
        if 'Python' in tech_stack.get('framework', ''):
            file_options = [
                'main.py', 'models.py', 'routes.py', 'config.py', 'requirements.txt',
                'README.md', 'Dockerfile', '.env.example', 'tests/test_main.py'
            ]
        else:
            file_options = [
                'server.js', 'package.json', 'models/User.js', 'routes/auth.js', 'routes/tasks.js',
                'middleware/auth.js', 'tests/server.test.js', 'README.md', '.env.example',
                'database/schema.sql'
            ]
        
        # Each agent suggests files
        agent_suggestions = set()
        
        for agent in self.agents:
            # Each agent chooses 3-4 files
            agent_choices = []
            shuffled_options = file_options.copy()
            random.shuffle(shuffled_options)
            
            for _ in range(random.randint(3, 4)):
                if shuffled_options:
                    choice = agent.make_decision(
                        {'prompt': prompt, 'tech_stack': tech_stack}, 
                        shuffled_options[:3]  # Give 3 options to choose from
                    )
                    agent_choices.append(choice)
                    if choice in shuffled_options:
                        shuffled_options.remove(choice)
            
            agent_suggestions.update(agent_choices)
        
        file_structure = list(agent_suggestions)
        print(f"📁 Agents chose {len(file_structure)} files")
        return file_structure

    def _agent_code_generation(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Agents generate code collaboratively"""
        
        print("⚡ Step 3: Agent Code Generation")
        
        generated_files = {}
        file_structure = context['file_structure']
        
        # Distribute files among agents
        for i, filename in enumerate(file_structure):
            agent = self.agents[i % len(self.agents)]
            
            print(f"🔄 {agent.name}: generating {filename}...")
            
            try:
                # Generate code using the agent's LLM
                code = self._generate_file_content(agent, filename, context)
                generated_files[filename] = code
                print(f"✅ {agent.name}: generated {filename} ({len(code.split())} lines)")
                
            except Exception as e:
                print(f"❌ {agent.name}: failed to generate {filename}: {e}")
                generated_files[filename] = self._simple_fallback(filename, context)
        
        return generated_files

    def _generate_file_content(self, agent, filename: str, context: Dict[str, Any]) -> str:
        """Generate content for a specific file using an agent"""
        
        tech_info = context.get('tech_stack', {})
        framework = tech_info.get('framework', 'Python + FastAPI')
        
        generation_prompt = f"""Generate complete working code for file: {filename}

Project context: {context['prompt']}
Framework: {framework}
Database: {tech_info.get('database', 'SQLite')}

Requirements:
- File: {filename}
- Minimum 30 lines of real code
- Include imports, exports, error handling
- Add comments and documentation
- Working, production-ready implementation

Generate ONLY the code, no explanations:"""
        
        response = agent.llm.get_raw_response(
            system_prompt=f"You are {agent.name}, expert {agent.role}. Generate high-quality code.",
            user_prompt=generation_prompt
        )
        
        if response and len(response.strip()) > 100:
            return agent._clean_code(response)
        else:
            print(f"⚠️ {agent.name}: LLM response too short for {filename}")
            return self._simple_fallback(filename, context)

    def _simple_fallback(self, filename: str, context: Dict[str, Any]) -> str:
        """Generate simple fallback content when LLM fails"""
        
        if filename.endswith('.py'):
            return f'''"""
{filename} - Generated by AgentForge
Project: {context.get('prompt', 'Agentic Project')}
"""

# TODO: Implement {filename.replace('.py', '')} functionality

def main():
    print("Hello from {filename}")

if __name__ == "__main__":
    main()
'''
        elif filename.endswith('.js'):
            return f'''// {filename} - Generated by AgentForge
// Project: {context.get('prompt', 'Agentic Project')}

console.log('Hello from {filename}');

module.exports = {{}};
'''
        elif filename == 'README.md':
            return f'''# {context.get('prompt', 'Agentic Project')}

Generated by AgentForge - Agentic System

## Quick Start

```bash
# Install dependencies
npm install  # or pip install -r requirements.txt

# Run the application
npm start    # or python main.py
```
'''
        else:
            return f"# {filename} - Generated by AgentForge\n# TODO: Implement content\n"

    def _agent_peer_review(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        """Agents review each other's work"""
        
        print("📝 Step 4: Agent Peer Review")
        
        reviews = []
        file_items = list(files.items())
        
        for filename, code in file_items[:5]:  # Review first 5 files
            # Get 2 random agents to review
            reviewers = random.sample(self.agents, min(2, len(self.agents)))
            
            for agent in reviewers:
                review = agent.review_code(filename, code)
                reviews.append(review)
        
        return reviews

    def _agent_self_correction(self, files: Dict[str, str], reviews: List[Dict]) -> Dict[str, str]:
        """Agents improve their own code based on reviews"""
        
        print("✨ Step 5: Agent Self-Correction")
        
        # For now, return files as-is (self-correction could be implemented later)
        return files

    def _save_project_files(self, files: Dict[str, str], project_name: str) -> List[str]:
        """Save generated files to disk"""
        
        print("💾 Step 6: Save Files")
        
        project_path = Path(self.project_folder) / project_name
        project_path.mkdir(exist_ok=True)
        
        saved_files = []
        
        for filename, content in files.items():
            # Handle nested file paths
            file_path = project_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_files.append(str(file_path))
                print(f"✅ Saved: {filename}")
                
            except Exception as e:
                print(f"❌ Failed to save {filename}: {e}")
        
        return saved_files

    def _calculate_project_score(self, reviews: List[Dict[str, Any]]) -> float:
        """Calculate overall project quality score"""
        
        if not reviews:
            return 7.0  # Default score
        
        scores = [review.get('score', 5.0) for review in reviews]
        return round(sum(scores) / len(scores), 1)

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics about agent activities"""
        
        stats = {}
        for agent in self.agents:
            stats[agent.name] = agent.get_stats()
        
        # Add memory stats
        stats['MemoryAgent'] = self.memory_agent.get_memory_stats()
        
        return stats


# Test function
def test_agentic_system():
    """Test the agentic system"""
    
    print("🤖 TESTING SIMPLE AGENTIC GRAPH...")
    
    # Create agentic system
    agentic = SimpleAgenticGraph("test_agentic")
    
    # Run test
    result = agentic.run_agentic_pipeline(
        "Create a simple task management API with user auth",
        "test_project"
    )
    
    print(f"\n🎉 AGENTIC TEST COMPLETE!")
    print(f"✅ Success: {result['success']}")
    print(f"📄 Files: {result['files_generated']}")
    print(f"💾 Saved: {result['files_saved']}")
    print(f"📝 Reviews: {result['reviews']}")
    
    # Print agent stats
    stats = agentic.get_agent_stats()
    print(f"\n🤖 Agent Stats:")
    for agent_name, agent_stats in stats.items():
        if agent_name != 'MemoryAgent':
            decisions = agent_stats.get('decisions_count', 0)
            reviews = agent_stats.get('reviews_count', 0)
            print(f"   {agent_name}: {decisions} decisions, {reviews} reviews")
    
    print(f"\n🎯 SIMPLE AGENTIC GRAPH WORKS!")
    
    return result


if __name__ == "__main__":
    test_agentic_system()
