"""Enhanced Dynamic Orchestrator v2
Fixes the clarification halting issue and adds smart defaults.
Can auto-proceed or accept pre-provided answers.
"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re
from .memory_store import MemoryStore
from .agent_base import AgentResult
from .agents_impl import (
    MemoryAgent, ClarifyAgent, TechSelectAgent, ArchitectureAgent, ArchitectureValidationAgent, ArchitectureExpandAgent, ScaffoldAgent, CodeGenAgent,
    DatabaseAgent, DeploymentSelectAgent, InfraAgent, DockerComposeAgent, KubeAgent,
    TestAgent, IngestAgent, EvaluationAgent, KnowledgeStoreAgent, RemediationAgent, PackageAgent, QuickstartAgent, ValidateAgent, ManifestAgent
)
from .rag_store import RAGStore

class SmartClarifyAgent(ClarifyAgent):
    """Enhanced ClarifyAgent that can auto-proceed with smart defaults"""
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Only run clarify if explicitly requested or if we detect missing context
        if 'force_clarify' in state:
            return super().can_run(state)
        return False  # Skip clarify by default to match original behavior
    
    def auto_resolve_questions(self, prompt: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-resolve questions with smart defaults based on prompt analysis"""
        lower = prompt.lower()
        answers = {}
        
        # Smart domain detection
        if 'blog' in lower or 'post' in lower or 'article' in lower:
            answers['domain'] = 'blog'
        elif 'shop' in lower or 'ecommerce' in lower or 'product' in lower:
            answers['domain'] = 'ecommerce'
        elif 'task' in lower or 'todo' in lower:
            answers['domain'] = 'task-management'
        elif 'chat' in lower or 'message' in lower:
            answers['domain'] = 'messaging'
        elif 'api' in lower:
            answers['domain'] = 'api'
        else:
            answers['domain'] = 'generic-app'
        
        # Smart entity extraction
        entities = []
        # Look for plural nouns that might be entities
        candidates = re.findall(r'\b([A-Za-z]{3,})s\b', prompt)
        # Filter common non-entity words
        filtered_candidates = [
            c for c in candidates 
            if c.lower() not in ['users', 'pages', 'items', 'things', 'features', 'options', 'details']
        ]
        if filtered_candidates:
            entities = filtered_candidates[:3]  # Take first 3
        else:
            # Fallback based on domain
            domain_entities = {
                'blog': ['posts', 'comments'],
                'ecommerce': ['products', 'orders'],
                'task-management': ['tasks', 'projects'],
                'messaging': ['messages', 'conversations'],
                'api': ['resources', 'endpoints']
            }
            entities = domain_entities.get(answers['domain'], ['items'])
        answers['entities'] = entities
        
        # Smart auth detection
        answers['auth'] = any(word in lower for word in ['auth', 'login', 'user', 'account', 'register', 'signup'])
        
        # Smart persistence detection
        answers['persistence'] = any(word in lower for word in ['database', 'db', 'store', 'save', 'persist', 'data'])
        
        # Smart deployment detection
        if 'docker' in lower or 'compose' in lower:
            answers['deployment'] = 'docker-compose'
        elif 'k8s' in lower or 'kubernetes' in lower:
            answers['deployment'] = 'kubernetes'
        else:
            answers['deployment'] = 'docker-compose'  # Default
        
        return answers

class EnhancedDynamicOrchestrator:
    def __init__(self, project_root: Path, memory: MemoryStore | None = None):
        self.memory = memory or MemoryStore()
        self.project_root = project_root
        self.state: Dict[str, Any] = {}
        self.log: List[str] = []
        self.rag = RAGStore()
        
        # Use enhanced clarify agent
        smart_clarify = SmartClarifyAgent()
        
        self.agents = [
            MemoryAgent(self.memory, self.rag),
            smart_clarify,
            TechSelectAgent(),
            ArchitectureAgent(),
            ArchitectureValidationAgent(),
            ArchitectureExpandAgent(),
            ScaffoldAgent(project_root),
            CodeGenAgent(project_root),
            ManifestAgent(project_root),
            ValidateAgent(project_root),
            DatabaseAgent(project_root),
            DeploymentSelectAgent(),
            InfraAgent(project_root),
            DockerComposeAgent(project_root),
            KubeAgent(project_root),
            TestAgent(project_root),
            QuickstartAgent(project_root),
            IngestAgent(project_root, self.rag),
            EvaluationAgent(),
            KnowledgeStoreAgent(project_root, self.rag),  # Store successful patterns in RAG!
            RemediationAgent(project_root),
            PackageAgent(project_root),
        ]

    def _candidate_agents(self) -> List:
        return [a for a in self.agents if a.can_run(self.state)]

    def _run_pipeline(self, prompt: str, max_steps: int = 25, answers: Optional[Dict[str, Any]] = None, auto_proceed: bool = True) -> Dict[str, Any]:
        """Run the orchestration pipeline with optional answers and auto-proceed"""
        self.state = {'prompt': prompt}
        if answers:
            self.state['answers'] = answers
        
        steps = 0
        while steps < max_steps:
            candidates = self._candidate_agents()
            if not candidates:
                self.log.append('No more agents can run. Stopping.')
                break
                
            # Score agents by success rate + feedback + stage heuristics
            def score_agent(agent):
                base_score = self.memory.success_rate(agent.id)
                # Feedback is already included in success_rate method
                return base_score
            
            agent = max(candidates, key=score_agent)
            self.log.append(f'Running agent: {agent.id}')
            
            try:
                result = agent.run(self.state)
                if result:
                    # Use correct state key (special case for tech_select -> 'tech')
                    key = agent.id if agent.id not in ('tech_select',) else 'tech'
                    self.state[key] = result
                    self.log.append(f'Agent {agent.id} completed successfully')
                    self.memory.record_agent_invocation(agent.id, True)
                    
                    # Special handling for clarify agent
                    if agent.id == 'clarify' and isinstance(agent, SmartClarifyAgent):
                        if result.get('questions') and auto_proceed:
                            self.log.append(f'Auto-resolving {len(result["questions"])} clarification questions...')
                            auto_answers = agent.auto_resolve_questions(prompt, self.state)
                            # Merge auto answers and re-run clarify
                            if 'answers' not in self.state:
                                self.state['answers'] = {}
                            self.state['answers'].update(auto_answers)
                            
                            # Re-run clarify with answers
                            result = agent.run(self.state)
                            self.state[key] = result
                            self.log.append(f'Clarification auto-resolved: {list(auto_answers.keys())}')
                    
            except Exception as e:
                self.log.append(f"Agent {agent.id} error: {e}")
                self.memory.record_agent_invocation(agent.id, False)
                self.memory.record_decision({'keys': list(self.state.keys())}, agent.id, 'fail')
                
            steps += 1
            
            # Original clarification gating (only if auto_proceed is False)
            if agent.id == 'clarify' and not auto_proceed:
                clar = self.state.get('clarify', {})
                if clar.get('questions'):
                    self.log.append('Clarification required. Halting until answers provided.')
                    break
                    
            # Allow remediation after evaluation if score low (<65)
            # Also allow knowledge storage to run after successful evaluation
            if 'evaluate' in self.state:
                score = self.state.get('evaluate', {}).get('score', 0)
                # Stop if package is done AND either score is good OR remediation is done AND knowledge is stored (if applicable)
                if 'package' in self.state:
                    if score >= 65:
                        # Allow knowledge storage for high scores before stopping
                        if score >= 70 and 'knowledge_store' not in self.state:
                            continue  # Keep running to store knowledge
                        break
                    elif 'remediate' in self.state:
                        break
                    
        # Persist run summary
        tech_stack = self.state.get('tech', {}).get('stack', [])
        artifacts = self.state.get('codegen', {}).get('files', [])
        score = self.state.get('evaluate', {}).get('score', 0)
        self.memory.record_run(prompt, tech_stack, artifacts, score)
        
        # Apply feedback weighting to contributing agents
        agents_used = [l.split(':',1)[1].strip() for l in self.log if l.startswith('Running agent')]
        try:
            self.memory.apply_feedback(agents_used, float(score))
        except Exception:
            pass
            
        return self.state

    def generate(self, prompt: str, answers: Optional[Dict[str, Any]] = None, auto_proceed: bool = True) -> Dict[str, Any]:
        """Main entry point for project generation"""
        self.log.clear()
        self.log.append(f'Starting orchestration for: "{prompt}"')
        
        result = self._run_pipeline(prompt, answers=answers, auto_proceed=auto_proceed)
        
        # Log summary
        files_generated = result.get('codegen', {}).get('files', [])
        self.log.append(f'Pipeline complete. Generated {len(files_generated)} files.')
        
        return result

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m orchestrator_v2.enhanced_orchestrator 'project description'")
        sys.exit(1)
        
    prompt = ' '.join(sys.argv[1:])
    project_root = Path.cwd() / "generated" / f"enhanced-{prompt.replace(' ', '-')[:20]}"
    project_root.mkdir(parents=True, exist_ok=True)
    
    orchestrator = EnhancedDynamicOrchestrator(project_root)
    
    print(f"🚀 Generating project: {prompt}")
    print(f"📂 Output directory: {project_root}")
    print("🤖 Auto-proceeding through clarification questions...")
    
    result = orchestrator.generate(prompt, auto_proceed=True)
    
    print(f"\n📋 Orchestration Log:")
    for entry in orchestrator.log:
        print(f"  {entry}")
    
    files = result.get('codegen', {}).get('files', [])
    print(f"\n✅ Generated {len(files)} files:")
    for file in files:
        print(f"  📄 {file}")
    
    score = result.get('evaluate', {}).get('score', 0)
    print(f"🎯 Quality Score: {score}/100")

if __name__ == '__main__':
    main()
