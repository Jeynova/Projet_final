"""Test des améliorations du TechSelector"""

from dotenv import load_dotenv
load_dotenv()

from orchestrator.tech_selector_smol import run_tech_selector_smol

# Test avec technologies à mapper
state = {
    'prompt': 'Application e-commerce Django avec MongoDB et Jenkins CI sur Kubernetes',
    'spec': {'name': 'ecommerce', 'web': 'auto', 'db': 'auto', 'infra': 'auto', 'ci': 'auto'},
    'logs': []
}

print("=== TEST AMÉLIORATIONS TECH SELECTOR ===")
print("Prompt:", state['prompt'])
print("Processing...")

result = run_tech_selector_smol(state)

print("\n=== RÉSULTATS ===")
sel = result.get('tech_selection', {})
raw = result.get('tech_selection_raw', {})

print("CHOIX RAW LLM:", raw)
print("CHOIX MAPPÉS:", {k: sel.get(k) for k in ('web','db','infra','ci')})
print("CONFIDENCE:", sel.get('confidence'))

print("\n=== LOGS MAPPING ===")
for log in result['logs']:
    print(f"  {log}")

print("\n=== RAISONS ===")
if 'reasons' in sel:
    for i, reason in enumerate(sel['reasons'][:3], 1):
        print(f"  {i}. {reason}")
