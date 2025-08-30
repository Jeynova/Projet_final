import argparse
from pathlib import Path
import json
import os

# Import legacy and v2 orchestrators
from orchestrator.truly_smart_system import TrulySmartAgentSystem
from orchestrator_v2.dynamic_orchestrator import DynamicOrchestrator


def run_legacy(prompt: str, name: str, output: str):
    system = TrulySmartAgentSystem()
    return system.build_project(prompt, name, output)


def run_v2(prompt: str, name: str, output: str, answers=None):
    root = Path(output) / name
    root.mkdir(parents=True, exist_ok=True)
    orch = DynamicOrchestrator(root)
    return orch.run(prompt, name, answers=answers)


def main():
    parser = argparse.ArgumentParser(description='AgentForge Orchestrator Selector CLI')
    parser.add_argument('--prompt', required=True, help='Project prompt')
    parser.add_argument('--name', required=True, help='Project name')
    parser.add_argument('--output', default='./generated', help='Output directory')
    parser.add_argument('--mode', choices=['legacy','v2','auto'], default='auto', help='Which orchestrator to use')
    parser.add_argument('--json', action='store_true', help='Print raw JSON result')
    parser.add_argument('--answers', help='Clarification answers key=value pairs (comma separated) e.g. domain=blog,auth=yes,persistence=postgres')
    parser.add_argument('--apply-remediation', action='store_true', help='Append remediation notes into project README (v2 only)')
    args = parser.parse_args()

    # Auto mode: if AGENTFORGE_AGENTIC=1 or AGENTFORGE_MODE=auto -> prefer v2
    chosen = args.mode
    if args.mode == 'auto':
        if os.getenv('AGENTFORGE_AGENTIC','0') == '1' or os.getenv('AGENTFORGE_MODE','') == 'auto':
            chosen = 'v2'
        else:
            chosen = 'legacy'

    answers_dict = {}
    if args.answers:
        for pair in args.answers.split(','):
            if '=' in pair:
                k,v = pair.split('=',1)
                answers_dict[k.strip()] = v.strip()

    if chosen == 'legacy':
        result = run_legacy(args.prompt, args.name, args.output)
    else:
        result = run_v2(args.prompt, args.name, args.output, answers=answers_dict or None)
        # Optional remediation application
        if args.apply_remediation:
            proj_root = Path(args.output) / args.name
            notes = proj_root / 'REMEDIATION_NOTES.md'
            readme = proj_root / 'README.md'
            if notes.exists():
                try:
                    existing = readme.read_text() if readme.exists() else f"# {args.name}\n\n"
                    merged = existing + "\n\n---\n\n" + notes.read_text()
                    readme.write_text(merged)
                    result['remediation_applied'] = True
                except Exception:
                    result['remediation_applied'] = False

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Orchestrator: {chosen}\nName: {args.name}\nScore: {result.get('score') or result.get('final_result',{}).get('project_score')}\nFiles/State Keys: {len(result.get('final_state',{}).keys()) if 'final_state' in result else result.get('files_created')}\n")
        if 'final_state' in result:
            clarify = result['final_state'].get('clarify')
            if clarify and clarify.get('questions'):
                print('Clarification questions:')
                for q in clarify['questions']:
                    print(f'- {q}')

if __name__ == '__main__':
    main()
