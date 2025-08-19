import re
from typing import Tuple, Dict, Any
from .specs import ProjectSpec
from .mappings import WEB_SYNONYMS, DB_SYNONYMS, AUTH_SYNONYMS
from .llm_client import LLMClient

SYSTEM_PROMPT = (
    "Tu es un extracteur qui convertit une demande en spec de projet. "
    "Renvoie strictement un JSON avec ces champs: name, project_type, language, web, db, auth, features, tests, ci, security, dockerize, infra."
)

DEFAULTS = {
    "project_type": "api",
    "language": "python",
    "web": None,
    "db": "sqlite",
    "auth": "jwt",
    "features": [],
    "tests": "basic",
    "ci": "github_actions",
    "security": "baseline",
    "dockerize": True,
    "infra": "docker_compose",
}

class SpecExtractor:
    def __init__(self):
        self.llm = LLMClient()

    def _heuristic(self, prompt: str) -> Dict[str, Any]:
        text = prompt.lower()
        name = re.findall(r"(nom|name)[:\s]+([\w\- ]{3,50})", text)
        name_val = name[0][1].strip() if name else "generated-project"

        web = None
        for k, v in WEB_SYNONYMS.items():
            if k in text:
                web = v; break

        db = DEFAULTS["db"]
        for k, v in DB_SYNONYMS.items():
            if re.search(rf"\b{k}\b", text):
                db = v; break

        auth = DEFAULTS["auth"]
        for k, v in AUTH_SYNONYMS.items():
            if re.search(rf"\b{k}\b", text):
                auth = v; break

        features = []
        if any(word in text for word in ["vehicle", "véhicule", "flotte", "drivers", "conducteur"]):
            features += ["crud:vehicles"]
        if "health" in text or "healthcheck" in text:
            features += ["healthcheck"]
        if "rate" in text or "limite" in text:
            features += ["rate_limit"]

        data = {
            "name": name_val,
            "project_type": "api",
            "language": "python",
            "web": web,
            "db": db,
            "auth": auth,
            "features": features,
            "tests": "basic",
            "ci": "github_actions",
            "security": "baseline",
            "dockerize": True,
            "infra": "docker_compose",
        }
        return data

    def extract(self, prompt: str) -> Tuple[ProjectSpec, Dict[str, float]]:
        # 1) Essai LLM (si dispo)
        llm_json = self.llm.extract_json(SYSTEM_PROMPT, prompt)
        if isinstance(llm_json, dict):
            try:
                spec = ProjectSpec(**{**DEFAULTS, **llm_json})
                # Compatible with both Pydantic v1 and v2
                field_names = list(spec.model_fields.keys()) if hasattr(spec, 'model_fields') else list(spec.__fields__.keys())
                conf = {field_name: 0.9 for field_name in field_names}
                return spec, conf
            except Exception:
                pass
        # 2) Heuristique fallback (sans réseau)
        data = self._heuristic(prompt)
        spec = ProjectSpec(**{**DEFAULTS, **data})
        # Compatible with both Pydantic v1 and v2
        field_names = list(spec.model_fields.keys()) if hasattr(spec, 'model_fields') else list(spec.__fields__.keys())
        conf = {field_name: 0.6 for field_name in field_names}
        if data.get("web"): conf["web"] = 0.8
        return spec, conf