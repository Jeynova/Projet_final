#!/usr/bin/env python3
"""
Configuration et Test LLM pour AgentForge
Permet de configurer et tester différents providers LLM
"""

import os
import sys
from pathlib import Path

# Add project to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from core.llm_client import LLMClient

def test_llm_connection():
    """Test la connexion LLM actuelle"""
    print("🧪 TEST CONNEXION LLM")
    print("=" * 50)
    
    client = LLMClient()
    provider = os.getenv("AGENTFORGE_LLM", "mock")
    
    print(f"Provider actuel: {provider}")
    
    # Test simple
    system_prompt = "Tu es un assistant qui répond en JSON. Réponds avec la structure: {\"status\": \"ok\", \"message\": \"connexion réussie\"}"
    user_prompt = "Test de connexion"
    
    print(f"\n🔄 Test avec prompt simple...")
    try:
        result = client.extract_json(system_prompt, user_prompt)
        
        if result is None:
            if provider == "mock":
                print("✅ Mode MOCK actif - Fallback déterministe")
                print("   → Génération rapide et fiable sans LLM")
                return "mock"
            else:
                print("❌ Échec connexion LLM")
                print("   → Fallback vers génération déterministe")
                return "failed"
        else:
            print("✅ Connexion LLM réussie !")
            print(f"   → Réponse: {result}")
            return "connected"
            
    except Exception as e:
        print(f"💥 Erreur: {e}")
        return "error"

def configure_openai():
    """Configure OpenAI"""
    print("\n🔧 CONFIGURATION OPENAI")
    print("=" * 30)
    
    api_key = input("Entrez votre clé API OpenAI (ou Enter pour passer): ").strip()
    
    if not api_key:
        print("⏭️ Configuration OpenAI sautée")
        return False
    
    # Vérifier le format de la clé
    if not api_key.startswith('sk-'):
        print("⚠️ Format de clé invalide (doit commencer par 'sk-')")
        return False
    
    # Configuration
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["AGENTFORGE_LLM"] = "openai"
    os.environ["OPENAI_MODEL"] = "gpt-4o-mini"  # Modèle économique
    
    print("✅ Configuration OpenAI appliquée")
    print(f"   Model: {os.environ['OPENAI_MODEL']}")
    return True

def configure_ollama():
    """Configure Ollama (local)"""
    print("\n🔧 CONFIGURATION OLLAMA")
    print("=" * 30)
    
    base_url = input("URL Ollama [http://localhost:11434]: ").strip()
    if not base_url:
        base_url = "http://localhost:11434"
    
    model = input("Modèle [llama3.1:latest]: ").strip()  
    if not model:
        model = "llama3.1:latest"
    
    # Test de connexion
    try:
        import requests
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama détecté")
            
            os.environ["AGENTFORGE_LLM"] = "ollama"
            os.environ["OLLAMA_BASE_URL"] = base_url
            os.environ["OLLAMA_MODEL"] = model
            
            print(f"   URL: {base_url}")
            print(f"   Model: {model}")
            return True
        else:
            print("❌ Ollama non accessible")
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion Ollama: {e}")
        return False

def benchmark_with_llm():
    """Benchmark avec LLM connecté"""
    print("\n⚡ BENCHMARK AVEC LLM")
    print("=" * 30)
    
    import time
    import tempfile
    from orchestrator.agents import spec_extractor, tech_selector, planner, scaffolder, codegen, eval_agent
    
    prompt = "API simple avec users(email unique, password_hash) et products(name, price float)"
    
    print(f"Prompt: {prompt}")
    print("\n🏁 Exécution pipeline complet...")
    
    start_time = time.time()
    
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            state = {
                "prompt": prompt,
                "name": "llm-test", 
                "artifacts_dir": tmp_dir,
                "logs": []
            }
            
            # Pipeline avec mesures
            agent_times = {}
            
            t0 = time.time()
            state = spec_extractor(state)
            agent_times["spec_extractor"] = time.time() - t0
            
            t0 = time.time()
            state = tech_selector(state)
            agent_times["tech_selector"] = time.time() - t0
            
            t0 = time.time()
            state = planner(state)
            agent_times["planner"] = time.time() - t0
            
            t0 = time.time()
            state = scaffolder(state)
            agent_times["scaffolder"] = time.time() - t0
            
            t0 = time.time()
            state = codegen(state)
            agent_times["codegen"] = time.time() - t0
            
            t0 = time.time()
            state = eval_agent(state)
            agent_times["eval_agent"] = time.time() - t0
            
            total_time = time.time() - start_time
            
            # Résultats
            entities = state["spec"].get("entities", [])
            score = state["eval"].get("score", 0)
            
            print(f"\n📊 RÉSULTATS:")
            print(f"   Temps total: {total_time:.3f}s")
            print(f"   Entités détectées: {len(entities)}")
            print(f"   Score final: {score}")
            
            print(f"\n🤖 TEMPS PAR AGENT:")
            for agent, t in agent_times.items():
                pct = (t / total_time) * 100 if total_time > 0 else 0
                print(f"   {agent:15}: {t:.3f}s ({pct:4.1f}%)")
            
            return total_time, score
            
    except Exception as e:
        print(f"💥 Erreur benchmark: {e}")
        return None, None

def main():
    """Menu principal de configuration LLM"""
    print("🤖 AGENTFORGE - CONFIGURATION LLM")
    print("=" * 50)
    
    # Test connexion actuelle
    current_status = test_llm_connection()
    
    if current_status == "mock":
        print(f"\n💡 ÉTAT ACTUEL:")
        print(f"   Mode: Fallback déterministe (très rapide)")
        print(f"   Avantages: 0.03s, 100% fiable, pas de coût")
        print(f"   Limitation: Pas d'intelligence LLM")
    
    print(f"\n🎯 OPTIONS:")
    print(f"1. Garder le mode actuel (fallback déterministe)")
    print(f"2. Configurer OpenAI (intelligent mais coût)")
    print(f"3. Configurer Ollama (local, gratuit)")
    print(f"4. Benchmark avec configuration actuelle")
    print(f"5. Reset vers mode mock")
    
    choice = input(f"\nChoisissez (1-5) [défaut: 1]: ").strip()
    
    if not choice or choice == "1":
        print(f"\n✅ Mode actuel conservé")
        if current_status == "mock":
            print(f"   → Système ultra-rapide et fiable pour présentation")
    
    elif choice == "2":
        if configure_openai():
            print(f"\n🔄 Test de la nouvelle configuration...")
            new_status = test_llm_connection()
            if new_status == "connected":
                print(f"🎉 OpenAI configuré avec succès !")
                
                # Proposition de benchmark
                test_bench = input(f"\nTester les performances ? (y/n): ").lower()
                if test_bench == 'y':
                    benchmark_with_llm()
            else:
                print(f"❌ Configuration échouée, retour au mode mock")
                os.environ["AGENTFORGE_LLM"] = "mock"
    
    elif choice == "3":
        if configure_ollama():
            print(f"\n🔄 Test de la nouvelle configuration...")
            new_status = test_llm_connection()
            if new_status == "connected":
                print(f"🎉 Ollama configuré avec succès !")
                
                # Proposition de benchmark
                test_bench = input(f"\nTester les performances ? (y/n): ").lower()
                if test_bench == 'y':
                    benchmark_with_llm()
            else:
                print(f"❌ Configuration échouée, retour au mode mock")
                os.environ["AGENTFORGE_LLM"] = "mock"
    
    elif choice == "4":
        print(f"\n⚡ Benchmark avec configuration actuelle...")
        time_taken, score = benchmark_with_llm()
        
        if time_taken and current_status == "mock":
            print(f"\n📈 COMPARAISON:")
            print(f"   Mode actuel (mock): {time_taken:.3f}s")
            print(f"   Mode avec LLM: ~2-10s (estimation)")
            print(f"   Différence: ~{10/time_taken:.0f}x plus lent avec LLM")
    
    elif choice == "5":
        os.environ["AGENTFORGE_LLM"] = "mock"
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        print(f"✅ Reset vers mode mock effectué")
    
    else:
        print(f"❌ Choix invalide")
    
    print(f"\n🎯 RECOMMANDATION POUR L'ORAL:")
    if current_status == "mock":
        print(f"   ✅ Mode actuel parfait pour démonstration")
        print(f"   → Rapide, fiable, sans dépendance externe")
        print(f"   → Montre l'approche 'Light AI' hybride")
    else:
        print(f"   → LLM connecté = plus intelligent mais plus lent")
        print(f"   → Idéal pour montrer les 2 modes de fonctionnement")

if __name__ == "__main__":
    main()
