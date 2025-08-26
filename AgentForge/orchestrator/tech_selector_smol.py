from pathlib import Path
import json, os
from typing import Dict, Any

INSTR = """
Tu recommandes une stack web/DB/infra/CI.
Réponds UNIQUEMENT en JSON: {"web": "...", "db": "...", "infra": "...", "ci": "...", "reasons": [...], "confidence": 0.xx}
Contraintes:
- web ∈ {"fastapi","flask"}
- db ∈ {"postgres","sqlite"}
- infra ∈ {"docker_compose","k8s"}
- ci ∈ {"github_actions","none"}
- Respecte tout choix explicitement fourni par l'utilisateur.
"""

def _model_from_env():
    """Créer le modèle LLM selon l'env, avec fallback pour mode mock"""
    provider = os.getenv("AGENTFORGE_LLM", "mock")
    
    # Import conditionnel pour éviter les erreurs si pas installé
    try:
        from smolagents import LiteLLMModel
    except ImportError:
        return None  # Fallback si smolagents pas installé
    
    if provider == "ollama":
        return LiteLLMModel(
            model_id=os.getenv("OLLAMA_MODEL", "ollama_chat/llama3.1:8b"),
            api_base=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        )
    elif provider == "openai":
        return LiteLLMModel(model_id=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    
    # Mode mock ou autre : retourner un modèle par défaut
    return LiteLLMModel(model_id=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

def run_tech_selector_smol(state: Dict[str, Any]) -> Dict[str, Any]:
    """Agent de sélection technique utilisant smolagents"""
    
    # Import conditionnel
    try:
        from smolagents import CodeAgent
        from .orchestrator_root import get_repo_root
        from .tools_smol import RetrieveSnippetsTool
    except ImportError as e:
        # Fallback si smolagents pas disponible
        state["logs"].append(f"TechSelector DISABLED: {e}")
        return _fallback_tech_selection(state)
    
    try:
        repo_root = get_repo_root()
        tools = [RetrieveSnippetsTool(repo_root)]
        model = _model_from_env()
        
        if model is None:
            return _fallback_tech_selection(state)
        
        agent = CodeAgent(
            tools=tools, 
            model=model, 
            max_steps=3,
            name="TechSelectorAgent", 
            try_local_execution=False
        )

        user_prompt = f"""
DESCRIPTION:
{state.get("prompt")}

SPEC INITIALE:
{json.dumps(state['spec'], ensure_ascii=False, indent=2)}

ACTIONS:
1) retrieve_snippets(tags="fastapi,flask,postgres,sqlite,k8s,docker,ci,github") pour notes
2) Renvoie UNIQUEMENT le JSON demandé
"""
        
        out = agent.run(INSTR + "\n\n" + user_prompt).strip()
        sel = json.loads(out)
        
        # Validation basique du JSON
        required_keys = {"web", "db", "infra", "ci"}
        if not all(k in sel for k in required_keys):
            raise ValueError("Missing required keys in LLM response")
            
    except Exception as e:
        state["logs"].append(f"TechSelector ERROR: {e}")
        return _fallback_tech_selection(state)

    # Merge sans écraser un choix utilisateur explicite
    spec = dict(state["spec"])
    for k in ("web", "db", "infra", "ci"):
        if spec.get(k) in (None, "", "auto"):
            spec[k] = sel.get(k, spec.get(k))
    
    state["spec"] = spec
    state["tech_selection"] = sel
    state["logs"].append(f"TechSelector(smol): {sel}")
    return state

def _fallback_tech_selection(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback si smolagents indisponible"""
    spec = state["spec"]
    sel = {
        "web": spec.get("web", "fastapi"),
        "db": spec.get("db", "postgres"), 
        "infra": spec.get("infra", "docker_compose"),
        "ci": spec.get("ci", "github_actions"),
        "reasons": ["fallback - smolagents unavailable"], 
        "confidence": 0.6
    }
    
    # Merge
    for k in ("web", "db", "infra", "ci"):
        if spec.get(k) in (None, "", "auto"):
            spec[k] = sel.get(k, spec.get(k))
    
    state["spec"] = spec
    state["tech_selection"] = sel
    state["logs"].append(f"TechSelector(fallback): {sel}")
    return state
