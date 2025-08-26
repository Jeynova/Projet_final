import os
from dotenv import load_dotenv
from core.llm_client import LLMClient

# Load environment
load_dotenv()

# Test the actual system prompt used in spec_extractor
SYSTEM_PROMPT = (
    "Tu es un extracteur qui convertit une demande en spec de projet. "
    "Renvoie strictement un JSON avec ces champs EXACTEMENT: "
    "name (string), "
    "project_type ('api' ou 'webapp' ou 'worker'), "
    "language ('python' ou 'node'), "
    "web ('fastapi' ou 'flask' ou 'express'), "
    "db ('postgres' ou 'sqlite' ou 'mysql' ou 'none'), "
    "auth ('none' ou 'jwt' ou 'session'), "
    "features (array de strings), "
    "tests ('none' ou 'basic' ou 'crud'), "
    "ci ('none' ou 'github_actions'), "
    "security ('baseline' ou 'strict'), "
    "dockerize (true ou false), "
    "infra ('docker_compose' ou 'k8s'), "
    "entities (array d'objets avec name et fields). "
    "EXEMPLE entities: [{'name': 'User', 'fields': ['email', 'password']}, {'name': 'Post', 'fields': ['title', 'content']}]. "
    "IMPORTANT: Utilise EXACTEMENT ces valeurs, pas d'autres variantes !"
)

USER_PROMPT = "API with users(email unique, password_hash) and products(name, price float, description, user_id FK)"

print("Testing LLM with actual prompts...")
print(f"System prompt length: {len(SYSTEM_PROMPT)}")
print(f"User prompt: {USER_PROMPT}")

client = LLMClient()
result = client.extract_json(SYSTEM_PROMPT, USER_PROMPT)

print(f"LLM Result: {result}")
print(f"Result type: {type(result)}")
