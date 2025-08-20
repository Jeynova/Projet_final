#!/usr/bin/env python3
"""
Test d'Intégration AgentForge UI
Tests de l'interface Flask avec scénarios utilisateur
"""

import sys
import requests
import json
import time
import threading
from pathlib import Path
from datetime import datetime
import subprocess
import signal
import os

# Add project to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

class UIIntegrationTest:
    """Tests d'intégration de l'interface utilisateur Flask"""
    
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.server_process = None
    
    def start_flask_server(self):
        """Démarre le serveur Flask en arrière-plan"""
        print("🚀 Démarrage du serveur Flask...")
        
        try:
            # Démarrer Flask en subprocess
            flask_script = ROOT / "apps" / "ui_flask" / "app.py"
            self.server_process = subprocess.Popen([
                sys.executable, str(flask_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Attendre que le serveur soit prêt
            for i in range(30):  # 30 secondes max
                try:
                    response = requests.get(f"{self.base_url}/", timeout=1)
                    if response.status_code == 200:
                        print("✅ Serveur Flask démarré !")
                        return True
                except:
                    pass
                time.sleep(1)
            
            print("❌ Impossible de démarrer le serveur Flask")
            return False
            
        except Exception as e:
            print(f"❌ Erreur démarrage serveur: {e}")
            return False
    
    def stop_flask_server(self):
        """Arrête le serveur Flask"""
        if self.server_process:
            print("🛑 Arrêt du serveur Flask...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
    
    def test_endpoint(self, name: str, method: str, endpoint: str, data=None, expected_status=200, timeout=30):
        """Test un endpoint spécifique"""
        print(f"\n🧪 TEST UI: {name}")
        print(f"Endpoint: {method} {endpoint}")
        
        self.total_tests += 1
        test_result = {
            "name": name,
            "method": method,
            "endpoint": endpoint,
            "expected_status": expected_status,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "details": {}
        }
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            else:
                response = requests.request(method, url, json=data, timeout=timeout)
            
            response_time = time.time() - start_time
            
            test_result.update({
                "success": response.status_code == expected_status,
                "details": {
                    "actual_status": response.status_code,
                    "response_time": round(response_time, 3),
                    "content_length": len(response.content),
                    "content_type": response.headers.get("Content-Type", ""),
                    "has_json": self._is_json_response(response)
                }
            })
            
            # Analyse du contenu
            if response.headers.get("Content-Type", "").startswith("text/html"):
                test_result["details"]["has_html_structure"] = self._check_html_structure(response.text)
            
            if response.status_code == expected_status:
                print(f"✅ SUCCÈS - Status: {response.status_code} | Temps: {response_time:.3f}s")
                self.passed_tests += 1
            else:
                print(f"❌ ÉCHEC - Status: {response.status_code} (attendu {expected_status})")
                
        except requests.exceptions.Timeout:
            print(f"⏱️ TIMEOUT - Pas de réponse en {timeout}s")
            test_result["details"]["error"] = "timeout"
        except Exception as e:
            print(f"💥 ERREUR - {e}")
            test_result["details"]["error"] = str(e)
        
        self.results.append(test_result)
    
    def _is_json_response(self, response):
        """Vérifie si la réponse est du JSON valide"""
        try:
            response.json()
            return True
        except:
            return False
    
    def _check_html_structure(self, html):
        """Vérifie la structure HTML basique"""
        checks = {
            "has_doctype": html.strip().lower().startswith("<!doctype"),
            "has_html_tag": "<html" in html.lower(),
            "has_head_tag": "<head" in html.lower(),
            "has_body_tag": "<body" in html.lower(),
            "has_title": "<title" in html.lower()
        }
        return checks
    
    def test_generation_flow(self, name: str, prompt: str):
        """Test complet de génération de projet"""
        print(f"\n🔄 TEST FLUX COMPLET: {name}")
        print(f"Prompt: {prompt[:50]}...")
        
        self.total_tests += 1
        test_result = {
            "name": f"Flow: {name}",
            "type": "generation_flow",
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "details": {}
        }
        
        try:
            # 1. POST vers generate
            generate_data = {"prompt": prompt}
            start_time = time.time()
            
            response = requests.post(f"{self.base_url}/generate", json=generate_data, timeout=120)
            
            generation_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                test_result.update({
                    "success": "success" in result,
                    "details": {
                        "generation_time": round(generation_time, 2),
                        "response_keys": list(result.keys()),
                        "has_project_id": "project_id" in result,
                        "success_status": result.get("success", False)
                    }
                })
                
                # 2. Test preview si project_id disponible
                if result.get("project_id"):
                    project_id = result["project_id"]
                    preview_response = requests.get(f"{self.base_url}/preview/{project_id}")
                    test_result["details"]["preview_accessible"] = preview_response.status_code == 200
                
                if result.get("success"):
                    print(f"✅ GÉNÉRATION COMPLÈTE - Temps: {generation_time:.2f}s")
                    self.passed_tests += 1
                else:
                    print(f"⚠️ GÉNÉRATION PARTIELLE - Temps: {generation_time:.2f}s")
            else:
                print(f"❌ ÉCHEC GÉNÉRATION - Status: {response.status_code}")
                test_result["details"]["error_status"] = response.status_code
                
        except Exception as e:
            print(f"💥 ERREUR FLUX - {e}")
            test_result["details"]["error"] = str(e)
        
        self.results.append(test_result)

def main():
    """Exécute la suite de tests d'intégration UI"""
    print("🧪 TESTS D'INTÉGRATION AGENTFORGE UI")
    print("Tests de l'interface Flask avec scénarios utilisateur")
    print("=" * 80)
    
    ui_test = UIIntegrationTest()
    
    # Démarrer le serveur
    if not ui_test.start_flask_server():
        print("💥 Impossible de démarrer le serveur - Tests annulés")
        return False
    
    try:
        # Tests basiques des endpoints
        print("\n📋 SECTION 1: ENDPOINTS BASIQUES")
        
        ui_test.test_endpoint("Page Accueil", "GET", "/")
        ui_test.test_endpoint("Assets CSS", "GET", "/static/style.css")
        ui_test.test_endpoint("Endpoint Inexistant", "GET", "/nonexistent", expected_status=404)
        
        # Tests API
        print("\n🔌 SECTION 2: API ENDPOINTS")
        
        ui_test.test_endpoint("Health Check", "GET", "/api/health")
        ui_test.test_endpoint("Projects List", "GET", "/api/projects")
        
        # Tests de génération
        print("\n⚙️ SECTION 3: GÉNÉRATION DE PROJETS")
        
        ui_test.test_generation_flow(
            "API Simple",
            "API pour gestion utilisateurs avec users(email unique, password_hash) et authentification"
        )
        
        ui_test.test_generation_flow(
            "E-commerce Basique", 
            "API e-commerce avec products(name, price float, stock int) et orders(user_id int, total float)"
        )
        
        # Tests edge cases UI
        print("\n🚨 SECTION 4: EDGE CASES UI")
        
        ui_test.test_endpoint("POST sans data", "POST", "/generate", data=None, expected_status=400)
        ui_test.test_endpoint("POST data vide", "POST", "/generate", data={}, expected_status=400)
        ui_test.test_endpoint("Preview ID invalide", "GET", "/preview/invalid-id", expected_status=404)
        
        # Tests de performance UI
        print("\n⚡ SECTION 5: PERFORMANCE UI")
        
        ui_test.test_generation_flow(
            "Prompt Complexe",
            "API complexe avec users, products, orders, payments, reviews, notifications et gestion complète e-commerce"
        )
        
        # Génération du rapport
        print(f"\n{'='*80}")
        print("🧪 RAPPORT TESTS D'INTÉGRATION UI")
        print(f"{'='*80}")
        
        success_rate = (ui_test.passed_tests / ui_test.total_tests) * 100
        
        print(f"Tests réussis: {ui_test.passed_tests}/{ui_test.total_tests}")
        print(f"Taux de réussite: {success_rate:.1f}%")
        
        # Analyse des temps de réponse
        response_times = []
        generation_times = []
        
        for result in ui_test.results:
            if "response_time" in result.get("details", {}):
                response_times.append(result["details"]["response_time"])
            if "generation_time" in result.get("details", {}):
                generation_times.append(result["details"]["generation_time"])
        
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            print(f"Temps réponse moyen: {avg_response:.3f}s")
        
        if generation_times:
            avg_generation = sum(generation_times) / len(generation_times)
            print(f"Temps génération moyen: {avg_generation:.1f}s")
        
        # Détails par test
        print(f"\n📊 DÉTAILS PAR TEST:")
        for result in ui_test.results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            
            if "response_time" in result.get("details", {}):
                timing = f"| {result['details']['response_time']:.3f}s"
            elif "generation_time" in result.get("details", {}):
                timing = f"| {result['details']['generation_time']:.1f}s"
            else:
                timing = ""
            
            print(f"{status} {result['name']:30} {timing}")
        
        # Sauvegarde des résultats
        results_file = ROOT / "ui_integration_test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": ui_test.total_tests,
                    "passed_tests": ui_test.passed_tests,
                    "success_rate": success_rate,
                    "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                    "avg_generation_time": sum(generation_times) / len(generation_times) if generation_times else 0
                },
                "tests": ui_test.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Résultats sauvegardés: {results_file}")
        
        # Conclusion
        if success_rate >= 90:
            print(f"\n🎉 INTERFACE EXCELLENTE ! ({success_rate:.1f}% succès)")
            return True
        elif success_rate >= 75:
            print(f"\n✅ Interface fonctionnelle ({success_rate:.1f}% succès)")
            return True
        else:
            print(f"\n⚠️ Interface à améliorer ({success_rate:.1f}% succès)")
            return False
        
    finally:
        # Arrêter le serveur
        ui_test.stop_flask_server()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
