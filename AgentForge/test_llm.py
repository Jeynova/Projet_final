import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment
load_dotenv()

print("Environment variables:")
print(f"AGENTFORGE_LLM: {os.getenv('AGENTFORGE_LLM')}")
print(f"AGENTFORGE_AGENTIC: {os.getenv('AGENTFORGE_AGENTIC')}")
print(f"OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL')}")
print(f"OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")

# Test LLM client
from core.llm_client import LLMClient

client = LLMClient()
print(f"LLM Provider: {client.provider}")

# Simple test
result = client.extract_json(
    "Respond with JSON only: {'status': 'ok', 'message': 'test'}",
    "Please respond with the requested JSON"
)
print(f"LLM Result: {result}")
