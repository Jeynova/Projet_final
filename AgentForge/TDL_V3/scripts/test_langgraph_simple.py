#!/usr/bin/env python3
"""
Test du pipeline LangGraph avec corrections
"""

import sys
from pathlib import Path
import tempfile

# Add project to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

def test_langgraph_simplified():
    """Test LangGraph avec un pipeline simplifié"""
    print("🔀 Test LangGraph Simplifié")
    print("=" * 50)
    
    try:
        from langgraph.graph import StateGraph, END
        from typing import TypedDict, List, Dict, Any
        from orchestrator.agents import spec_extractor, planner, scaffolder, codegen, eval_agent
        
        # StateGraph simplifié pour éviter les conflits
        class SimpleState(TypedDict, total=False):
            prompt: str
            name: str
            spec: Dict[str, Any]
            preset: str
            artifacts_dir: str
            project_dir: str
            logs: List[str]
            eval: Dict[str, Any]
        
        # Créer un graphe minimal
        graph = StateGraph(SimpleState)
        
        # Ajouter seulement les agents essentiels
        graph.add_node("spec_extractor", spec_extractor)
        graph.add_node("planner", planner)  
        graph.add_node("scaffolder", scaffolder)
        graph.add_node("codegen", codegen)
        graph.add_node("eval_agent", eval_agent)
        
        # Connections séquentielles simples
        graph.set_entry_point("spec_extractor")
        graph.add_edge("spec_extractor", "planner")
        graph.add_edge("planner", "scaffolder")
        graph.add_edge("scaffolder", "codegen")
        graph.add_edge("codegen", "eval_agent")
        graph.add_edge("eval_agent", END)
        
        app = graph.compile()
        
        # Test avec état minimal
        with tempfile.TemporaryDirectory() as tmp_dir:
            state = {
                "prompt": "API simple avec users(email unique, password_hash) et products(name, price float)",
                "name": "simple-api",
                "artifacts_dir": tmp_dir,
                "logs": []
            }
            
            print("🚀 Lancement LangGraph...")
            result = app.invoke(state)
            
            # Vérifications
            print(f"✅ Entités parsées: {len(result.get('spec', {}).get('entities', []))}")
            print(f"✅ Projet créé: {Path(result.get('project_dir', '')).exists()}")
            print(f"✅ Score final: {result.get('eval', {}).get('score', 0)}")
            print(f"✅ Logs: {len(result.get('logs', []))}")
            
            score = result.get('eval', {}).get('score', 0)
            if score >= 0.8:
                print("\n🎉 LangGraph Pipeline 100% réussi !")
                return True
            else:
                print(f"\n⚠️ LangGraph Pipeline partiellement réussi (score: {score})")
                return False
                
    except Exception as e:
        print(f"❌ Erreur LangGraph: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_langgraph_simplified()
    if success:
        print("\n🏆 MISSION ACCOMPLIE - Pipeline 100% opérationnel !")
    else:
        print("\n❌ Échec du test LangGraph")
    sys.exit(0 if success else 1)
