#!/usr/bin/env python3
"""
Benchmark Performance AgentForge
Mesure temps d'exécution et métriques de performance
"""

import sys
import time
import tempfile
import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project to path  
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from orchestrator.agents import spec_extractor, planner, scaffolder, tech_selector, codegen, eval_agent

class PerformanceBenchmark:
    """Benchmark des performances AgentForge"""
    
    def __init__(self):
        self.runs = []
    
    def benchmark_pipeline(self, prompt: str, iterations: int = 3) -> Dict[str, Any]:
        """Benchmark un pipeline complet sur plusieurs itérations"""
        print(f"\n🏁 BENCHMARK: {iterations} itérations")
        print(f"Prompt: {prompt}")
        print("-" * 60)
        
        run_times = []
        agent_times = {}
        success_count = 0
        
        for i in range(iterations):
            print(f"Run {i+1}/{iterations}...", end=" ", flush=True)
            
            result = self._single_run(prompt)
            run_times.append(result["total_time"])
            
            # Agrégation temps par agent
            for agent, time_val in result["agent_times"].items():
                if agent not in agent_times:
                    agent_times[agent] = []
                agent_times[agent].append(time_val)
            
            if result["success"]:
                success_count += 1
                print("✅")
            else:
                print("❌")
        
        # Calcul statistiques
        stats = {
            "prompt": prompt,
            "iterations": iterations,
            "success_rate": success_count / iterations,
            "total_time": {
                "mean": statistics.mean(run_times),
                "median": statistics.median(run_times),
                "min": min(run_times),
                "max": max(run_times),
                "stdev": statistics.stdev(run_times) if len(run_times) > 1 else 0
            },
            "agent_times": {}
        }
        
        # Stats par agent
        for agent, times in agent_times.items():
            stats["agent_times"][agent] = {
                "mean": statistics.mean(times),
                "min": min(times),
                "max": max(times)
            }
        
        return stats
    
    def _single_run(self, prompt: str) -> Dict[str, Any]:
        """Une exécution complète du pipeline avec mesure de temps"""
        agent_times = {}
        total_start = time.perf_counter()
        
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                state = {
                    "prompt": prompt,
                    "name": "benchmark-test",
                    "artifacts_dir": tmp_dir,
                    "logs": []
                }
                
                # Mesure chaque agent
                agents = [
                    ("spec_extractor", spec_extractor),
                    ("tech_selector", tech_selector), 
                    ("planner", planner),
                    ("scaffolder", scaffolder),
                    ("codegen", codegen),
                    ("eval_agent", eval_agent)
                ]
                
                for agent_name, agent_func in agents:
                    start = time.perf_counter()
                    state = agent_func(state)
                    end = time.perf_counter()
                    agent_times[agent_name] = end - start
                
                total_time = time.perf_counter() - total_start
                score = state.get("eval", {}).get("score", 0)
                
                return {
                    "success": score >= 0.8,
                    "total_time": total_time,
                    "agent_times": agent_times,
                    "score": score,
                    "entities_count": len(state.get("spec", {}).get("entities", [])),
                    "files_count": len(list(Path(state["project_dir"]).rglob("*")))
                }
                
        except Exception as e:
            total_time = time.perf_counter() - total_start
            return {
                "success": False,
                "total_time": total_time,
                "agent_times": agent_times,
                "error": str(e),
                "score": 0,
                "entities_count": 0,
                "files_count": 0
            }

def main():
    print("⚡ BENCHMARK PERFORMANCE AGENTFORGE")
    print("=" * 80)
    
    benchmark = PerformanceBenchmark()
    
    # Scénarios de benchmark
    scenarios = [
        {
            "name": "Simple API",
            "prompt": "API simple avec users et products",
            "iterations": 5
        },
        {
            "name": "Complex Parsing",
            "prompt": "API avec users(email unique, password_hash) et products(name, price float, stock int)",
            "iterations": 5
        },
        {
            "name": "E-commerce Full",
            "prompt": "API e-commerce avec users(email unique, role), products(name, price float, category_id), orders(user_id int, status, total float), reviews(user_id int, product_id int, rating int, comment)",
            "iterations": 3
        }
    ]
    
    all_results = []
    
    for scenario in scenarios:
        print(f"\n📊 SCENARIO: {scenario['name']}")
        print("=" * 60)
        
        result = benchmark.benchmark_pipeline(
            scenario["prompt"], 
            scenario["iterations"]
        )
        result["scenario_name"] = scenario["name"]
        all_results.append(result)
        
        # Affichage résultats
        print(f"\n📈 RÉSULTATS:")
        print(f"   Taux de réussite: {result['success_rate']:.1%}")
        print(f"   Temps moyen: {result['total_time']['mean']:.2f}s")
        print(f"   Temps médian: {result['total_time']['median']:.2f}s")
        print(f"   Écart-type: {result['total_time']['stdev']:.2f}s")
        
        print(f"\n🤖 TEMPS PAR AGENT:")
        for agent, times in result["agent_times"].items():
            print(f"   {agent:15}: {times['mean']:.3f}s (min: {times['min']:.3f}s, max: {times['max']:.3f}s)")
    
    # Rapport global
    print(f"\n{'='*80}")
    print("📊 RAPPORT GLOBAL DE PERFORMANCE")
    print(f"{'='*80}")
    
    # Moyennes globales
    avg_success_rate = statistics.mean([r["success_rate"] for r in all_results])
    avg_total_time = statistics.mean([r["total_time"]["mean"] for r in all_results])
    
    print(f"Taux de réussite moyen: {avg_success_rate:.1%}")
    print(f"Temps d'exécution moyen: {avg_total_time:.2f}s")
    
    # Performance par agent (moyenne sur tous scénarios)
    all_agent_times = {}
    for result in all_results:
        for agent, times in result["agent_times"].items():
            if agent not in all_agent_times:
                all_agent_times[agent] = []
            all_agent_times[agent].append(times["mean"])
    
    print(f"\n⚡ PERFORMANCE MOYENNE PAR AGENT:")
    for agent, times in all_agent_times.items():
        avg_time = statistics.mean(times)
        percentage = (avg_time / avg_total_time) * 100
        print(f"   {agent:15}: {avg_time:.3f}s ({percentage:5.1f}%)")
    
    # Métriques de qualité
    print(f"\n🎯 MÉTRIQUES DE QUALITÉ:")
    for result in all_results:
        print(f"   {result['scenario_name']:15}: {result['success_rate']:.1%} succès")
    
    # Sauvegarde résultats
    benchmark_file = ROOT / "benchmark_results.json"
    with open(benchmark_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "avg_success_rate": avg_success_rate,
                "avg_total_time": avg_total_time,
                "agent_performance": {
                    agent: statistics.mean(times) 
                    for agent, times in all_agent_times.items()
                }
            },
            "scenarios": all_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Benchmark sauvegardé: {benchmark_file}")
    
    # Conclusion
    if avg_success_rate >= 0.9:
        print(f"\n🎉 PERFORMANCE EXCELLENTE ! ({avg_success_rate:.1%} succès)")
    elif avg_success_rate >= 0.8:
        print(f"\n✅ Performance satisfaisante ({avg_success_rate:.1%} succès)")
    else:
        print(f"\n⚠️ Performance à améliorer ({avg_success_rate:.1%} succès)")

if __name__ == "__main__":
    main()
