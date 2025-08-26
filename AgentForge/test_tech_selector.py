import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("=== Environment Check ===")
print(f"AGENTFORGE_LLM: {os.getenv('AGENTFORGE_LLM')}")
print(f"AGENTFORGE_AGENTIC: {os.getenv('AGENTFORGE_AGENTIC')}")
print(f"OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL')}")
print(f"OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")

# Test the issue with the TechSelector specifically
try:
    from orchestrator.tech_selector_smol import run_tech_selector_smol
    print("✅ tech_selector_smol import successful")
    
    # Test state
    state = {
        'prompt': 'API with users(email, password) and tasks(title, description)',
        'spec': {
            'name': 'test',
            'project_type': 'api',
            'language': 'python',
            'web': 'fastapi',
            'db': 'postgres',
            'auth': 'jwt',
            'features': [],
            'tests': 'basic',
            'ci': 'github_actions',
            'security': 'baseline',
            'dockerize': True,
            'infra': 'docker_compose',
            'entities': []
        },
        'logs': []
    }
    
    print("=== Testing TechSelector ===")
    result = run_tech_selector_smol(state)
    print(f"TechSelector result: {result.get('tech_selection', 'No tech_selection key')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
