import argparse, json, os
from typing import TypedDict, List, Dict, Any, Annotated
from pathlib import Path
from langgraph.graph import StateGraph, END
from operator import add
from .agents import spec_extractor, planner, scaffolder, security_qa, tester, dockerizer, ci_agent, verifier
from .agents import retrieve_recipes, codegen  # NEW
from .utils import ensure_dir, write_json

# Feature flag
AGENTIC = os.getenv("AGENTFORGE_AGENTIC", "0") == "1"

if AGENTIC:
    try:
        from .tech_selector_smol import run_tech_selector_smol
    except ImportError:
        AGENTIC = False  # Fallback si smolagents pas disponible

class BuildState(TypedDict, total=False):
    prompt: str  # Single value, no updates expected
    name: str
    spec: Dict[str, Any]
    preset: str
    artifacts_dir: str
    project_dir: str
    logs: Annotated[List[str], add]  # Can accumulate multiple values
    status: str
    tests_ok: bool
    tech_selection: Dict[str, Any]  # NEW - pour tech_selector
    eval: Dict[str, Any]  # NEW - pour eval_agent

def build_app():
    graph = StateGraph(BuildState)
    
    # Noeuds principaux
    graph.add_node("spec_extractor", spec_extractor)
    
    # Injection conditionnelle du TechSelector
    if AGENTIC:
        graph.add_node("tech_selector", run_tech_selector_smol)
        graph.add_node("planner", planner)
        graph.set_entry_point("spec_extractor")
        graph.add_edge("spec_extractor", "tech_selector")
        graph.add_edge("tech_selector", "planner")
    else:
        graph.add_node("planner", planner)
        graph.set_entry_point("spec_extractor")
        graph.add_edge("spec_extractor", "planner")
    
    graph.add_node("scaffolder", scaffolder)
    graph.add_node("codegen", codegen)
    
    # Flow après planner identique
    graph.add_edge("planner", "scaffolder")
    graph.add_edge("scaffolder", "codegen")
    graph.add_edge("codegen", END)

    return graph.compile()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, help="Description naturelle du projet")
    parser.add_argument("--name", default="generated-app")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "generated"))
    args = parser.parse_args()

    app = build_app()
    state: BuildState = {
        "prompt": args.prompt,
        "name": args.name,
        "artifacts_dir": args.out,
        "logs": [],
    }
    ensure_dir(Path(args.out))
    final = app.invoke(state)
    out_dir = Path(final["project_dir"])
    logs_path = Path(args.out) / f"{args.name}_logs.json"
    write_json(logs_path, {"logs": final["logs"], "status": final.get("status")})
    print("\n=== Résultat ===")
    print("Projet :", out_dir)
    print("Statut :", final.get("status"))
    print("Logs   :", logs_path)

if __name__ == "__main__":
    main()
