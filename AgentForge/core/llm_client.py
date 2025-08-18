import os
from typing import Optional, Dict, Any

class LLMClient:
    def __init__(self):
        self.provider = os.getenv("AGENTFORGE_LLM", "mock")

    def extract_json(self, system_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        if self.provider == "mock":
            # Baseline déterministe (sans réseau) pour le MVP J1
            return None
        if self.provider == "openai":
            try:
                from openai import OpenAI
                client = OpenAI()
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                resp = client.responses.create(
                    model=model,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                # openai>=1.0 – récupérer le texte JSON
                content = resp.output_text
                import json
                return json.loads(content)
            except Exception:
                return None
        if self.provider == "ollama":
            try:
                import requests, json
                base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
                payload = {
                    "model": model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}\nRéponds en JSON valide uniquement.",
                    "format": "json",
                    "stream": False,
                }
                r = requests.post(f"{base}/api/generate", json=payload, timeout=120)
                r.raise_for_status()
                data = r.json()
                return json.loads(data.get("response", "{}"))
            except Exception:
                return None
        return None