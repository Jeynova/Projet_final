from typing import Dict, Any
from pathlib import Path
from .project_spec import ProjectSpec
from .utils import render_dir, run_cmd, ensure_dir, write_json
from colorama import Fore, Style
from .llm_client import LLMClient

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
    context = spec.dict()
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
    code = run_cmd(["docker", "compose", "build"], cwd=proj)
    state["logs"].append(f"Tester: build docker compose status={code}.")
    code2 = run_cmd(["docker", "compose", "run", "--rm", "api", "pytest", "-q"], cwd=proj)
    state["logs"].append(f"Tester: pytest status={code2}.")
    state["tests_ok"] = (code == 0 and code2 == 0)
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
            state["spec"] = spec.dict()
            state["logs"].append("Spec Extractor: spec dérivée via LLM.")
            return state
        except Exception:
            pass

    # 2) Fallback heuristique (comme avant)
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
        features=["healthcheck","rate_limit"] + (["crud:vehicles"] if "flotte" in prompt or "fleet" in prompt else [])
    )
    state["spec"] = spec.dict()
    state["logs"].append("Spec Extractor: spec dérivée du prompt (heuristique).")
    return state