import os
os.environ['AGENTFORGE_LLM'] = 'ollama'
os.environ['AGENTFORGE_AGENTIC'] = '1'

from orchestrator.graph import build_app
from pathlib import Path

state = {
    'prompt': 'API with users(email, password) and products(name, price)',
    'name': 'test-debug',
    'artifacts_dir': str(Path('generated')),
    'logs': []
}

print("=== STARTING FULL PIPELINE ===")
app = build_app()
result = app.invoke(state)

print("\n=== FINAL RESULT ===")
for log in result.get('logs', []):
    print(f'LOG: {log}')
print(f'Status: {result.get("status")}')
print(f'Project dir: {result.get("project_dir")}')

# Check entities in final spec
spec = result.get('spec', {})
entities = spec.get('entities', [])
print(f'Final entities count: {len(entities)}')
for entity in entities:
    print(f'  Entity: {entity.get("name")} with {len(entity.get("fields", []))} fields')
