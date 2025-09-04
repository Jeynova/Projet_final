#!/usr/bin/env python3
"""
Test simple du pipeline AgentForge sans LangGraph
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add project to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from orchestrator.agents import spec_extractor, planner, scaffolder, tech_selector, codegen, eval_agent

def test_manual_pipeline():
    """Test du pipeline manuel agent par agent"""
    print("🔧 Test Pipeline Manuel")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # État initial
        state = {
            "prompt": "API pour gestion de flotte avec users(email unique, password_hash) et vehicles(license_plate unique, make, model, year int)",
            "name": "fleet-api",
            "artifacts_dir": tmp_dir,
            "logs": []
        }
        
        try:
            # Agent 1: Extraction de spec
            print("1️⃣ spec_extractor...")
            state = spec_extractor(state)
            entities = state["spec"].get("entities", [])
            print(f"   Entités détectées: {len(entities)}")
            for e in entities:
                print(f"     - {e['name']}: {len(e['fields'])} champs")
            
            # Agent 2: Sélection technique
            print("2️⃣ tech_selector...")
            state = tech_selector(state)
            tech = state.get("tech_selection", {})
            print(f"   Tech stack: {tech.get('web', 'N/A')}, {tech.get('db', 'N/A')}")
            
            # Agent 3: Planification
            print("3️⃣ planner...")
            state = planner(state)
            print(f"   Preset choisi: {state.get('preset', 'N/A')}")
            
            # Agent 4: Scaffolding
            print("4️⃣ scaffolder...")
            state = scaffolder(state)
            project_path = Path(state["project_dir"])
            print(f"   Projet créé: {project_path.exists()}")
            
            # Agent 5: Génération de code
            print("5️⃣ codegen...")
            state = codegen(state)
            
            # Agent 6: Évaluation
            print("6️⃣ eval_agent...")
            state = eval_agent(state)
            eval_result = state.get("eval", {})
            print(f"   Score final: {eval_result.get('score', 0)}")
            
            # Vérification des fichiers
            print("\n📁 Fichiers générés:")
            generated_files = []
            for file in project_path.rglob("*"):
                if file.is_file():
                    rel_path = file.relative_to(project_path)
                    # Normaliser les chemins pour Windows (remplacer \ par /)
                    normalized_path = str(rel_path).replace("\\", "/")
                    generated_files.append(normalized_path)
                    print(f"   - {rel_path}")
            
            # Vérifications spécifiques - adapter aux entités réelles
            entities = state["spec"].get("entities", [])
            expected_files = ["src/models.py"]
            
            # Ajouter les fichiers attendus selon les entités détectées
            for entity in entities:
                entity_name = entity["name"].lower()
                expected_files.extend([
                    f"src/routes/{entity_name}.py",
                    f"tests/test_{entity_name}.py"
                ])
            
            print(f"\n✅ Vérifications:")
            all_present = True
            for expected in expected_files:
                present = expected in generated_files
                status = "✅" if present else "❌"
                print(f"   {status} {expected}")
                if not present:
                    all_present = False
            
            # Vérifier le contenu du modèle
            models_file = project_path / "src" / "models.py"
            if models_file.exists():
                content = models_file.read_text(encoding="utf-8")
                has_user = "class User(" in content or "class Users(" in content
                has_vehicle = "class Vehicle(" in content or "class Vehicles(" in content
                print(f"   {'✅' if has_user else '❌'} Modèle User dans models.py")
                print(f"   {'✅' if has_vehicle else '❌'} Modèle Vehicle dans models.py")
            
            print(f"\n📊 Résumé:")
            print(f"   - Entités parsées: {len(entities)}")
            print(f"   - Fichiers générés: {len(generated_files)}")
            print(f"   - Score d'évaluation: {eval_result.get('score', 0)}")
            print(f"   - Logs: {len(state.get('logs', []))}")
            
            if all_present and eval_result.get('score', 0) > 0.5:
                print("\n🎉 Pipeline manuel réussi !")
                return True
            else:
                print("\n⚠️ Pipeline partiellement réussi")
                return False
                
        except Exception as e:
            print(f"\n❌ Erreur dans le pipeline manuel: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_manual_pipeline()
    sys.exit(0 if success else 1)
