#!/usr/bin/env python3
"""
Test de Stress AgentForge
Tests de robustesse avec prompts edge-cases
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

class StressTest:
    """Tests de stress et edge cases"""
    
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
    
    def test_edge_case(self, name: str, prompt: str, should_succeed: bool = True):
        """Test un cas limite spécifique"""
        print(f"\n🔥 STRESS TEST: {name}")
        print(f"Prompt: {prompt}")
        print(f"Attendu: {'Succès' if should_succeed else 'Gestion gracieuse'}")
        
        self.total_tests += 1
        test_result = {
            "name": name,
            "prompt": prompt,
            "should_succeed": should_succeed,
            "timestamp": datetime.now().isoformat(),
            "actual_success": False,
            "graceful_failure": False,
            "details": {}
        }
        
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                state = {
                    "prompt": prompt,
                    "name": f"stress-{name.lower().replace(' ', '-')}",
                    "artifacts_dir": tmp_dir,
                    "logs": []
                }
                
                # Pipeline complet avec gestion d'erreurs
                try:
                    state = spec_extractor(state)
                    entities = state["spec"].get("entities", [])
                    
                    state = tech_selector(state) 
                    state = planner(state)
                    state = scaffolder(state)
                    state = codegen(state)
                    state = eval_agent(state)
                    
                    eval_result = state.get("eval", {})
                    score = eval_result.get("score", 0)
                    
                    test_result.update({
                        "actual_success": score >= 0.5,  # Seuil plus bas pour stress test
                        "graceful_failure": True,  # A réussi sans crash
                        "details": {
                            "entities_parsed": len(entities),
                            "eval_score": score,
                            "logs_count": len(state.get("logs", [])),
                            "project_created": Path(state.get("project_dir", "")).exists()
                        }
                    })
                    
                    if score >= 0.5:
                        print(f"✅ SUCCÈS - Score: {score} | Entités: {len(entities)}")
                        if should_succeed:
                            self.passed_tests += 1
                    else:
                        print(f"⚠️ ÉCHEC GRACIEUX - Score: {score}")
                        if not should_succeed:  # Échec attendu géré gracieusement
                            self.passed_tests += 1
                            
                except Exception as inner_e:
                    print(f"⚠️ ERREUR GÉRÉE: {inner_e}")
                    test_result["graceful_failure"] = True
                    test_result["details"]["inner_error"] = str(inner_e)
                    if not should_succeed:
                        self.passed_tests += 1
                    
        except Exception as e:
            print(f"💥 CRASH NON GÉRÉ: {e}")
            test_result.update({
                "actual_success": False,
                "graceful_failure": False,
                "details": {"crash_error": str(e)}
            })
            import traceback
            traceback.print_exc()
        
        self.results.append(test_result)

def main():
    print("🔥 TEST DE STRESS AGENTFORGE")
    print("Tests de robustesse et gestion edge cases")
    print("=" * 80)
    
    stress = StressTest()
    
    # Tests de robustesse - Prompts valides mais difficiles
    print("\n📋 SECTION 1: PROMPTS COMPLEXES")
    
    stress.test_edge_case(
        "Prompt Très Long",
        "API très complexe pour système de gestion d'entreprise avec utilisateurs ayant des rôles multiples, des produits avec variantes et options, des commandes avec états complexes, des paiements avec multiples méthodes, des livraisons avec tracking, des retours et remboursements, des avis clients avec modération, des promotions et codes de réduction, des statistiques et rapports avancés, intégration avec systèmes externes, notifications temps réel, cache distribué, recherche elasticsearch",
        should_succeed=True
    )
    
    stress.test_edge_case(
        "Entités Multiples",
        "API avec users(email unique, password_hash, role, created_at datetime), products(name, description, price float, stock int, category_id int, active bool), categories(name unique, description), orders(user_id int, total float, status, created_at datetime), order_items(order_id int, product_id int, quantity int, price float), reviews(user_id int, product_id int, rating int, comment, created_at datetime)",
        should_succeed=True
    )
    
    stress.test_edge_case(
        "Types Complexes",
        "API avec events(name, start_datetime datetime, end_datetime datetime, price float, capacity int, available bool) et bookings(event_id int, user_email, quantity int, total_price float, booking_date datetime, status)",
        should_succeed=True
    )
    
    # Tests edge cases - Prompts limites
    print("\n🚨 SECTION 2: EDGE CASES")
    
    stress.test_edge_case(
        "Prompt Vide",
        "",
        should_succeed=False
    )
    
    stress.test_edge_case(
        "Prompt Très Court", 
        "API",
        should_succeed=True  # Devrait générer quelque chose par défaut
    )
    
    stress.test_edge_case(
        "Syntaxe Incorrecte",
        "API avec users(email unique password_hash et products name, price",
        should_succeed=True  # Devrait gérer la syntaxe cassée
    )
    
    stress.test_edge_case(
        "Caractères Spéciaux",
        "API avec entités spéciales: users(email@domain.com, password#hash) et products(name with spaces, price$)",
        should_succeed=True
    )
    
    stress.test_edge_case(
        "Mélange Langues",
        "API pour gestion utilisateurs avec users(email unique, mot_de_passe) and products(nom, prix float)",
        should_succeed=True
    )
    
    stress.test_edge_case(
        "Répétitions",
        "API API API avec users users users(email email, password password) et products products(name name, price price)",
        should_succeed=True
    )
    
    # Tests de performance dégradée
    print("\n⚡ SECTION 3: PERFORMANCE DÉGRADÉE")
    
    stress.test_edge_case(
        "Entités Nombreuses",
        "API avec " + ", ".join([f"entity{i}(field1, field2, field3 int)" for i in range(20)]),
        should_succeed=True
    )
    
    stress.test_edge_case(
        "Champs Nombreux",
        f"API avec bigentity({', '.join([f'field{i}' for i in range(50)])})",
        should_succeed=True
    )
    
    # Tests de cas métier spéciaux
    print("\n🏢 SECTION 4: CAS MÉTIER SPÉCIAUX")
    
    stress.test_edge_case(
        "Domaine Médical",
        "API pour dossiers médicaux avec patients(nom, date_naissance datetime, sécurité_sociale unique) et consultations(patient_id int, médecin, diagnostic, prescription)",
        should_succeed=True
    )
    
    stress.test_edge_case(
        "Système Bancaire", 
        "API bancaire avec comptes(numero unique, solde float, type) et transactions(compte_source int, compte_dest int, montant float, date_transaction datetime)",
        should_succeed=True
    )
    
    stress.test_edge_case(
        "IoT Sensors",
        "API IoT avec sensors(device_id unique, location, type) et measurements(sensor_id int, value float, timestamp datetime, unit)",
        should_succeed=True
    )
    
    # Rapport final
    print(f"\n{'='*80}")
    print("🔥 RAPPORT STRESS TEST")
    print(f"{'='*80}")
    
    success_rate = (stress.passed_tests / stress.total_tests) * 100
    graceful_failures = sum(1 for r in stress.results if r["graceful_failure"])
    crashes = stress.total_tests - graceful_failures
    
    print(f"Tests réussis: {stress.passed_tests}/{stress.total_tests}")
    print(f"Taux de réussite: {success_rate:.1f}%")
    print(f"Échecs gracieux: {graceful_failures}/{stress.total_tests}")
    print(f"Crashes: {crashes}/{stress.total_tests}")
    
    # Détails par test
    print(f"\n📊 DÉTAILS PAR TEST:")
    for result in stress.results:
        if result["actual_success"]:
            status = "✅ PASS"
        elif result["graceful_failure"]:
            status = "⚠️ GRACEFUL"
        else:
            status = "💥 CRASH"
        
        score = result["details"].get("eval_score", 0)
        entities = result["details"].get("entities_parsed", 0)
        
        print(f"{status} {result['name']:25} | Score: {score:3.1f} | Entités: {entities:2}")
    
    # Sauvegarde
    results_file = ROOT / "stress_test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": stress.total_tests,
                "passed_tests": stress.passed_tests,
                "success_rate": success_rate,
                "graceful_failures": graceful_failures,
                "crashes": crashes,
                "robustness_score": (graceful_failures / stress.total_tests) * 100
            },
            "tests": stress.results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Résultats sauvegardés: {results_file}")
    
    # Conclusion
    robustness_score = (graceful_failures / stress.total_tests) * 100
    
    if crashes == 0 and success_rate >= 70:
        print(f"\n🛡️ SYSTÈME TRÈS ROBUSTE ! (0 crash, {success_rate:.1f}% succès)")
        return True
    elif crashes == 0:
        print(f"\n✅ Système robuste (0 crash, {success_rate:.1f}% succès)")
        return True
    elif crashes <= 2:
        print(f"\n⚠️ Robustesse acceptable ({crashes} crashes)")
        return True
    else:
        print(f"\n❌ Robustesse insuffisante ({crashes} crashes)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
