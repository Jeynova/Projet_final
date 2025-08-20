from typing import Dict, Any
from pathlib import Path

def run_eval(state: Dict[str, Any]) -> Dict[str, Any]:
    spec = state["spec"]
    proj = Path(state["project_dir"])

    want_entities = spec.get("entities", [])
    ok_models = (proj / "src/models.py").exists()
    
    # Vérifier que les routes et tests existent pour chaque entité
    missing_routes = []
    missing_tests = []
    
    for entity in want_entities:
        entity_name = entity['name'].lower()
        route_file = proj / f"src/routes/{entity_name}.py"
        test_file = proj / f"tests/test_{entity_name}.py"
        
        if not route_file.exists():
            missing_routes.append(entity_name)
        if not test_file.exists():
            missing_tests.append(entity_name)
    
    ok_routes = len(missing_routes) == 0
    ok_tests = len(missing_tests) == 0

    # Score pondéré
    score = 0
    if ok_models:
        score += 0.4  # 40% pour les modèles
    if ok_routes:
        score += 0.4  # 40% pour les routes
    if ok_tests:
        score += 0.2  # 20% pour les tests

    report = {
        "models": ok_models,
        "routes": ok_routes,
        "tests": ok_tests,
        "entities_requested": [e["name"] for e in want_entities],
        "missing_routes": missing_routes,
        "missing_tests": missing_tests,
        "score": round(score, 2),
    }
    state["eval"] = report
    state["logs"].append(f"Eval: score={report['score']}, models={ok_models}, routes={ok_routes}, tests={ok_tests}")
    return state
