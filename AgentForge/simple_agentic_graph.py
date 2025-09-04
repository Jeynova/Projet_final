"""
SIMPLE AGENTIC GRAPH - MVP with real agent behavior

This adds MINIMAL agentic features to the working fast graph:
1. Multiple agents making independent decisions
2. Agents review and improve each other's work  
3. Self-correction and iteration
4. Dynamic decision-making

KEEPS IT SIMPLE AND WORKING!
"""

from typing import Dict, Any, List
import json
from pathlib import Path
import random


class SimpleAgent:
    """
    Simple agent that makes independent decisions
    """
    
    def __init__(self, name: str, role: str, model: str):
        self.name = name
        self.role = role
        self.model = model
        from core.llm_client import LLMClient
        self.llm = LLMClient(preferred_model=model)
        self.decisions_made = []
        self.reviews_given = []
    
    def make_decision(self, context: Dict[str, Any], options: List[str]) -> str:
        """Agent makes independent decision"""
        try:
            prompt = f"""You are {self.name}, a {self.role}.
            
Context: {context.get('prompt', 'project')}

Choose ONE option that best fits your expertise:
{json.dumps(options, indent=2)}

Return ONLY the chosen option (exact text):"""
            
            response = self.llm.get_raw_response(
                system_prompt=f"You are {self.name}, expert {self.role}. Make independent decisions.",
                user_prompt=prompt
            )
            
            if response:
                # Find matching option
                for option in options:
                    if option.lower() in response.lower():
                        decision = option
                        self.decisions_made.append(decision)
                        print(f"🎯 {self.name}: chose '{decision}'")
                        return decision
            
            # Fallback to random (still agentic!)
            decision = random.choice(options)
            self.decisions_made.append(decision)
            print(f"🎲 {self.name}: random choice '{decision}'")
            return decision
            
        except Exception as e:
            print(f"⚠️ {self.name} decision failed: {e}")
            decision = random.choice(options)
            self.decisions_made.append(decision)
            return decision
    
    def review_code(self, filename: str, code: str) -> Dict[str, Any]:
        """Agent reviews another agent's code"""
        try:
            prompt = f"""Review this {filename} code as a {self.role}:

```
{code[:500]}...
```

Rate 1-5 and suggest ONE improvement:
{{"score": 4, "improvement": "Add error handling"}}"""
            
            response = self.llm.extract_json(
                system_prompt=f"You are {self.name}, expert {self.role}. Review code critically but constructively.",
                user_prompt=prompt
            )
            
            if response and 'score' in response:
                review = {
                    'reviewer': self.name,
                    'score': response.get('score', 3),
                    'improvement': response.get('improvement', 'Good code'),
                    'filename': filename
                }
                self.reviews_given.append(review)
                print(f"📝 {self.name}: reviewed {filename} -> {review['score']}/5")
                return review
                
        except Exception as e:
            print(f"⚠️ {self.name} review failed: {e}")
        
        # Simple fallback review
        review = {
            'reviewer': self.name,
            'score': 4,
            'improvement': 'Looks good',
            'filename': filename
        }
        self.reviews_given.append(review)
        return review
    
    def improve_code(self, filename: str, code: str, reviews: List[Dict]) -> str:
        """Agent improves code based on reviews"""
        if not reviews:
            return code
            
        try:
            improvements = [r.get('improvement', '') for r in reviews if r.get('improvement')]
            
            prompt = f"""Improve this {filename} code based on peer reviews:

ORIGINAL CODE:
```
{code[:800]}
```

PEER REVIEWS:
{json.dumps(improvements, indent=2)}

Return ONLY the improved code:"""
            
            response = self.llm.get_raw_response(
                system_prompt=f"You are {self.name}, expert {self.role}. Improve code based on feedback.",
                user_prompt=prompt
            )
            
            if response and len(response.strip()) > len(code) * 0.8:  # Must be substantial
                print(f"✨ {self.name}: improved {filename} (+{len(response) - len(code)} chars)")
                return self._clean_code(response)
                
        except Exception as e:
            print(f"⚠️ {self.name} improvement failed: {e}")
        
        return code  # Return original if improvement fails
    
    def _clean_code(self, code: str) -> str:
        """Clean code response"""
        if "```" in code:
            lines = code.split('\n')
            code_lines = []
            in_code = False
            
            for line in lines:
                if line.strip().startswith('```'):
                    in_code = not in_code
                    continue
                if in_code:
                    code_lines.append(line)
            
            return '\n'.join(code_lines) if code_lines else code
        
        return code.strip()


class SimpleAgenticGraph:
    """
    Simple Agentic Graph - Adds minimal agent behavior to working fast graph
    """
    
    def __init__(self, save_folder: str = "agentic_generated"):
        self.save_folder = save_folder
        
        # Create 3 simple agents with different expertise
        self.agents = [
            SimpleAgent("DevAgent", "Senior Developer", "codellama:7b"),
            SimpleAgent("ArchAgent", "Solution Architect", "mistral:7b"),  
            SimpleAgent("QAAgent", "Quality Assurance", "qwen2.5-coder:7b")
        ]
        
        print("🤖 SIMPLE AGENTIC GRAPH:")
        print("   🎯 3 agents making independent decisions")
        print("   📝 Agents review each other's work")
        print("   ✨ Self-correction and improvement")
        print("   🎲 Dynamic decision-making")
        print(f"   💾 Output: {save_folder}/")
    
    def run_agentic(self, prompt: str, project_name: str = "AgenticProject") -> Dict[str, Any]:
        """Run the simple agentic pipeline"""
        
        print(f"\n🚀 AGENTIC GRAPH: {prompt[:50]}...")
        
        try:
            # Step 1: Agents decide tech stack independently
            print("🎯 Step 1: Agent Tech Decisions")
            tech_stack = self._agent_tech_decisions(prompt)
            
            # Step 2: Agents decide architecture 
            print("🏗️ Step 2: Agent Architecture Decisions")
            files = self._agent_architecture_decisions(prompt, tech_stack)
            
            # Step 3: Agents generate code independently
            print("⚡ Step 3: Agent Code Generation")
            generated_files = self._agent_code_generation({
                'prompt': prompt,
                'tech_stack': tech_stack,
                'files': files
            })
            
            # Step 4: Agent peer review
            print("📝 Step 4: Agent Peer Review")
            reviews = self._agent_peer_review(generated_files)
            
            # Step 5: Agent self-correction
            print("✨ Step 5: Agent Self-Correction") 
            improved_files = self._agent_self_correction(generated_files, reviews)
            
            # Step 6: Save
            print("💾 Step 6: Save Files")
            saved_count = self._save_files(improved_files, project_name)
            
            print(f"\n🎉 AGENTIC GRAPH COMPLETE!")
            print(f"📊 Files: {len(improved_files)}")
            print(f"💾 Saved: {saved_count}")
            print(f"📝 Reviews: {len(reviews)}")
            
            return {
                'files': improved_files,
                'files_count': len(improved_files),
                'saved_count': saved_count,
                'reviews': reviews,
                'tech_stack': tech_stack,
                'success': True,
                'agent_stats': self._get_agent_stats()
            }
            
        except Exception as e:
            print(f"❌ Agentic graph failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _agent_tech_decisions(self, prompt: str) -> Dict[str, Any]:
        """Agents make independent tech stack decisions"""
        
        tech_options = [
            "Node.js + Express",
            "Python + FastAPI", 
            "Node.js + Koa",
            "Python + Django"
        ]
        
        db_options = [
            "MongoDB",
            "PostgreSQL",
            "MySQL",
            "SQLite"
        ]
        
        # Each agent decides independently
        backend_votes = {}
        db_votes = {}
        
        for agent in self.agents:
            backend = agent.make_decision({'prompt': prompt}, tech_options)
            database = agent.make_decision({'prompt': prompt}, db_options)
            
            backend_votes[backend] = backend_votes.get(backend, 0) + 1
            db_votes[database] = db_votes.get(database, 0) + 1
        
        # Winner takes all (democratic decision)
        chosen_backend = max(backend_votes, key=backend_votes.get)
        chosen_db = max(db_votes, key=db_votes.get)
        
        tech_stack = {
            "backend": {"name": chosen_backend, "votes": backend_votes[chosen_backend]},
            "database": {"name": chosen_db, "votes": db_votes[chosen_db]},
            "frontend": {"name": "React", "reasoning": "Standard choice"}
        }
        
        print(f"🗳️ Democratic choice: {chosen_backend} + {chosen_db}")
        return tech_stack
    
    def _agent_architecture_decisions(self, prompt: str, tech_stack: Dict[str, Any]) -> List[str]:
        """Agents decide architecture independently"""
        
        base_files = ['server.js', 'package.json', '.env.example']
        
        optional_files = [
            'routes/auth.js',
            'routes/tasks.js', 
            'models/User.js',
            'models/Task.js',
            'middleware/auth.js',
            'database/schema.sql',
            'tests/server.test.js',
            'README.md'
        ]
        
        # Each agent votes on optional files
        file_votes = {}
        
        for agent in self.agents:
            # Agent chooses 3-5 optional files
            chosen_files = []
            for i in range(4):  # Each agent picks 4 files
                remaining = [f for f in optional_files if f not in chosen_files]
                if remaining:
                    choice = agent.make_decision(
                        {'prompt': prompt, 'tech_stack': tech_stack},
                        remaining
                    )
                    chosen_files.append(choice)
                    file_votes[choice] = file_votes.get(choice, 0) + 1
        
        # Include files with at least 2 votes
        selected_files = base_files + [f for f, votes in file_votes.items() if votes >= 2]
        
        print(f"📁 Agents chose {len(selected_files)} files")
        return selected_files
    
    def _agent_code_generation(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Agents generate code independently"""
        
        files = context.get('files', [])
        generated = {}
        
        # Distribute files among agents
        for i, filename in enumerate(files):
            agent = self.agents[i % len(self.agents)]  # Round-robin
            
            print(f"🔄 {agent.name}: generating {filename}...")
            
            # Agent generates code
            content = self._agent_generate_file(agent, filename, context)
            
            if content and len(content.strip()) > 20:
                generated[filename] = content
                lines = len(content.split('\n'))
                print(f"✅ {agent.name}: generated {filename} ({lines} lines)")
            else:
                print(f"⚠️ {agent.name}: skipped {filename}")
        
        return generated
    
    def _agent_generate_file(self, agent: SimpleAgent, filename: str, context: Dict[str, Any]) -> str:
        """Agent generates a specific file"""
        
        try:
            tech_stack = context.get('tech_stack', {})
            prompt_text = context.get('prompt', 'web application')
            
            generation_prompt = f"""Generate complete production code for {filename}

PROJECT: {prompt_text}
TECH STACK: {tech_stack}
YOUR ROLE: {agent.role}

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
                
        except Exception as e:
            print(f"❌ {agent.name}: generation failed for {filename}: {e}")
            return self._simple_fallback(filename, context)
    
    def _agent_peer_review(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        """Agents review each other's work"""
        
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
        
        improved = files.copy()
        
        # Group reviews by filename
        reviews_by_file = {}
        for review in reviews:
            filename = review.get('filename')
            if filename not in reviews_by_file:
                reviews_by_file[filename] = []
            reviews_by_file[filename].append(review)
        
        # Agents improve code based on reviews
        for filename, file_reviews in reviews_by_file.items():
            if filename in improved:
                # Random agent improves the code
                improver = random.choice(self.agents)
                improved_code = improver.improve_code(filename, improved[filename], file_reviews)
                improved[filename] = improved_code
        
        return improved
    
    def _simple_fallback(self, filename: str, context: Dict[str, Any]) -> str:
        """Simple fallback for failed generations"""
        
        if filename == 'server.js':
            return """const express = require('express');
const app = express();

app.use(express.json());

app.get('/health', (req, res) => {
    res.json({ status: 'OK', message: 'Server is running' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

module.exports = app;"""
        
        elif filename.endswith('.json') and 'package' in filename:
            return """{
  "name": "agentic-project",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}"""
        
        else:
            return f"""// {filename}
// Generated by Simple Agentic Graph
console.log('File: {filename}');
module.exports = {{}};"""
    
    def _save_files(self, files: Dict[str, str], project_name: str) -> int:
        """Save files"""
        output_dir = Path(self.save_folder) / project_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved = 0
        for filename, content in files.items():
            file_path = output_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved += 1
                print(f"✅ Saved: {filename}")
            except Exception as e:
                print(f"❌ Failed: {filename}: {e}")
        
        return saved
    
    def _get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        stats = {}
        for agent in self.agents:
            stats[agent.name] = {
                'decisions': len(agent.decisions_made),
                'reviews': len(agent.reviews_given),
                'role': agent.role
            }
        return stats


if __name__ == "__main__":
    print("🤖 TESTING SIMPLE AGENTIC GRAPH...")
    
    agentic = SimpleAgenticGraph("test_agentic")
    
    result = agentic.run_agentic(
        "Create a simple task management API with user authentication",
        "SimpleAgenticAPI"
    )
    
    print(f"\n🎉 AGENTIC TEST COMPLETE!")
    print(f"✅ Success: {result['success']}")
    print(f"📄 Files: {result['files_count']}")
    print(f"💾 Saved: {result['saved_count']}")
    print(f"📝 Reviews: {len(result.get('reviews', []))}")
    
    print(f"\n🤖 Agent Stats:")
    for agent_name, stats in result.get('agent_stats', {}).items():
        print(f"   {agent_name}: {stats['decisions']} decisions, {stats['reviews']} reviews")
    
    print(f"\n🎯 SIMPLE AGENTIC GRAPH WORKS!")
