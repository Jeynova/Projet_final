"""Enhanced Dynamic Orchestrator v2 with detailed logging
Shows exactly when each agent runs and what it accomplishes.
"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import time
import json
import os

# Load environment variables from .env file
from pathlib import Path
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    import dotenv
    dotenv.load_dotenv(env_file)
    print(f"🔧 Loaded .env: AGENTFORGE_LLM={os.getenv('AGENTFORGE_LLM', 'not set')}")

from .memory_store import MemoryStore
from .agent_base import AgentResult
from .agents_impl import (
    MemoryAgent, ClarifyAgent, TechSelectAgent, ArchitectureAgent, ArchitectureValidationAgent, ArchitectureExpandAgent, ScaffoldAgent, CodeGenAgent,
    DatabaseAgent, DeploymentSelectAgent, InfraAgent, DockerComposeAgent, KubeAgent,
    TestAgent, IngestAgent, EvaluationAgent, RemediationAgent, PackageAgent, QuickstartAgent, ValidateAgent, ManifestAgent
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
        import re
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

class LoggedDynamicOrchestrator:
    def __init__(self, project_root: Path, memory: MemoryStore | None = None, verbose: bool = True):
        self.memory = memory or MemoryStore()
        self.project_root = project_root
        self.state: Dict[str, Any] = {}
        self.log: List[str] = []
        self.detailed_log: List[Dict[str, Any]] = []
        self.rag = RAGStore()
        self.verbose = verbose
        
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
            RemediationAgent(project_root),
            PackageAgent(project_root),
        ]

    def _log_agent_start(self, agent, candidates_count: int, score: float):
        """Log when an agent starts"""
        log_entry = {
            'timestamp': time.time(),
            'event': 'agent_start',
            'agent_id': agent.id,
            'agent_class': agent.__class__.__name__,
            'score': score,
            'competitors': candidates_count,
            'state_keys': list(self.state.keys())
        }
        self.detailed_log.append(log_entry)
        
        if self.verbose:
            print(f"\n🤖 [{len(self.detailed_log):02d}] Running: {agent.__class__.__name__} (id: {agent.id})")
            print(f"    📊 Score: {score:.3f} (beat {candidates_count-1} other agents)")
            print(f"    🗂️  Current state: {', '.join(self.state.keys()) if self.state.keys() else 'empty'}")
            
            # Show why this agent can run
            if hasattr(agent, 'can_run'):
                print(f"    ✅ Can run because: {self._explain_can_run(agent)}")

    def _log_agent_success(self, agent, result: Dict[str, Any], duration: float):
        """Log when an agent completes successfully"""
        log_entry = {
            'timestamp': time.time(),
            'event': 'agent_success',
            'agent_id': agent.id,
            'duration': duration,
            'result_keys': list(result.keys()) if result else [],
            'result_summary': self._summarize_result(agent.id, result)
        }
        self.detailed_log.append(log_entry)
        
        if self.verbose:
            print(f"    ✅ Success! ({duration:.2f}s)")
            print(f"    📤 Output: {self._summarize_result(agent.id, result)}")
            if result:
                self._show_result_details(agent.id, result)

    def _log_agent_error(self, agent, error: Exception, duration: float):
        """Log when an agent fails"""
        log_entry = {
            'timestamp': time.time(),
            'event': 'agent_error',
            'agent_id': agent.id,
            'duration': duration,
            'error': str(error),
            'error_type': type(error).__name__
        }
        self.detailed_log.append(log_entry)
        
        if self.verbose:
            print(f"    ❌ Failed! ({duration:.2f}s)")
            print(f"    💥 Error: {type(error).__name__}: {error}")

    def _explain_can_run(self, agent) -> str:
        """Explain why an agent can run"""
        explanations = {
            'memory': "No memory analysis done yet",
            'clarify': "Force clarify mode enabled",
            'tech_select': "No tech stack selected yet",
            'architecture': "Tech stack ready, no architecture yet",
            'arch_validate': "Architecture needs validation",
            'arch_expand': "Architecture might need expansion",
            'scaffold': "Need basic project structure",
            'codegen': "Ready for code generation",
            'manifest': "Need dependency manifest",
            'validate': "Code needs validation",
            'database': "Database setup needed",
            'deploy_select': "Need deployment strategy",
            'infra': "Infrastructure files needed",
            'compose': "Docker Compose setup needed",
            'kube': "Kubernetes setup needed",
            'tests': "Test files needed",
            'quickstart': "Documentation needed",
            'ingest': "Knowledge ingestion needed",
            'evaluate': "Project needs evaluation",
            'remediate': "Issues need fixing",
            'package': "Project needs packaging"
        }
        return explanations.get(agent.id, "Conditions met")

    def _summarize_result(self, agent_id: str, result: Dict[str, Any]) -> str:
        """Create a human-readable summary of agent results"""
        if not result:
            return "No output"
            
        summaries = {
            'memory': lambda r: f"Found {len(r.get('similar', []))} similar projects, confidence: {r.get('confidence', 0):.2f}",
            'tech_select': lambda r: f"Selected: {', '.join(s.get('name', s) if isinstance(s, dict) else str(s) for s in r.get('stack', []))}",
            'architecture': lambda r: f"{len(r.get('files', []))} files, {len(r.get('directories', []))} dirs, pattern: {r.get('pattern', 'N/A')}",
            'arch_validate': lambda r: f"Validated {r.get('file_count', 0)} files, entrypoint: {r.get('has_entrypoint', False)}",
            'arch_expand': lambda r: f"Added {r.get('added', 0)} files, final: {r.get('final_count', 0)}",
            'scaffold': lambda r: f"Created {len(r.get('files', []))} scaffolds",
            'codegen': lambda r: f"Generated {len(r.get('files', []))} code files",
            'manifest': lambda r: f"Created manifest with {len(r.get('dependencies', []))} deps",
            'validate': lambda r: f"Status: {r.get('status', 'unknown')}, {r.get('file_count', 0)} files, {r.get('placeholder_files', 0)} placeholders",
            'database': lambda r: f"DB setup: {r.get('type', 'none')}, {len(r.get('models', []))} models",
            'deploy_select': lambda r: f"Strategy: {r.get('strategy', 'unknown')}",
            'infra': lambda r: f"Created {len(r.get('files', []))} infra files",
            'tests': lambda r: f"Created {len(r.get('created', []))} test files",
            'evaluate': lambda r: f"Score: {r.get('score', 0)}/100, {len(r.get('improvements', []))} suggestions",
            'remediate': lambda r: f"Applied: {r.get('applied', False)}, {len(r.get('actions', []))} actions",
            'package': lambda r: f"Package: {r.get('archive', 'none')}"
        }
        
        summarizer = summaries.get(agent_id, lambda r: f"{len(r)} keys: {', '.join(list(r.keys())[:3])}")
        return summarizer(result)

    def _show_result_details(self, agent_id: str, result: Dict[str, Any]):
        """Show detailed results for important agents"""
        if agent_id == 'tech_select' and 'stack' in result:
            for item in result['stack'][:3]:
                if isinstance(item, dict):
                    print(f"      🔧 {item.get('name', 'unknown')}: {item.get('reasoning', 'no reason')[:50]}...")
        elif agent_id == 'codegen' and 'files' in result:
            print(f"      📁 Files: {', '.join(result['files'][:5])}")
        elif agent_id == 'evaluate':
            score = result.get('score', 0)
            emoji = "🎉" if score >= 80 else "👍" if score >= 65 else "⚠️" if score >= 50 else "🔴"
            print(f"      {emoji} Score: {score}/100")
            improvements = result.get('improvements', [])
            if improvements:
                print(f"      💡 Top improvement: {improvements[0][:60]}...")

    def _candidate_agents(self) -> List:
        return [a for a in self.agents if a.can_run(self.state)]

    def _run_pipeline(self, prompt: str, max_steps: int = 25, answers: Optional[Dict[str, Any]] = None, auto_proceed: bool = True) -> Dict[str, Any]:
        """Run the orchestration pipeline with detailed logging"""
        self.state = {'prompt': prompt}
        if answers:
            self.state['answers'] = answers
        
        if self.verbose:
            print(f"\n🚀 Starting orchestration pipeline")
            print(f"📝 Prompt: '{prompt}'")
            print(f"🎯 Max steps: {max_steps}")
            print(f"🤖 Available agents: {len(self.agents)}")
            print("="*80)
        
        steps = 0
        start_time = time.time()
        
        while steps < max_steps:
            candidates = self._candidate_agents()
            if not candidates:
                if self.verbose:
                    print(f"\n🏁 No more agents can run. Pipeline complete after {steps} steps.")
                break
                
            # Score agents by success rate
            def score_agent(agent):
                base_score = self.memory.success_rate(agent.id)
                return base_score
            
            agent = max(candidates, key=score_agent)
            agent_start_time = time.time()
            
            self._log_agent_start(agent, len(candidates), score_agent(agent))
            
            try:
                result = agent.run(self.state)
                duration = time.time() - agent_start_time
                
                if result:
                    # Use correct state key (special case for tech_select -> 'tech')
                    key = agent.id if agent.id not in ('tech_select',) else 'tech'
                    self.state[key] = result
                    self._log_agent_success(agent, result, duration)
                    self.memory.record_agent_invocation(agent.id, True)
                    
                    # Special handling for clarify agent
                    if agent.id == 'clarify' and isinstance(agent, SmartClarifyAgent):
                        if result.get('questions') and auto_proceed:
                            if self.verbose:
                                print(f"    🔄 Auto-resolving {len(result['questions'])} clarification questions...")
                            auto_answers = agent.auto_resolve_questions(prompt, self.state)
                            if 'answers' not in self.state:
                                self.state['answers'] = {}
                            self.state['answers'].update(auto_answers)
                            
                            result = agent.run(self.state)
                            self.state[key] = result
                            if self.verbose:
                                print(f"    ✨ Auto-resolved: {list(auto_answers.keys())}")
                
            except Exception as e:
                duration = time.time() - agent_start_time
                self._log_agent_error(agent, e, duration)
                self.log.append(f"Agent {agent.id} error: {e}")
                self.memory.record_agent_invocation(agent.id, False)
                
            steps += 1
            
            # Original clarification gating (only if auto_proceed is False)
            if agent.id == 'clarify' and not auto_proceed:
                clar = self.state.get('clarify', {})
                if clar.get('questions'):
                    if self.verbose:
                        print("\n⏸️  Halting for user clarification...")
                    break
                    
            # Allow remediation after evaluation if score low (<65)
            if 'evaluate' in self.state:
                if 'package' in self.state and (self.state.get('evaluate', {}).get('score', 0) >= 65 or 'remediate' in self.state):
                    break
                    
        # Final summary
        total_time = time.time() - start_time
        if self.verbose:
            print("="*80)
            print(f"🏆 Pipeline completed in {total_time:.2f}s with {steps} agent executions")
            self._print_summary()
            
        return self.state

    def _print_summary(self):
        """Print a summary of what was accomplished"""
        files = self.state.get('codegen', {}).get('files', [])
        score = self.state.get('evaluate', {}).get('score', 0)
        
        print(f"\n📊 Final Results:")
        print(f"   📁 Files generated: {len(files)}")
        print(f"   🎯 Quality score: {score}/100")
        print(f"   🔧 Tech stack: {', '.join(s.get('name', str(s)) if isinstance(s, dict) else str(s) for s in self.state.get('tech', {}).get('stack', []))}")
        print(f"   🏗️  Architecture: {self.state.get('architecture', {}).get('pattern', 'N/A')}")
        
        if files:
            print(f"   📄 Key files: {', '.join(files[:5])}")

    def generate(self, prompt: str, answers: Optional[Dict[str, Any]] = None, auto_proceed: bool = True) -> Dict[str, Any]:
        """Main entry point for project generation with detailed logging"""
        self.log.clear()
        self.detailed_log.clear()
        
        result = self._run_pipeline(prompt, answers=answers, auto_proceed=auto_proceed)
        return result

    def get_execution_report(self) -> Dict[str, Any]:
        """Get a detailed report of the execution"""
        return {
            'timeline': self.detailed_log,
            'agents_used': [entry['agent_id'] for entry in self.detailed_log if entry['event'] == 'agent_start'],
            'total_duration': self.detailed_log[-1]['timestamp'] - self.detailed_log[0]['timestamp'] if self.detailed_log else 0,
            'success_rate': len([e for e in self.detailed_log if e['event'] == 'agent_success']) / len([e for e in self.detailed_log if e['event'] in ['agent_success', 'agent_error']]) if self.detailed_log else 0,
            'final_state_keys': list(self.state.keys())
        }

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m orchestrator_v2.logged_orchestrator 'project description'")
        sys.exit(1)
        
    prompt = ' '.join(sys.argv[1:])
    project_root = Path.cwd() / "generated" / f"logged-{prompt.replace(' ', '-')[:20]}"
    project_root.mkdir(parents=True, exist_ok=True)
    
    orchestrator = LoggedDynamicOrchestrator(project_root, verbose=True)
    
    print(f"🚀 Generating project with detailed logging: {prompt}")
    print(f"📂 Output directory: {project_root}")
    
    result = orchestrator.generate(prompt, auto_proceed=True)
    
    # Save detailed report
    report = orchestrator.get_execution_report()
    report_file = project_root / "EXECUTION_REPORT.json"
    report_file.write_text(json.dumps(report, indent=2))
    
    print(f"\n📋 Execution report saved to: {report_file}")

if __name__ == '__main__':
    main()
