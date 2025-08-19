from typing import Dict, Any, List
from pathlib import Path
import re
from .project_spec import ProjectSpec, EntitySpec, FieldSpec
from .utils import render_dir, run_cmd, ensure_dir, write_json
from colorama import Fore, Style
from .llm_client import LLMClient

# --- Entity Parser Function ---
def _parse_entities_from_text(text: str) -> List[EntitySpec]:
    """Parse entities from text patterns like 'users(email unique, password_hash)'"""
    entities = []
    # pattern "users(...)" ou "products(...)"
    for match in re.finditer(r"(\w+)\s*\(([^)]*)\)", text):
        ename = match.group(1)
        raw_fields = [f.strip() for f in match.group(2).split(",") if f.strip()]
        fields = []
        for rf in raw_fields:
            # ex: "email unique" / "price:float" / "id:int pk"
            name_type = rf.split(":")
            name = name_type[0].split()[0]
            typ = (name_type[1] if len(name_type) > 1 else "str").strip().lower()
            pk = " pk" in rf or name.lower() in ("id", f"{ename}_id")
            unique = " unique" in rf
            nullable = not unique and not pk
            fields.append(FieldSpec(
                name=name, 
                type=typ if typ in ["int","str","float","bool","datetime"] else "str", 
                pk=pk, 
                unique=unique, 
                nullable=nullable
            ))
        
        # id par défaut si absent
        if not any(f.pk for f in fields):
            fields.insert(0, FieldSpec(name="id", type="int", pk=True, unique=True, nullable=False))
        
        entities.append(EntitySpec(name=ename.capitalize(), fields=fields))
    
    # Default entities for common patterns
    text_lower = text.lower()
    if "crud:users" in text_lower or "users" in text_lower:
        if not any(e.name.lower() == "user" for e in entities):
            entities.append(EntitySpec(
                name="User",
                fields=[
                    FieldSpec(name="id", type="int", pk=True, unique=True, nullable=False),
                    FieldSpec(name="email", type="str", unique=True, nullable=False),
                    FieldSpec(name="hashed_password", type="str", nullable=False),
                    FieldSpec(name="created_at", type="datetime", nullable=False)
                ]
            ))
    
    if "crud:vehicles" in text_lower or "flotte" in text_lower or "fleet" in text_lower:
        if not any(e.name.lower() == "vehicle" for e in entities):
            entities.append(EntitySpec(
                name="Vehicle",
                fields=[
                    FieldSpec(name="id", type="int", pk=True, unique=True, nullable=False),
                    FieldSpec(name="license_plate", type="str", unique=True, nullable=False),
                    FieldSpec(name="make", type="str", nullable=False),
                    FieldSpec(name="model", type="str", nullable=False),
                    FieldSpec(name="year", type="int", nullable=True),
                    FieldSpec(name="owner_id", type="int", nullable=True),
                    FieldSpec(name="created_at", type="datetime", nullable=False)
                ]
            ))
    
    return entities

# --- Agent 0: Spec Extractor (with LLM support and heuristic fallback) ---

# --- Agent 1: Planner ---
def planner(state: Dict[str, Any]) -> Dict[str, Any]:
    spec = ProjectSpec(**state["spec"])
    # Sélection du preset
    if spec.language == "python" and spec.project_type == "api" and spec.db == "postgres":
        preset = "api_fastapi_postgres" if spec.web == "fastapi" else "api_flask_postgres"
    elif spec.language == "python" and spec.project_type == "api" and spec.db == "sqlite":
        preset = "api_flask_sqlite" if spec.web == "flask" else "api_fastapi_sqlite"
    else:
        preset = "api_fastapi_postgres"
    state["preset"] = preset
    state["logs"].append(f"Planner: preset choisi = {preset}.")
    return state

# --- Agent 2: Scaffolder ---
def scaffolder(state: Dict[str, Any]) -> Dict[str, Any]:
    spec = ProjectSpec(**state["spec"])
    preset = state["preset"]
    out_dir = Path(state["artifacts_dir"]) / spec.name
    template_dir = Path(__file__).resolve().parents[1] / "templates" / preset
    # Pydantic v2 compatibility
    context = spec.model_dump() if hasattr(spec, 'model_dump') else spec.dict()
    context["project_name"] = spec.name
    render_dir(template_dir, out_dir, context)
    state["project_dir"] = str(out_dir)
    state["logs"].append(f"Scaffolder: fichiers générés dans {out_dir}.")
    return state

# --- Agent 3: Security/QA (placeholders) ---
def security_qa(state: Dict[str, Any]) -> Dict[str, Any]:
    proj = Path(state["project_dir"])
    # Ajout simple: ruff + bandit + pip-audit déjà listés dans requirements du projet
    state["logs"].append("Security/QA: configuration de base ajoutée (ruff/bandit/pip-audit).")
    return state

# --- Agent 4: Tester (génère tests basiques et lance pytest en container) ---
def tester(state: Dict[str, Any]) -> Dict[str, Any]:
    proj = Path(state["project_dir"])
    # Exécute tests via docker compose si possible
    try:
        code = run_cmd(["docker", "compose", "build"], cwd=proj)
        state["logs"].append(f"Tester: build docker compose status={code}.")
        try:
            code2 = run_cmd(["docker", "compose", "run", "--rm", "api", "pytest", "-q"], cwd=proj)
            state["logs"].append(f"Tester: pytest status={code2}.")
            state["tests_ok"] = (code == 0 and code2 == 0)
        except Exception as e:
            state["logs"].append(f"Tester: pytest failed - {str(e)}")
            state["tests_ok"] = False
    except Exception as e:
        state["logs"].append(f"Tester: docker not available - {str(e)}")
        state["tests_ok"] = False
    return state

# --- Agent 5: Dockerizer (déjà via templates, mais ajoute healthchecks) ---
def dockerizer(state: Dict[str, Any]) -> Dict[str, Any]:
    state["logs"].append("Dockerizer: Dockerfile & compose générés (avec healthcheck).")
    return state

# --- Agent 6: CI Agent ---
def ci_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    state["logs"].append("CI Agent: workflow GitHub Actions ajouté.")
    return state

# --- Agent 7: Verifier (lecture logs simple) ---
def verifier(state: Dict[str, Any]) -> Dict[str, Any]:
    ok = state.get("tests_ok", False)
    if ok:
        state["status"] = "success"
        state["logs"].append(Fore.GREEN + "Verifier: génération OK ✅" + Style.RESET_ALL)
    else:
        state["status"] = "needs_fix"
        state["logs"].append(Fore.YELLOW + "Verifier: des corrections peuvent être nécessaires ⚠️" + Style.RESET_ALL)
    return state

SYSTEM_PROMPT = (
    "Tu es un extracteur qui convertit une demande en spec de projet. "
    "Renvoie strictement un JSON avec ces champs: "
    "name, project_type, language, web, db, auth, features, tests, ci, security, dockerize, infra."
)

# --- Agent 0: Spec Extractor (with LLM support and heuristic fallback) ---
def spec_extractor(state):
    prompt = state["prompt"].lower()
    name = state.get("name") or "generated-app"

    # 1) Tentative LLM si configuré
    llm = LLMClient()
    llm_json = llm.extract_json(SYSTEM_PROMPT, state["prompt"])
    if isinstance(llm_json, dict):
        try:
            spec = ProjectSpec(**{
                "name": llm_json.get("name", name),
                "project_type": llm_json.get("project_type", "api"),
                "language": llm_json.get("language", "python"),
                "web": llm_json.get("web", "fastapi"),
                "db": llm_json.get("db", "postgres"),
                "auth": llm_json.get("auth", "jwt"),
                "features": llm_json.get("features", []),
                "tests": llm_json.get("tests", "basic"),
                "ci": llm_json.get("ci", "github_actions"),
                "security": llm_json.get("security", "baseline"),
                "dockerize": llm_json.get("dockerize", True),
                "infra": llm_json.get("infra", "docker_compose"),
            })
            # Pydantic v2 compatibility
            state["spec"] = spec.model_dump() if hasattr(spec, 'model_dump') else spec.dict()
            state["logs"].append("Spec Extractor: spec dérivée via LLM.")
            return state
        except Exception:
            pass

    # 2) Fallback heuristique (comme avant)
    entities = _parse_entities_from_text(state["prompt"])
    
    spec = ProjectSpec(
        name=name,
        project_type="api",
        language="python",
        web="fastapi" if "flask" not in prompt else "flask",
        db=("postgres" if "postgres" in prompt or "pg" in prompt else ("sqlite" if "sqlite" in prompt else "postgres")),
        auth=("jwt" if "jwt" in prompt else "none" if "sans auth" in prompt or "no auth" in prompt else "jwt"),
        tests="crud" if "crud" in prompt else "basic",
        ci="github_actions",
        security="baseline",
        dockerize=True,
        infra="docker_compose",
        features=["healthcheck","rate_limit"] + (["crud:vehicles"] if "flotte" in prompt or "fleet" in prompt else []),
        entities=entities  # <-- NEW
    )
    # Pydantic v2 compatibility
    state["spec"] = spec.model_dump() if hasattr(spec, 'model_dump') else spec.dict()
    state["logs"].append(f"Spec Extractor: spec dérivée du prompt (heuristique). Entités détectées: {len(entities)}")
    return state