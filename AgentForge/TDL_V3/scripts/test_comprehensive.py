#!/usr/bin/env python3
"""
Suite de Tests Complète AgentForge
Tests de validation pour différents scénarios d'usage
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add project to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from orchestrator.agents import spec_extractor, planner, scaffolder, tech_selector, codegen, eval_agent

class TestScenarios:
    """Tests de validation pour différents scénarios"""
    
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
    
    def run_scenario(self, name: str, prompt: str, expected_entities: int = None):
        """Exécute un scénario de test complet"""
        print(f"\n{'='*60}")
        print(f"🧪 TEST SCENARIO: {name}")
        print(f"{'='*60}")
        print(f"Prompt: {prompt}")
        
        self.total_tests += 1
        scenario_result = {
            "name": name,
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "details": {}
        }
        
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # État initial
                state = {
                    "prompt": prompt,
                    "name": f"test-{name.lower().replace(' ', '-')}",
                    "artifacts_dir": tmp_dir,
                    "logs": []
                }
                
                # Pipeline complet
                print("1️⃣ spec_extractor...")
                state = spec_extractor(state)
                entities = state["spec"].get("entities", [])
                print(f"   ✅ Entités détectées: {len(entities)}")
                for e in entities:
                    print(f"     - {e['name']}: {len(e['fields'])} champs")
                
                print("2️⃣ tech_selector...")
                state = tech_selector(state)
                tech = state.get("tech_selection", {})
                print(f"   ✅ Stack: {tech.get('web', 'N/A')}, {tech.get('db', 'N/A')}")
                
                print("3️⃣ planner...")
                state = planner(state)
                print(f"   ✅ Preset: {state.get('preset', 'N/A')}")
                
                print("4️⃣ scaffolder...")
                state = scaffolder(state)
                project_path = Path(state["project_dir"])
                print(f"   ✅ Projet créé: {project_path.exists()}")
                
                print("5️⃣ codegen...")
                state = codegen(state)
                
                print("6️⃣ eval_agent...")
                state = eval_agent(state)
                eval_result = state.get("eval", {})
                score = eval_result.get("score", 0)
                print(f"   ✅ Score: {score}")
                
                # Vérifications spécifiques
                files_count = len(list(project_path.rglob("*"))) if project_path.exists() else 0
                
                # Résultats
                scenario_result.update({
                    "success": score >= 0.8,
                    "details": {
                        "entities_parsed": len(entities),
                        "entities_expected": expected_entities,
                        "tech_stack": tech,
                        "preset": state.get("preset"),
                        "files_generated": files_count,
                        "eval_score": score,
                        "eval_details": eval_result,
                        "logs_count": len(state.get("logs", []))
                    }
                })
                
                if score >= 0.8:
                    print(f"✅ SUCCÈS - Score: {score}")
                    if expected_entities and len(entities) == expected_entities:
                        print(f"✅ Nombre d'entités correct: {len(entities)}/{expected_entities}")
                    self.passed_tests += 1
                else:
                    print(f"❌ ÉCHEC - Score insuffisant: {score}")
                    
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            scenario_result["error"] = str(e)
            import traceback
            traceback.print_exc()
        
        self.results.append(scenario_result)
        return scenario_result["success"]

def main():
    print("🚀 SUITE DE TESTS COMPLÈTE AGENTFORGE")
    print("=" * 80)
    
    test_suite = TestScenarios()
    
    # Scénario 1: API Simple
    test_suite.run_scenario(
        "API Simple",
        "API simple pour blog avec articles et commentaires",
        expected_entities=2
    )
    
    # Scénario 2: Parsing Explicite  
    test_suite.run_scenario(
        "Parsing Explicite",
        "API avec users(email unique, password_hash) et products(name, price float, stock int)",
        expected_entities=2
    )
    
    # Scénario 3: E-commerce Complex
    test_suite.run_scenario(
        "E-commerce Complex",
        "API e-commerce avec users(email unique, role), products(name, price float, category_id int), orders(user_id int, status, total float)",
        expected_entities=3
    )
    
    # Scénario 4: Fleet Management
    test_suite.run_scenario(
        "Fleet Management", 
        "API gestion de flotte avec drivers(license_number unique, name) et vehicles(license_plate unique, make, model, driver_id int)",
        expected_entities=2
    )
    
    # Scénario 5: Sans entités explicites
    test_suite.run_scenario(
        "Détection Automatique",
        "API pour gestion des utilisateurs et véhicules avec authentification JWT",
        expected_entities=2
    )
    
    # Scénario 6: Types complexes
    test_suite.run_scenario(
        "Types Complexes",
        "API avec events(name, start_date datetime, price float, active bool) et tickets(event_id int, buyer_email unique)",
        expected_entities=2
    )
    
    # Rapport final
    print(f"\n{'='*80}")
    print("📊 RAPPORT FINAL")
    print(f"{'='*80}")
    
    success_rate = (test_suite.passed_tests / test_suite.total_tests) * 100
    print(f"Tests réussis: {test_suite.passed_tests}/{test_suite.total_tests}")
    print(f"Taux de réussite: {success_rate:.1f}%")
    
    # Détails par scénario
    for result in test_suite.results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        score = result["details"].get("eval_score", 0)
        entities = result["details"].get("entities_parsed", 0)
        files = result["details"].get("files_generated", 0)
        
        print(f"{status} {result['name']:20} | Score: {score:3.1f} | Entités: {entities:2} | Fichiers: {files:2}")
    
    # Sauvegarde résultats
    results_file = ROOT / "test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": test_suite.total_tests,
                "passed_tests": test_suite.passed_tests,
                "success_rate": success_rate
            },
            "scenarios": test_suite.results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Résultats sauvegardés: {results_file}")
    
    if success_rate >= 80:
        print(f"\n🎉 SUITE DE TESTS RÉUSSIE ! ({success_rate:.1f}%)")
        return True
    else:
        print(f"\n❌ Suite de tests échouée ({success_rate:.1f}%)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
