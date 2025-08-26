from pathlib import Path
import json, os, re
from typing import Dict, Any

ALLOWED = {
    "web": {"fastapi","flask"},
    "db": {"postgres","sqlite"},
    "infra": {"docker_compose","k8s"},
    "ci": {"github_actions","none"},
}

ALIASES = {
    "web": {
        "django":"fastapi", "starlette":"fastapi", "quart":"flask",
        "tornado":"fastapi",  # (souvent plus proche d'ASGI)
    },
    "db": {
        "postgresql":"postgres", "psql":"postgres", "mysql":"postgres",
        "mongodb":"sqlite", "mongo":"sqlite", "redis":"sqlite",
        "clickhouse":"postgres",
    },
    "infra": {
        "kubernetes":"k8s", "k8s":"k8s", "docker swarm":"docker_compose",
        "swarm":"docker_compose", "bare metal":"docker_compose",
        "bare_metal":"docker_compose", "nomad":"k8s",
        "docker-compose":"docker_compose", "docker compose":"docker_compose",
    },
    "ci": {
        "github actions":"github_actions", "gitlab":"github_actions",
        "gitlab ci":"github_actions", "jenkins":"github_actions",
        "circleci":"github_actions", "azure pipelines":"github_actions",
        "azure_pipelines":"github_actions",
    },
}

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("-", " ").replace("/", " ")
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" ", "_")
    return s

def _map_choice(cat: str, val: str) -> str:
    v = _norm(val)
    v = ALIASES.get(cat, {}).get(v, v)
    if v in ALLOWED[cat]:
        return v
    # Fallbacks stables par défaut
    fallbacks = {"web": "fastapi", "db": "postgres", "infra": "docker_compose", "ci": "github_actions"}
    return fallbacks.get(cat, "fastapi")

def _parse_json_strict(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise
        return json.loads(m.group(0))

INSTR = """
Tu es un architecte logiciel expert. Recommande une stack technique moderne pour un projet Python.

Réponds UNIQUEMENT en JSON: {"web": "...", "db": "...", "infra": "...", "ci": "...", "reasons": [...], "confidence": 0.xx}

Choisis librement parmi TOUTES les technologies Python modernes :
- Web: FastAPI, Flask, Django, Starlette, Tornado, Quart, etc.
- DB: PostgreSQL, MySQL, SQLite, MongoDB, Redis, ClickHouse, etc.
- Infra: Docker Compose, Kubernetes, Docker Swarm, Bare Metal, etc.  
- CI: GitHub Actions, GitLab CI, Jenkins, CircleCI, Azure Pipelines, etc.

Justifie tes choix dans "reasons" selon :
- Complexité du projet (simple/complexe)
- Charge attendue (faible/forte) 
- Priorités (dev rapide/performance/scalabilité)
- Contraintes techniques mentionnées

Si l'utilisateur impose explicitement une technologie, RESPECTE-LA.
"""

def _model_from_env():
    """Créer le modèle LLM selon l'env, avec fallback pour mode mock"""
    provider = os.getenv("AGENTFORGE_LLM", "mock")
    
    # Import conditionnel pour éviter les erreurs si pas installé
    try:
        from smolagents import LiteLLMModel
    except ImportError:
        return None  # Fallback si smolagents pas installé
    
    # Mode test pour démonstration
    if provider == "test":
        return "TEST_MODE"  # Signal pour utiliser des réponses simulées
    
    if provider == "ollama":
        return LiteLLMModel(
            model_id=f"ollama/{os.getenv('OLLAMA_MODEL', 'llama3.1')}",
            api_base=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        )
    elif provider == "openai":
        # Vérifier qu'on a une vraie clé API
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key.startswith("sk-test"):
            return "TEST_MODE"  # Mode simulé si pas de vraie clé
        return LiteLLMModel(model_id=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    
    # Mode mock ou autre : mode test
    return "TEST_MODE"

def _validate_and_map_selection(sel: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """Validation et mapping robuste des choix LLM vers templates supportés"""
    raw = {k: str(sel.get(k,"")) for k in ("web","db","infra","ci")}
    mapped = {
        "web": _map_choice("web", raw["web"]),
        "db": _map_choice("db", raw["db"]),
        "infra": _map_choice("infra", raw["infra"]),
        "ci": _map_choice("ci", raw["ci"]),
        "reasons": sel.get("reasons", []) or [],
        "confidence": float(sel.get("confidence", 0.6)),
    }
    
    # log des changements
    changes = []
    for k in ("web","db","infra","ci"):
        if _norm(raw[k]) != mapped[k]:
            changes.append(f"{k}: {raw[k]} → {mapped[k]}")
    if changes:
        state["logs"].append("TechSelector mappings: " + ", ".join(changes))
        mapped["reasons"] = list(mapped["reasons"]) + [f"Mapped to supported templates: {', '.join(changes)}"]

    # garde pour l'UI & audit
    state["tech_selection_raw"] = raw
    # clamp confidence
    if mapped["confidence"] < 0: mapped["confidence"] = 0.0
    if mapped["confidence"] > 1: mapped["confidence"] = 1.0
    return mapped

def _simulate_llm_selection(state: Dict[str, Any]) -> Dict[str, Any]:
    """Simulation intelligente des choix LLM pour démo/test"""
    prompt = state.get("prompt", "").lower()
    
    # Analyse contextuelle intelligente avec priorités
    if any(word in prompt for word in ["e-commerce", "scalabilité", "100k", "concurrent"]):
        # Projet complexe/haute performance - mots clés spécifiques
        sel = {
            "web": "django",  # Plus robuste pour complexe
            "db": "postgresql", 
            "infra": "kubernetes",  # Scalabilité 
            "ci": "gitlab_ci",
            "reasons": [
                "Projet complexe détecté: e-commerce haute performance",
                "Django choisi pour robustesse et admin intégré", 
                "PostgreSQL pour ACID et performances",
                "Kubernetes pour scalabilité horizontale",
                "GitLab CI pour pipeline DevOps avancé"
            ],
            "confidence": 0.85
        }
    elif any(word in prompt for word in ["prototype", "simple", "rapide", "démonstration", "2 développeurs"]):
        # Prototype/MVP simple - priorité haute
        sel = {
            "web": "flask",
            "db": "sqlite", 
            "infra": "docker_compose",
            "ci": "github_actions",
            "reasons": [
                "Prototype simple détecté",
                "Flask choisi pour simplicité et rapidité",
                "SQLite pour démarrage sans config",
                "Docker Compose pour développement facile",
                "GitHub Actions pour CI/CD simple"
            ],
            "confidence": 0.90
        }
    elif any(word in prompt for word in ["api", "microservice", "rest", "async", "jwt"]):
        # API/Microservices
        sel = {
            "web": "fastapi",
            "db": "postgres",
            "infra": "k8s", 
            "ci": "github_actions",
            "reasons": [
                "API/microservices détecté",
                "FastAPI choisi pour performance async",
                "PostgreSQL pour robustesse",
                "Kubernetes pour orchestration microservices",
                "GitHub Actions pour déploiement continu"
            ],
            "confidence": 0.80
        }
    elif any(word in prompt for word in ["haute performance", "monitoring", "analytics"]):
        # Performance avancée (mais pas e-commerce)
        sel = {
            "web": "fastapi",
            "db": "postgres",
            "infra": "k8s",
            "ci": "github_actions",
            "reasons": [
                "Haute performance requise",
                "FastAPI pour performance async",
                "PostgreSQL pour robustesse", 
                "Kubernetes pour scalabilité",
                "CI/CD pour déploiement fréquent"
            ],
            "confidence": 0.85
        }
    else:
        # Cas général équilibré
        sel = {
            "web": "fastapi",
            "db": "postgres",
            "infra": "docker_compose",
            "ci": "github_actions", 
            "reasons": [
                "Configuration équilibrée par défaut",
                "FastAPI pour performances et documentation auto",
                "PostgreSQL pour robustesse",
                "Docker Compose pour simplicité",
                "GitHub Actions pour intégration"
            ],
            "confidence": 0.75
        }
    
    # Application du mapping
    sel = _validate_and_map_selection(sel, state)
    
    # Merge sans écraser choix utilisateur
    spec = dict(state["spec"])
    for k in ("web", "db", "infra", "ci"):
        if spec.get(k) in (None, "", "auto"):
            spec[k] = sel.get(k, spec.get(k))
    
    state["spec"] = spec
    state["tech_selection"] = sel
    state["logs"].append(f"TechSelector(simulated): {sel.get('web')}/{sel.get('db')}/{sel.get('infra')}/{sel.get('ci')}")
    return state

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
        
        # Mode simulation pour tests/démo
        if model == "TEST_MODE":
            return _simulate_llm_selection(state)
        
        agent = CodeAgent(
            tools=tools, 
            model=model, 
            max_steps=3,
            name="TechSelectorAgent",
            additional_authorized_imports=['json']
        )

        user_prompt = f"""
DESCRIPTION:
{state.get("prompt")}

SPEC INITIALE:
{json.dumps(state['spec'], ensure_ascii=False, indent=2)}

ACTIONS:
1) retrieve_snippets(tags="fastapi,flask,django,starlette,postgres,sqlite,mysql,mongodb,redis,clickhouse,k8s,docker,ci,github,gitlab,jenkins") pour notes
2) Renvoie UNIQUEMENT le JSON demandé
"""
        
        out = agent.run(INSTR + "\n\n" + user_prompt)
        
        # Extraction du JSON de la réponse finale avec parsing robuste
        if hasattr(out, 'content') and out.content:
            json_str = out.content.strip()
        elif isinstance(out, dict):
            sel = out
        else:
            json_str = str(out).strip()
            
        # Parse JSON si on a une string
        if 'sel' not in locals():
            sel = _parse_json_strict(json_str)
        
        # Validation basique du JSON
        required_keys = {"web", "db", "infra", "ci"}
        if not all(k in sel for k in required_keys):
            raise ValueError("Missing required keys in LLM response")
        
        # Mapping vers templates supportés si nécessaire
        sel = _validate_and_map_selection(sel, state)
            
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
