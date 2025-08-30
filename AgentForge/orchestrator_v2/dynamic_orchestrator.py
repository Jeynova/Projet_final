"""Dynamic Orchestrator v2
Selects which agent to run next based on current state + lightweight learning.
"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from pathlib import Path
from .memory_store import MemoryStore
from .agent_base import AgentResult
from .agents_impl import (
    MemoryAgent, ClarifyAgent, TechSelectAgent, ArchitectureAgent, ArchitectureValidationAgent, ArchitectureExpandAgent, ScaffoldAgent, CodeGenAgent,
    DatabaseAgent, DeploymentSelectAgent, InfraAgent, DockerComposeAgent, KubeAgent,
    TestAgent, IngestAgent, EvaluationAgent, RemediationAgent, PackageAgent, QuickstartAgent, ValidateAgent, ManifestAgent
)
from .rag_store import RAGStore

class DynamicOrchestrator:
    def __init__(self, project_root: Path, memory: MemoryStore | None = None):
        self.memory = memory or MemoryStore()
        self.project_root = project_root
        self.state: Dict[str, Any] = {}
        self.log: List[str] = []
        self.rag = RAGStore()
        self.agents = [
            MemoryAgent(self.memory, self.rag),
            ClarifyAgent(),
            TechSelectAgent(),
            ArchitectureAgent(),
            ArchitectureValidationAgent(),
            ArchitectureExpandAgent(),
            ScaffoldAgent(project_root),
            CodeGenAgent(project_root),
            # Run manifest generation before validation so validate can count it
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

    def _candidate_agents(self) -> List:
        return [a for a in self.agents if a.can_run(self.state)]

    def _score_agent(self, agent) -> float:
        base = self.memory.success_rate(agent.id)
        stage_order = ['memory','clarify','tech_select','architecture','arch_validate','arch_expand','scaffold','codegen','manifest','validate','database','deploy_select','infra','compose','kube','tests','quickstart','ingest','evaluate','remediate','package']
        if agent.id == 'clarify' and 'clarify' not in self.state:
            return base + 2.0
        if agent.id in stage_order:
            pos = stage_order.index(agent.id)
            bonus = (len(stage_order) - pos) / len(stage_order) * 0.2
        else:
            bonus = 0
        return base + bonus

    def run(self, prompt: str, name: str, answers: Dict[str, Any] | None = None, boilerplate_only: bool = False) -> Dict[str, Any]:
        self.state['prompt'] = prompt
        self.state['name'] = name
        if answers:
            self.state['answers'] = answers
        if boilerplate_only:
            self.state.setdefault('config', {})['boilerplate_only'] = True
        steps = 0
        while steps < 30:  # safety cap (slightly higher with more agents)
            candidates = self._candidate_agents()
            if not candidates:
                break
            scored = sorted([(self._score_agent(a), a) for a in candidates], key=lambda x: x[0], reverse=True)
            _, agent = scored[0]
            self.log.append(f"Running agent: {agent.id}")
            try:
                output = agent.run(self.state)
                key = agent.id if agent.id not in ('tech_select',) else 'tech'
                self.state[key] = output
                self.memory.record_agent_invocation(agent.id, True)
                self.memory.record_decision({'keys': list(self.state.keys())}, agent.id, 'success')
            except Exception as e:
                self.log.append(f"Agent {agent.id} error: {e}")
                self.memory.record_agent_invocation(agent.id, False)
                self.memory.record_decision({'keys': list(self.state.keys())}, agent.id, 'fail')
            steps += 1
            # Clarification gating: if clarification produced unanswered questions, stop early
            if agent.id == 'clarify':
                clar = self.state.get('clarify', {})
                if clar.get('questions'):
                    self.log.append('Clarification required. Halting until answers provided.')
                    break
            # Allow remediation after evaluation if score low (<65)
            if 'evaluate' in self.state:
                # Break only after packaging so we always produce artifact
                if 'package' in self.state and (self.state.get('evaluate', {}).get('score', 0) >= 65 or 'remediate' in self.state):
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
        # Generate lightweight run report
        report_path = self.project_root / 'AGENT_RUN_REPORT.md'
        try:
            report_lines = [
                f"# Agent Run Report: {name}",
                '',
                f"Prompt: {prompt}",
                f"Score: {score}",
                f"Agents Used ({len(agents_used)}): " + ', '.join(agents_used),
                '',
                '## Final State Keys',
                ', '.join(sorted(self.state.keys())),
                '',
                '## Log',
            ] + self.log
            report_path.write_text('\n'.join(report_lines))
        except Exception:
            report_path = None
        return {
            'final_state': self.state,
            'log': self.log,
            'score': score,
            'agents_used': agents_used,
            'report_path': str(report_path) if report_path else None
        }

if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser(description='Run dynamic orchestrator v2')
    parser.add_argument('--prompt', required=True)
    parser.add_argument('--name', default='dyn-project')
    parser.add_argument('--output', default='./generated')
    parser.add_argument('--boilerplate-only', action='store_true', help='Generate only deterministic scaffold + infra + quickstart (skip full codegen)')
    args = parser.parse_args()
    root = Path(args.output) / args.name
    root.mkdir(parents=True, exist_ok=True)
    orch = DynamicOrchestrator(root)
    result = orch.run(args.prompt, args.name, boilerplate_only=args.boilerplate_only)
    print(json.dumps(result, indent=2))
