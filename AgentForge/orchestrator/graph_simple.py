import argparse, json
from typing import TypedDict, List, Dict, Any, Annotated
from pathlib import Path
from langgraph.graph import StateGraph, END
from operator import add
from .agents_simple import spec_extractor, planner, scaffolder, codegen, eval_agent
from .utils import ensure_dir, write_json

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
    tech_selection: Dict[str, Any]
    eval: Dict[str, Any]

def build_app():
    graph = StateGraph(BuildState)
    
    # Noeuds principaux seulement
    graph.add_node("spec_extractor", spec_extractor)
    graph.add_node("planner", planner)
    graph.add_node("scaffolder", scaffolder)
    graph.add_node("codegen", codegen)
    graph.add_node("eval_agent", eval_agent)
    
    # Flow simple et linéaire
    graph.set_entry_point("spec_extractor")
    graph.add_edge("spec_extractor", "planner")
    graph.add_edge("planner", "scaffolder")
    graph.add_edge("scaffolder", "codegen")
    graph.add_edge("codegen", "eval_agent")
    graph.add_edge("eval_agent", END)

    return graph.compile()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--name", default="generated-app")
    parser.add_argument("--artifacts-dir", default="./generated")
    
    args = parser.parse_args()
    
    artifacts_dir = Path(args.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    app = build_app()
    
    state = {
        "prompt": args.prompt,
        "name": args.name,
        "artifacts_dir": str(artifacts_dir),
        "logs": []
    }
    
    final = app.invoke(state)
    
    print("🎉 Generation completed!")
    print(f"Status: {final.get('status', 'unknown')}")
    print(f"Project: {final.get('project_dir', 'unknown')}")
    
    if final.get("logs"):
        print("\nLogs:")
        for log in final["logs"]:
            print(f"  {log}")

if __name__ == "__main__":
    main()
