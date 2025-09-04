import os
from typing import Optional, Dict, Any

class LLMClient:
    def __init__(self, preferred_model=None):
        self.provider = os.getenv("AGENTFORGE_LLM", "mock")
        self.preferred_model = preferred_model  # Agent-specific model preference

    def extract_json(self, system_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        if self.provider == "mock":
            # Baseline déterministe (sans réseau) pour le MVP J1
            return None
        if self.provider == "openai":
            try:
                from openai import OpenAI
                client = OpenAI()
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                content = resp.choices[0].message.content
                import json
                return json.loads(content)
            except Exception:
                return None
        if self.provider == "ollama":
            try:
                import requests, json
                base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                # Use preferred model if specified, otherwise fall back to env var
                model = self.preferred_model or os.getenv("OLLAMA_MODEL", "llama3.1:latest")
                print(f"🔧 DEBUG Ollama: base={base}, model={model}")
                payload = {
                    "model": model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}\nRéponds en JSON valide uniquement.",
                    "format": "json",
                    "stream": False,
                    "options": {
                        "num_predict": 1024,  # Longer responses for JSON
                        "temperature": 0.3,   # More focused for structured output
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                }
                print(f"🚀 DEBUG Ollama: Envoi requête...")
                r = requests.post(f"{base}/api/generate", json=payload, timeout=120)
                r.raise_for_status()
                data = r.json()
                print(f"✅ DEBUG Ollama: Réponse reçue: {data.get('response', '')[:100]}...")
                return json.loads(data.get("response", "{}"))
            except Exception as e:
                print(f"❌ DEBUG Ollama: Exception: {e}")
                # Try to fix common JSON issues
                try:
                    response_text = data.get("response", "{}")
                    print(f"🔧 DEBUG Ollama: Attempting JSON repair on: {response_text[:200]}...")
                    
                    # Common fixes for malformed JSON
                    fixed_json = response_text
                    
                    # Fix trailing commas
                    import re
                    fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                    
                    # Fix missing commas between elements
                    fixed_json = re.sub(r'"\s*\n\s*"', r'",\n"', fixed_json)
                    fixed_json = re.sub(r'}\s*\n\s*{', r'},\n{', fixed_json)
                    fixed_json = re.sub(r']\s*\n\s*\[', r'],\n[', fixed_json)
                    
                    # Fix missing quotes around keys
                    fixed_json = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed_json)
                    
                    # Try to parse the fixed JSON
                    return json.loads(fixed_json)
                except:
                    print(f"❌ DEBUG Ollama: JSON repair failed, returning empty dict")
                    return {}
        return None

    def get_raw_response(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Get raw text response when JSON parsing fails"""
        if self.provider == "ollama":
            try:
                import requests
                base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                # Use preferred model if specified, otherwise fall back to env var
                model = self.preferred_model or os.getenv("OLLAMA_MODEL", "llama3.1:latest")
                print(f"🔧 {self.preferred_model or 'DEFAULT'}: using model {model}")
                payload = {
                    "model": model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False,
                    "options": {
                        "num_predict": 2048,  # Force longer responses
                        "temperature": 0.7,   # More creative
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                }
                r = requests.post(f"{base}/api/generate", json=payload, timeout=120)
                r.raise_for_status()
                data = r.json()
                return data.get("response", "")
            except Exception as e:
                print(f"❌ Raw response failed: {e}")
                return None
        return None