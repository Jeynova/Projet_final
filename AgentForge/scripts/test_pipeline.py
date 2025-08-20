#!/usr/bin/env python3
"""
Script de test pour valider le pipeline AgentForge complet
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add project to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from orchestrator.graph import build_app

def test_entity_parsing():
    """Test du parsing d'entités"""
    from orchestrator.agents import _parse_entities_from_text
    
    # Test 1: Format simple
    text1 = "Je veux gérer des users(email unique, password_hash) et des vehicles(license_plate unique, make, model)"
    entities1 = _parse_entities_from_text(text1)
    print(f"Test 1 - Entités trouvées: {len(entities1)}")
    for e in entities1:
        print(f"  - {e.name}: {[f.name for f in e.fields]}")
    
    # Test 2: Format complexe
    text2 = "API pour fleet management avec conducteurs et véhicules"
    entities2 = _parse_entities_from_text(text2)
    print(f"Test 2 - Entités par défaut: {len(entities2)}")
    for e in entities2:
        print(f"  - {e.name}: {[f.name for f in e.fields]}")

def test_individual_agents():
    """Test des agents individuels"""
    print("\n=== Test Agents Individuels ===")
    
    from orchestrator.agents import spec_extractor, tech_selector, codegen, eval_agent
    
    # Test spec_extractor
    state = {
        "prompt": "API pour gestion avec users(email unique, password_hash)",
        "name": "test-api",
        "logs": []
    }
    
    try:
        # Test spec_extractor
        result = spec_extractor(state)
        print(f"✅ spec_extractor: {len(result.get('spec', {}).get('entities', []))} entités")
        
        # Test tech_selector avec spec
        result = tech_selector(result)
        print(f"✅ tech_selector: {result.get('tech_selection', {}).get('web', 'N/A')}")
        
        # Simuler project_dir pour codegen
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            result["project_dir"] = tmp_dir
            result = codegen(result)
            print(f"✅ codegen: généré")
            
            result = eval_agent(result)
            print(f"✅ eval_agent: score {result.get('eval', {}).get('score', 0)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur agents individuels: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Tests AgentForge")
    print("=" * 50)
    
    # Test parsing entités
    test_entity_parsing()
    
    # Test agents individuels
    success = test_individual_agents()
    
    if success:
        print("\n✅ Tous les tests passent !")
    else:
        print("\n❌ Certains tests échouent")
        sys.exit(1)
