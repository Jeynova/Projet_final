#!/usr/bin/env python3
"""
Diagnostic LLM AgentForge
Vérifie pourquoi le LLM passe en fallback
"""

import os
import sys
from pathlib import Path

# Add project to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from core.llm_client import LLMClient

def test_llm_detailed():
    """Test détaillé de la connexion LLM avec logs"""
    print("🔍 DIAGNOSTIC LLM DÉTAILLÉ")
    print("=" * 50)
    
    # Test avec configuration Ollama
    os.environ["AGENTFORGE_LLM"] = "ollama"
    os.environ["OLLAMA_MODEL"] = "llama3.1:latest"
    
    client = LLMClient()
    print(f"Provider configuré: {client.provider}")
    
    # Test 1: Connexion basique
    print(f"\n📡 TEST 1: Connexion basique")
    system_prompt = "Réponds en JSON avec {\"status\": \"ok\", \"message\": \"test réussi\"}"
    user_prompt = "Test de connexion"
    
    try:
        print(f"Appel LLM en cours...")
        import time
        start_time = time.time()
        
        result = client.extract_json(system_prompt, user_prompt)
        
        duration = time.time() - start_time
        print(f"⏱️ Durée: {duration:.2f}s")
        
        if result is None:
            print(f"❌ Résultat: None (fallback activé)")
            return False
        else:
            print(f"✅ Résultat: {result}")
            return True
            
    except Exception as e:
        print(f"💥 Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_spec_extraction():
    """Test l'extraction de spec comme dans le vrai pipeline"""
    print(f"\n🧪 TEST 2: Extraction de spécification")
    
    system_prompt = (
        "Tu extrais des spécifications d'un prompt utilisateur. Réponds UNIQUEMENT en JSON valide avec la structure:"
        '{"entities": [{"name": "EntityName", "fields": ["field1", "field2"]}], "tech": {"web": "fastapi", "db": "postgres"}, "features": []}'
    )
    
    user_prompt = "API avec users(email unique, password_hash) et products(name, price float)"
    
    client = LLMClient()
    
    try:
        print(f"Extraction en cours...")
        import time
        start_time = time.time()
        
        result = client.extract_json(system_prompt, user_prompt)
        
        duration = time.time() - start_time
        print(f"⏱️ Durée: {duration:.2f}s")
        
        if result is None:
            print(f"❌ Extraction échouée → Fallback déterministe")
            return False
        else:
            print(f"✅ Extraction réussie:")
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
            
    except Exception as e:
        print(f"💥 Erreur extraction: {e}")
        return False

def test_ollama_direct():
    """Test direct d'Ollama sans passer par LLMClient"""
    print(f"\n🔧 TEST 3: Ollama direct")
    
    try:
        import requests
        import json
        
        # Test API tags
        print("Test /api/tags...")
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            tags_data = response.json()
            models = tags_data.get("models", [])
            print(f"✅ {len(models)} modèles disponibles:")
            for model in models[:3]:
                print(f"  - {model.get('name', 'unknown')}")
        else:
            print(f"❌ /api/tags failed: {response.status_code}")
            return False
        
        # Test génération
        print(f"\nTest génération avec llama3.1:latest...")
        payload = {
            "model": "llama3.1:latest",
            "prompt": "Réponds juste 'Hello' en JSON: {\"message\": \"Hello\"}",
            "format": "json",
            "stream": False,
        }
        
        import time
        start_time = time.time()
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            ollama_response = data.get("response", "")
            print(f"✅ Réponse Ollama ({duration:.2f}s): {ollama_response}")
            
            # Try to parse as JSON
            try:
                json_result = json.loads(ollama_response)
                print(f"✅ JSON valide: {json_result}")
                return True
            except:
                print(f"⚠️ Réponse non-JSON: {ollama_response}")
                return False
        else:
            print(f"❌ Génération failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Erreur Ollama direct: {e}")
        return False

def main():
    print("🔍 DIAGNOSTIC POURQUOI FALLBACK ?")
    print("Vérifie pourquoi Ollama passe en mode déterministe")
    print("=" * 60)
    
    # Tests séquentiels
    test1_ok = test_llm_detailed()
    test2_ok = test_spec_extraction()
    test3_ok = test_ollama_direct()
    
    print(f"\n" + "=" * 60)
    print(f"📊 RÉSULTATS DIAGNOSTIC")
    print(f"=" * 60)
    
    print(f"Test connexion basique: {'✅ OK' if test1_ok else '❌ ÉCHEC'}")
    print(f"Test extraction spec: {'✅ OK' if test2_ok else '❌ ÉCHEC'}")
    print(f"Test Ollama direct: {'✅ OK' if test3_ok else '❌ ÉCHEC'}")
    
    if not any([test1_ok, test2_ok, test3_ok]):
        print(f"\n🚨 DIAGNOSTIC: Ollama complètement inaccessible")
        print(f"   → Vérifiez qu'Ollama tourne")
        print(f"   → Commande: ollama serve")
    elif test3_ok and not test1_ok:
        print(f"\n🔧 DIAGNOSTIC: Problème dans LLMClient")
        print(f"   → Ollama fonctionne mais LLMClient échoue")
        print(f"   → Problème de timeout, parsing JSON ou exception")
    elif test1_ok and not test2_ok:
        print(f"\n📝 DIAGNOSTIC: Problème de prompt complexe")
        print(f"   → Connexion OK mais extraction de spec échoue")
        print(f"   → Le modèle n'arrive pas à respecter le format JSON demandé")
    else:
        print(f"\n✅ DIAGNOSTIC: LLM devrait fonctionner")
        print(f"   → Problème peut-être dans l'interface Flask")
        print(f"   → Ou dans la gestion des variables d'environnement")
    
    print(f"\n💡 POUR FORCER OLLAMA:")
    print(f"   $env:AGENTFORGE_LLM=\"ollama\"")
    print(f"   $env:OLLAMA_MODEL=\"llama3.1:latest\"")
    print(f"   Puis relancer Flask")

if __name__ == "__main__":
    main()
