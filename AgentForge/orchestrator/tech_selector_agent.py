import json
from typing import Dict, Any
from pathlib import Path
from .project_spec import ProjectSpec
from .llm_client import LLMClient

SYSTEM = (
  "Tu es un conseiller technique. À partir d'une description de projet, "
  "tu recommandes web framework, base de données, et infra (docker_compose vs k8s). "
  "Réponds STRICTEMENT en JSON avec: {web, db, infra, ci, reasons:[], confidence:float}."
)

# RAG simple: on lit quelques fichiers et on les colle en contexte
def _load_snippets(repo_root: Path) -> str:
    acc = []
    for p in (repo_root / "rag_snippets").glob("*.md"):
        acc.append(f"\n--- {p.name} ---\n{p.read_text(encoding='utf-8')}\n")
        if len(acc) >= 6:
            break
    return "\n".join(acc)

def run_tech_selector(state: Dict[str, Any]) -> Dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    spec = ProjectSpec(**state["spec"])
    prompt = f"""
Description utilisateur:
{state.get("prompt")}

Spec initiale:
{json.dumps(spec.dict(), indent=2, ensure_ascii=False)}

Notes (snippets):
{_load_snippets(repo_root)}

Contraintes:
- Web: fastapi|flask|express
- DB: postgres|sqlite|mysql|none
- Infra: docker_compose|k8s
- CI: github_actions|none
- Si la description parle de scalable/prod, favorise postgres et k8s; sinon sqlite et docker_compose.
- Donne "reasons" (liste) et "confidence" (0..1).
"""
    # Essai LLM
    llm = LLMClient()
    data = llm.extract_json(SYSTEM, prompt) or {}
    # Fallback simple si LLM indisponible
    if not data:
        data = {
            "web": spec.web or "fastapi",
            "db": spec.db or "postgres",
            "infra": spec.infra or "docker_compose",
            "ci": spec.ci or "github_actions",
            "reasons": ["Fallback heuristique"],
            "confidence": 0.6,
        }

    # On met à jour la spec seulement là où l'utilisateur n'a pas forcé
    updated = spec.dict()
    for k in ["web","db","infra","ci"]:
        if (updated.get(k) in (None, "", "auto")) and data.get(k):
            updated[k] = data[k]

    state["spec"] = updated
    state["tech_selection"] = data
    state["logs"].append(f"TechSelector: {data}")
    return state
