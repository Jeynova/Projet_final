#!/usr/bin/env python3
"""
Maître de Tests AgentForge
Exécute toute la suite de tests avec rapport consolidé
"""

import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

class TestMaster:
    """Orchestrateur de tous les tests AgentForge"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_test_suite(self, name: str, script_path: Path, timeout: int = 300):
        """Exécute une suite de tests spécifique"""
        print(f"\n{'='*80}")
        print(f"🚀 EXÉCUTION: {name}")
        print(f"Script: {script_path.name}")
        print(f"Timeout: {timeout}s")
        print(f"{'='*80}")
        
        suite_start = time.time()
        
        try:
            # Exécuter le script de test
            result = subprocess.run([
                sys.executable, str(script_path)
            ], cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
            
            suite_time = time.time() - suite_start
            
            # Analyser les résultats
            suite_result = {
                "name": name,
                "script": script_path.name,
                "execution_time": round(suite_time, 2),
                "return_code": result.returncode,
                "success": result.returncode == 0,
                "stdout_lines": len(result.stdout.splitlines()),
                "stderr_lines": len(result.stderr.splitlines()),
                "timestamp": datetime.now().isoformat()
            }
            
            # Afficher sortie en temps réel
            if result.stdout:
                print(result.stdout)
            
            if result.stderr and result.returncode != 0:
                print("ERREURS:", file=sys.stderr)
                print(result.stderr, file=sys.stderr)
            
            # Statut final
            if result.returncode == 0:
                print(f"✅ {name} RÉUSSI - Temps: {suite_time:.2f}s")
            else:
                print(f"❌ {name} ÉCHEC - Code: {result.returncode}")
            
            self.results[name] = suite_result
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            suite_time = time.time() - suite_start
            print(f"⏱️ {name} TIMEOUT - Dépasse {timeout}s")
            
            self.results[name] = {
                "name": name,
                "script": script_path.name,
                "execution_time": timeout,
                "return_code": -1,
                "success": False,
                "timeout": True,
                "timestamp": datetime.now().isoformat()
            }
            return False
            
        except Exception as e:
            suite_time = time.time() - suite_start
            print(f"💥 {name} ERREUR CRITIQUE - {e}")
            
            self.results[name] = {
                "name": name,
                "script": script_path.name,  
                "execution_time": round(suite_time, 2),
                "return_code": -2,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return False
    
    def generate_consolidated_report(self):
        """Génère le rapport consolidé final"""
        print(f"\n{'='*80}")
        print("📊 RAPPORT CONSOLIDÉ - AGENTFORGE TEST MASTER")
        print(f"{'='*80}")
        
        total_time = self.end_time - self.start_time
        successful_suites = sum(1 for r in self.results.values() if r["success"])
        total_suites = len(self.results)
        success_rate = (successful_suites / total_suites) * 100 if total_suites > 0 else 0
        
        print(f"Durée totale: {total_time:.2f}s")
        print(f"Suites réussies: {successful_suites}/{total_suites}")
        print(f"Taux de réussite: {success_rate:.1f}%")
        
        print(f"\n📋 DÉTAIL PAR SUITE:")
        for suite_name, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            exec_time = result["execution_time"]
            
            # Indicateurs spéciaux
            indicators = []
            if result.get("timeout"):
                indicators.append("⏱️ TIMEOUT")
            if result.get("error"):
                indicators.append("💥 ERROR")
            if result["return_code"] < 0:
                indicators.append(f"RC:{result['return_code']}")
            
            indicator_str = " " + " ".join(indicators) if indicators else ""
            
            print(f"{status} {suite_name:25} | {exec_time:6.2f}s{indicator_str}")
        
        # Analyse des fichiers de résultats générés
        print(f"\n📁 FICHIERS DE RÉSULTATS:")
        result_files = [
            "test_comprehensive_results.json",
            "benchmark_results.json", 
            "stress_test_results.json",
            "ui_integration_test_results.json"
        ]
        
        consolidated_data = {}
        
        for filename in result_files:
            filepath = ROOT / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        consolidated_data[filename] = data
                        
                    size_kb = filepath.stat().st_size / 1024
                    print(f"✅ {filename:35} | {size_kb:6.1f} KB")
                    
                except Exception as e:
                    print(f"❌ {filename:35} | Erreur: {e}")
            else:
                print(f"⚠️ {filename:35} | Non trouvé")
        
        # Métriques consolidées
        print(f"\n🎯 MÉTRIQUES CONSOLIDÉES:")
        
        # Extraire les métriques des fichiers JSON
        total_individual_tests = 0
        total_passed_tests = 0
        
        for filename, data in consolidated_data.items():
            if "summary" in data:
                summary = data["summary"]
                tests = summary.get("total_tests", 0)
                passed = summary.get("passed_tests", 0)
                
                total_individual_tests += tests
                total_passed_tests += passed
                
                suite_rate = (passed / tests) * 100 if tests > 0 else 0
                print(f"{filename[:20]:20} | Tests: {passed:2}/{tests:2} ({suite_rate:5.1f}%)")
        
        if total_individual_tests > 0:
            overall_test_rate = (total_passed_tests / total_individual_tests) * 100
            print(f"{'TOTAL':20} | Tests: {total_passed_tests:2}/{total_individual_tests:2} ({overall_test_rate:5.1f}%)")
        
        # Sauvegarde rapport consolidé
        consolidated_report = {
            "timestamp": datetime.now().isoformat(),
            "execution_summary": {
                "total_time": total_time,
                "total_suites": total_suites,
                "successful_suites": successful_suites,
                "suite_success_rate": success_rate,
                "total_individual_tests": total_individual_tests,
                "total_passed_tests": total_passed_tests,
                "overall_test_success_rate": overall_test_rate if total_individual_tests > 0 else 0
            },
            "suite_results": self.results,
            "detailed_results": consolidated_data
        }
        
        master_report_file = ROOT / "master_test_report.json"
        with open(master_report_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Rapport maître sauvegardé: {master_report_file}")
        
        # Verdict final
        print(f"\n{'='*80}")
        
        if success_rate == 100 and overall_test_rate >= 90:
            print("🏆 AGENTFORGE VALIDATION COMPLÈTE ! Système prêt pour production")
            verdict = "EXCELLENT"
        elif success_rate >= 75 and overall_test_rate >= 75:
            print("✅ AgentForge validation réussie - Système fonctionnel")
            verdict = "BON"
        elif success_rate >= 50:
            print("⚠️ Validation partielle - Améliorations recommandées")
            verdict = "ACCEPTABLE"
        else:
            print("❌ Validation échouée - Corrections nécessaires")
            verdict = "INSUFFISANT"
        
        print(f"Verdict: {verdict}")
        print(f"{'='*80}")
        
        return success_rate >= 75

def main():
    """Exécute toute la suite de tests AgentForge"""
    print("🎯 AGENTFORGE TEST MASTER")
    print("Suite complète de validation")
    print(f"Racine: {ROOT}")
    print(f"Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    master = TestMaster()
    master.start_time = time.time()
    
    # Définition des suites de tests
    test_suites = [
        {
            "name": "Tests Complets",
            "script": "test_comprehensive.py", 
            "timeout": 300,
            "description": "Tests scénarios complets avec évaluation"
        },
        {
            "name": "Benchmarks Performance",
            "script": "benchmark.py",
            "timeout": 600,
            "description": "Tests performance et métriques détaillées"
        },
        {
            "name": "Tests de Stress",
            "script": "stress_test.py", 
            "timeout": 400,
            "description": "Tests robustesse et edge cases"
        },
        {
            "name": "Tests Interface UI",
            "script": "ui_integration_test.py",
            "timeout": 300,
            "description": "Tests intégration interface Flask"
        }
    ]
    
    # Vérification de la présence des scripts
    scripts_dir = ROOT / "scripts"
    missing_scripts = []
    
    for suite in test_suites:
        script_path = scripts_dir / suite["script"]
        if not script_path.exists():
            missing_scripts.append(suite["script"])
    
    if missing_scripts:
        print(f"❌ Scripts manquants: {', '.join(missing_scripts)}")
        return False
    
    # Exécution des suites
    successful_suites = 0
    
    for suite in test_suites:
        script_path = scripts_dir / suite["script"]
        print(f"\n📝 {suite['description']}")
        
        success = master.run_test_suite(
            suite["name"], 
            script_path, 
            suite["timeout"]
        )
        
        if success:
            successful_suites += 1
            
        # Pause entre les suites
        if suite != test_suites[-1]:  # Pas de pause après la dernière suite
            print("\n⏸️ Pause 2s avant suite suivante...")
            time.sleep(2)
    
    master.end_time = time.time()
    
    # Génération du rapport final
    overall_success = master.generate_consolidated_report()
    
    return overall_success

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 VALIDATION AGENTFORGE RÉUSSIE !")
        sys.exit(0)
    else:
        print("\n⚠️ VALIDATION AGENTFORGE INCOMPLÈTE")
        sys.exit(1)
