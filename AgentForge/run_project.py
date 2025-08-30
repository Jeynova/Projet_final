"""Simple entrypoint script for users.
Default: dynamic orchestrator (legacy enhanced system).

Env switches (preferred for new agentic pipeline):
  AGENTFORGE_AGENTIC=1          -> use new smol pipeline (deterministic + selective agents)
  AGENTFORGE_MODE=templates|auto|agent_first
    templates    : only scaffold + manifest + package
    auto (default): scaffold + selective enrichment
    agent_first  : full staged pipeline (questions, tech validate, infra, etc.)

CLI flags (still supported):
  --smol : use older experimental smol system
  --boilerplate : (legacy) only scaffold path inside dynamic orchestrator

Usage (PowerShell):
  python run_project.py "Blog platform with FastAPI and SQLite" -n blog_app
Outputs go to ./generated/<name>/
"""
from pathlib import Path
import argparse, json, os, re
from orchestrator_v2.dynamic_orchestrator import DynamicOrchestrator
from orchestrator_v2.smol_smart_system import run_smol_system

AGENTIC_FLAG = os.getenv('AGENTFORGE_AGENTIC','0') == '1'
AGENTIC_MODE = os.getenv('AGENTFORGE_MODE','auto')

def main():
  ap = argparse.ArgumentParser(description='AgentForge Project Generator (minimal CLI)')
  # Positional prompt OR --prompt; either works. If neither given, enter interactive mode.
  ap.add_argument('prompt_positional', nargs='?', help='Project description (positional)')
  ap.add_argument('--prompt','-p', help='Project description prompt (alternative to positional)')
  ap.add_argument('--name','-n', default='project', help='Project short name')
  ap.add_argument('--out','-o', default='generated', help='Output base directory')
  ap.add_argument('--boilerplate', action='store_true', help='Only deterministic scaffold + infra + quickstart')
  ap.add_argument('--smol', action='store_true', help='Use experimental smol agent pipeline')
  args = ap.parse_args()
  prompt = args.prompt or args.prompt_positional
  if not prompt:
    try:
      prompt = input("Enter project prompt: ").strip()
    except KeyboardInterrupt:
      print("Aborted."); return
  if not prompt:
    print("No prompt provided."); return
  # Auto-generate name if user kept default 'project'
  name = args.name
  if name == 'project':
    slug = re.sub(r'[^a-z0-9]+','-', prompt.lower()).strip('-')
    if not slug:
      slug = 'project'
    if len(slug) > 18:
      slug = slug[:18]
    name = slug
  root = Path(args.out) / name
  root.mkdir(parents=True, exist_ok=True)
  if AGENTIC_FLAG:
    # New smol-agent style pipeline (deterministic core + light agent staging)
    try:
      from orchestrator_v2.agentic_smol_pipeline import run_agentic_pipeline
      result = run_agentic_pipeline(prompt=prompt, name=name, project_root=root)
      print(f"[agentic:{AGENTIC_MODE}] new pipeline used")
    except Exception as e:
      print("[agentic] Failed (", e, ") falling back to legacy dynamic orchestrator")
      orch = DynamicOrchestrator(root)
      result = orch.run(prompt, name, boilerplate_only=args.boilerplate)
  elif args.smol:
    result = run_smol_system(prompt=prompt, name=name, project_root=root)
  else:
    orch = DynamicOrchestrator(root)
    result = orch.run(prompt, name, boilerplate_only=args.boilerplate)
  report = root / 'RUN_RESULT.json'
  report.write_text(json.dumps(result, indent=2))
  print(f"\n✨ Generation complete. Output: {root}")
  if result.get('agents_used'):
    print("Agents:", ', '.join(result['agents_used']))
  print("Next: cd", root, "and start coding.")

if __name__ == '__main__':
    main()
