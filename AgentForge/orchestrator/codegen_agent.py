import json, re
from typing import Dict, Any, List
from pathlib import Path
from pydantic import BaseModel
from .file_ops import FileOps
from .project_spec import ProjectSpec
from .llm_client import LLMClient

SYSTEM = (
  "Tu génères du code pour compléter un boilerplate Python 3.10.\n"
  "Framework: FastAPI + SQLAlchemy + pytest.\n"
  "Règles:\n"
  "- Réponds STRICTEMENT en JSON (schema: {operations:[{path,action,language,content}]}).\n"
  "- Chaque entité a un fichier 'src/routes/<entity>.py' et expose 'router = APIRouter()'.\n"
  "- Crée 'src/models.py' (SQLAlchemy Declarative Base) avec les entités.\n"
  "- Crée 'tests/test_<entity>.py' (TestClient) pour GET liste et création simple.\n"
  "- N'écris que sous 'src/' et 'tests/'.\n"
)

def _snippet_context(repo_root: Path) -> str:
    acc = []
    tags = ["fastapi","crud","sqlalchemy","pytest"]
    for p in (repo_root / "rag_snippets").glob("*.md"):
        txt = p.read_text(encoding="utf-8")
        if any(t in txt for t in tags):
            acc.append(f"\n--- {p.name} ---\n{txt}\n")
        if len(acc) >= 6:
            break
    return "\n".join(acc)

def _build_user_prompt(spec: ProjectSpec) -> str:
    return f"""
Spec:
{json.dumps(spec.dict(), indent=2, ensure_ascii=False)}

TÂCHES:
1) Si 'entities' est vide -> renvoie {{"operations":[]}}.
2) Sinon:
   - Génère src/models.py avec les classes SQLAlchemy selon 'entities'.
   - Pour chaque entité E, routes CRUD 'src/routes/<e>.py' avec 'router = APIRouter()' et endpoints /<e>s.
   - Génère tests/test_<e>.py (FastAPI TestClient) avec un test de lecture et un test de création JSON minimal.

CONTRAINTES:
- Types autorisés: int, str, float, bool, datetime -> mappe vers SQLAlchemy.
- Laisse l'auth/jwt de côté pour le MVP.
- Retourne uniquement du JSON valide.
""".strip()

def run_codegen(state: Dict[str, Any]) -> Dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    spec = ProjectSpec(**state["spec"])
    if not spec.dict().get("entities"):
        state["logs"].append("Codegen: aucune entité, rien à générer.")
        return state

    llm = LLMClient()
    prompt = _build_user_prompt(spec) + "\n\nSnippets:\n" + _snippet_context(repo_root)
    data = llm.extract_json(SYSTEM, prompt) or {"operations": []}

    # Debug: afficher la réponse LLM
    state["logs"].append(f"Codegen: LLM response keys: {list(data.keys())}")

    # Valider souplement, puis appliquer avec whitelist
    try:
        ops = FileOps(**data)
    except Exception as e:
        state["logs"].append(f"Codegen: Erreur validation FileOps: {e}")
        ops = FileOps(operations=[])

    project_dir = Path(state["project_dir"])
    written: List[str] = []
    
    # Si pas d'opérations LLM, générer du code fallback
    if not ops.operations:
        state["logs"].append("Codegen: Pas d'opérations LLM, génération fallback...")
        ops.operations = _generate_fallback_operations(spec)

    for op in ops.operations:
        if not (op.path.startswith("src/") or op.path.startswith("tests/")):
            continue
        dst = project_dir / op.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(op.content, encoding="utf-8")
        written.append(op.path)

    state["logs"].append(f"Codegen: fichiers écrits ({len(written)}) -> {written}")

    # Bonus: génère automatiquement src/routes_auto.py pour inclure les routers si des routes existent
    route_files = [p for p in written if p.startswith("src/routes/") and p.endswith(".py")]
    if route_files:
        lines = ["from fastapi import FastAPI"]
        for rf in route_files:
            mod = rf.replace("src/", "").replace(".py", "").replace("/", ".")
            var = mod.split(".")[-1]
            lines.append(f"from .{mod.split('.',1)[1]} import router as {var}_router")
        lines.append("\n\ndef register_auto_routes(app: FastAPI):")
        for rf in route_files:
            var = rf.split("/")[-1].replace(".py","")
            lines.append(f"    app.include_router({var}_router, prefix=\"\")")
        (project_dir / "src/routes_auto.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
        state["logs"].append("Codegen: routes_auto.py généré (registre des routers).")

    return state

def _generate_fallback_operations(spec: ProjectSpec) -> List:
    """Génère du code basique en fallback si LLM indisponible"""
    from .file_ops import FileOp
    
    operations = []
    entities = spec.dict().get("entities", [])
    
    if not entities:
        return operations
    
    # Génère src/models.py
    models_content = _generate_models_content(entities)
    operations.append(FileOp(
        path="src/models.py",
        action="write",
        language="python",
        content=models_content
    ))
    
    # Génère routes et tests pour chaque entité
    for entity in entities:
        name = entity["name"].lower()
        
        # Route CRUD
        route_content = _generate_route_content(entity)
        operations.append(FileOp(
            path=f"src/routes/{name}.py",
            action="write", 
            language="python",
            content=route_content
        ))
        
        # Tests
        test_content = _generate_test_content(entity)
        operations.append(FileOp(
            path=f"tests/test_{name}.py",
            action="write",
            language="python", 
            content=test_content
        ))
    
    return operations

def _generate_models_content(entities) -> str:
    """Génère le contenu de src/models.py"""
    lines = [
        "from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime",
        "from sqlalchemy.ext.declarative import declarative_base", 
        "from sqlalchemy.sql import func",
        "",
        "Base = declarative_base()",
        ""
    ]
    
    for entity in entities:
        class_name = entity["name"]
        table_name = entity["name"].lower() + "s"
        
        lines.append(f"class {class_name}(Base):")
        lines.append(f'    __tablename__ = "{table_name}"')
        lines.append("")
        
        for field in entity["fields"]:
            col_type = _map_field_type(field["type"])
            constraints = []
            if field.get("pk"):
                constraints.append("primary_key=True")
            if field.get("unique"):
                constraints.append("unique=True")
            if not field.get("nullable", True):
                constraints.append("nullable=False")
                
            constraint_str = ", " + ", ".join(constraints) if constraints else ""
            lines.append(f'    {field["name"]} = Column({col_type}{constraint_str})')
        
        lines.append("")
    
    return "\n".join(lines)

def _generate_route_content(entity) -> str:
    """Génère le contenu d'une route CRUD"""
    name = entity["name"].lower()
    class_name = entity["name"]
    
    return f'''from fastapi import APIRouter, HTTPException
from typing import List
from ..models import {class_name}

router = APIRouter()

@router.get("/{name}s", response_model=List[dict])
async def get_{name}s():
    """Récupère tous les {name}s"""
    # TODO: Implémentation avec base de données
    return []

@router.post("/{name}s", response_model=dict)
async def create_{name}(data: dict):
    """Crée un nouveau {name}"""
    # TODO: Implémentation avec base de données
    return {{"id": 1, **data}}

@router.get("/{name}s/{{item_id}}")
async def get_{name}(item_id: int):
    """Récupère un {name} par ID"""
    # TODO: Implémentation avec base de données
    return {{"id": item_id}}
'''

def _generate_test_content(entity) -> str:
    """Génère le contenu d'un fichier de test"""
    name = entity["name"].lower()
    
    return f'''from fastapi.testclient import TestClient
from ..src.main import app

client = TestClient(app)

def test_get_{name}s():
    """Test récupération liste {name}s"""
    response = client.get("/{name}s")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_{name}():
    """Test création {name}"""
    test_data = {{"name": "test"}}
    response = client.post("/{name}s", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
'''

def _map_field_type(field_type: str) -> str:
    """Map field type to SQLAlchemy type"""
    mapping = {
        "int": "Integer",
        "str": "String(255)",
        "float": "Float", 
        "bool": "Boolean",
        "datetime": "DateTime(timezone=True)"
    }
    return mapping.get(field_type, "String(255)")
