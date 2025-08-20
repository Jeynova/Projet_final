# Architecture AgentForge - Explication Composants

> Guide détaillé de chaque composant du système AgentForge

## Structure Globale du Projet

```
AgentForge/
├── 🧠 core/ # Cerveau du système - Parsing et LLM
├── orchestrator/ # Multi-agents et pipeline
├── 🌐 apps/ui_flask/ # Interface utilisateur web
├── templates/ # Templates de génération de code 
├── rag_snippets/ # Base de connaissances
├── scripts/ # Outils et utilitaires
└── tests/ # Tests et validation
```

---

## 🧠 CORE/ - Le Cerveau du Système

### `llm_client.py` - Interface LLM Unifiée
Rôle : Abstraction pour différents providers LLM

```python
class LLMClient:
 def extract_json(self, system_prompt, user_prompt):
 # Gère OpenAI, Ollama, ou mock selon config
 # Parsing robuste des réponses JSON
 # Fallback intelligent si erreur
```

Points clés :
- Support multi-providers (OpenAI, Ollama, Mock)
- Parsing JSON robuste avec validation
- Gestion d'erreurs et timeouts
- Fallback gracieux si LLM indisponible

### `spec_extractor.py` - Parseur de Spécifications 
Rôle : Convertit langage naturel → structure ProjectSpec

```python
class SpecExtractor:
 def extract(self, prompt: str) -> Tuple[ProjectSpec, Dict[str, float]]:
 # 1. Tentative LLM pour parsing avancé
 # 2. Fallback heuristique regex
 # 3. Validation Pydantic
```

Fonctionnalités :
- Détection technologies : "fastapi" → web="fastapi"
- Mapping base de données : "postgres" → db="postgres"
- 🔐 Détection auth : "jwt" → auth="jwt"
- Scores de confiance pour chaque champ

### `specs.py` - Modèles de Données
Rôle : Définit les structures Pydantic

```python
class FieldSpec(BaseModel):
 name: str # Nom du champ
 type: Literal[...] # Type de données 
 pk: bool = False # Clé primaire
 unique: bool = False # Contrainte unique
 nullable: bool = True # Nullable

class EntitySpec(BaseModel):
 name: str # Nom de l'entité
 fields: List[FieldSpec] # Liste des champs

class ProjectSpec(BaseModel):
 name: str # Nom du projet
 entities: List[EntitySpec] = [] # Entités métier
 # ... autres configurations
```

### `mappings.py` - Dictionnaires de Synonymes
Rôle : Maps les termes utilisateur → valeurs standardisées

```python
WEB_SYNONYMS = {
 "fastapi": "fastapi",
 "fast api": "fastapi", 
 "flask": "flask",
 # ...
}

DB_SYNONYMS = {
 "postgres": "postgres",
 "postgresql": "postgres",
 "pg": "postgres",
 # ...
}
```

---

## ORCHESTRATOR/ - Pipeline Multi-Agents

### `graph.py` - Chef d'Orchestre LangGraph
Rôle : Définit et exécute le pipeline multi-agents

```python
def build_app():
 graph = StateGraph(BuildState)
 
 # Ajout des agents
 graph.add_node("spec_extractor", spec_extractor)
 graph.add_node("tech_selector", tech_selector) 
 graph.add_node("codegen", codegen)
 # ...
 
 # Définition du flux
 graph.add_edge("spec_extractor", "planner")
 graph.add_edge("planner", "scaffolder")
 # ...
 
 return graph.compile()
```

Architecture :
- StateGraph : Pipeline avec état partagé
- Flow Control : Transitions conditionnelles
- Logging : Traçabilité complète
- Parallélisation : Agents concurrents possibles

### `agents.py` - Agents Principaux
Rôle : Implémentation des agents de base

#### spec_extractor(state)
```python
def spec_extractor(state):
 # 1. Essai LLM pour parsing avancé
 # 2. Parsing entités: "users(email unique)" → EntitySpec
 # 3. Fallback heuristique robuste
 # 4. Validation et nettoyage
 return state
```

#### planner(state) 
```python
def planner(state):
 # Sélection template selon:
 # - Langage (Python/Node.js)
 # - Framework (FastAPI/Flask)
 # - Base de données (PostgreSQL/SQLite)
 return state
```

#### scaffolder(state)
```python
def scaffolder(state):
 # 1. Résolution template Jinja2
 # 2. Génération structure projet
 # 3. Copie fichiers boilerplate
 # 4. Substitution variables
 return state
```

### `tech_selector_agent.py` - Conseiller Technique
Rôle : Recommande la stack technique optimale

```python
def run_tech_selector(state):
 # 1. Analyse description projet
 # 2. Consultation RAG snippets
 # 3. Recommandations LLM-assistées
 # 4. Fallback heuristique
 
 return {
 "web": "fastapi",
 "db": "postgres", 
 "infra": "docker_compose",
 "confidence": 0.85
 }
```

Innovation : RAG intégré avec snippets techniques

### `codegen_agent.py` - Générateur de Code
Rôle : Génère le code source à partir des entités

```python
def run_codegen(state):
 # 1. Extraction entités du state
 # 2. Génération models.py SQLAlchemy
 # 3. Génération routes CRUD FastAPI
 # 4. Génération tests pytest
 # 5. Auto-registration des routers
 
 return state # avec fichiers écrits
```

Fichiers générés :
- `src/models.py` : Classes SQLAlchemy
- `src/routes/<entity>.py` : Routes CRUD 
- `tests/test_<entity>.py` : Tests automatisés
- `src/routes_auto.py` : Enregistrement automatique

### `eval_agent.py` - Évaluateur de Qualité
Rôle : Valide la qualité du code généré

```python
def run_eval(state):
 score = (
 0.4 * (1 if models_exist else 0) +
 0.4 * (1 if routes_exist else 0) + 
 0.2 * (1 if tests_exist else 0)
 )
 
 return {"score": score, "details": {...}}
```

Métriques :
- Score pondéré (modèles 40% + routes 40% + tests 20%)
- Validation fichiers requis
- Détection fichiers manquants

### `file_ops.py` - Opérations sur Fichiers
Rôle : Modèles Pydantic pour opérations fichiers

```python
class FileOp(BaseModel):
 path: str # Chemin relatif
 action: Literal["write"] # Action (write seulement)
 language: str # Langage (python, yaml, etc.)
 content: str # Contenu du fichier

class FileOps(BaseModel):
 operations: List[FileOp] = []
```

---

## 🌐 APPS/UI_FLASK/ - Interface Utilisateur

### `app.py` - Serveur Flask Principal
Rôle : Interface web pour génération interactive

```python
@app.post("/generate")
def generate():
 # 1. Récupération prompt utilisateur
 # 2. Lancement pipeline AgentForge 
 # 3. Packaging résultats (ZIP)
 # 4. Persistance en base SQLite
 # 5. Retour interface résultats
```

Fonctionnalités :
- Interface web intuitive
- Persistance projets (SQLite)
- 📦 Export ZIP automatique 
- 🐳 Build/Push Docker intégré
- Historique des générations

### `models.py` - Modèles Base de Données
Rôle : Persistance des projets générés

```python
class Project(Base):
 id = Column(Integer, primary_key=True)
 name = Column(String(128))
 prompt = Column(Text) # Prompt original
 project_path = Column(Text) # Chemin sur disque
 zip_path = Column(Text) # Archive ZIP
 created_at = Column(DateTime)

class DockerImage(Base): 
 project_id = Column(Integer)
 image_name = Column(String(256))
 pushed = Column(Boolean)
 # ...
```

### `db.py` - Configuration Base de Données
Rôle : Setup SQLAlchemy + SQLite

```python
engine = create_engine("sqlite:///agentforge.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
```

### `templates/` - Templates HTML
Structure :
- `base.html` : Layout principal
- `index.html` : Page d'accueil + formulaire
- `preview.html` : Prévisualisation spec
- `result.html` : Résultats génération

---

## TEMPLATES/ - Générateurs de Code

### Structure Templates Jinja2
```
templates/api_fastapi_postgres/
├── docker-compose.yml.j2 # Stack complète
├── Dockerfile.j2 # Image Python
├── requirements.txt.j2 # Dépendances
├── src/
│ ├── main.py.j2 # Point d'entrée FastAPI
│ ├── db.py.j2 # Configuration DB
│ └── security.py.j2 # Auth JWT
└── tests/
 └── test_health.py.j2 # Tests de base
```

### Variables de Template
```jinja2
# Dans main.py.j2
from fastapi import FastAPI

app = FastAPI(
 title="{{ name }}",
 description="{{ description }}",
 version="1.0.0"
)

{% if auth == "jwt" %}
from .security import get_current_user
{% endif %}
```

Avantages :
- Structure cohérente garantie
- Configuration dynamique 
- Personnalisation fine
- Patterns industriels éprouvés

---

## RAG_SNIPPETS/ - Base de Connaissances

### Snippets Techniques
- `fastapi_crud.md` : Patterns CRUD FastAPI
- `sqlalchemy_mapping.md` : Mapping types de données
- `pytest_fastapi.md` : Tests avec TestClient
- `docker_healthchecks.md` : Configuration Docker
- `security_headers.md` : Headers de sécurité

### Utilisation RAG
```python
def _load_snippets(repo_root: Path) -> str:
 acc = []
 tags = ["fastapi", "crud", "sqlalchemy", "pytest"]
 for p in (repo_root / "rag_snippets").glob("*.md"):
 txt = p.read_text()
 if any(t in txt for t in tags):
 acc.append(txt)
 return "\n".join(acc)
```

Intégration :
- Sélection contextuelle par tags
- Injection dans prompts LLM
- Recommandations de bonnes pratiques
- Base de connaissances extensible

---

## SCRIPTS/ - Outils et Utilitaires

### `run_ui.ps1` - Lancement Interface
```powershell
# Active environnement virtuel
# Lance serveur Flask sur port 5001
# Gestion d'erreurs et dépendances
```

### `generate.ps1` - Génération CLI 
```powershell
param(
 [string]$Prompt,
 [string]$Name = "generated-app"
)
# Génération via ligne de commande
# Paramètres personnalisables
```

### `test_*.py` - Scripts de Test
- `test_pipeline.py` : Tests agents individuels
- `test_manual_pipeline.py` : Test pipeline complet
- `test_langgraph_simple.py` : Test LangGraph

---

## Flow de Données - Vue d'Ensemble

```
┌─────────────┐
│ Utilisateur │ "API avec users(email unique, password_hash)"
└──────┬──────┘
 │
 ▼
┌─────────────┐
│spec_extract │ → EntitySpec[User(id, email, password_hash)]
└──────┬──────┘
 │ 
 ▼
┌─────────────┐
│tech_selector│ → web=fastapi, db=postgres
└──────┬──────┘
 │
 ▼
┌─────────────┐
│ planner │ → preset=api_fastapi_postgres
└──────┬──────┘
 │
 ▼
┌─────────────┐
│ scaffolder │ → Structure projet + boilerplate
└──────┬──────┘
 │
 ▼ 
┌─────────────┐
│ codegen │ → models.py + routes/user.py + tests/
└──────┬──────┘
 │
 ▼
┌─────────────┐
│ eval_agent │ → Score 1.0/1.0 └──────┬──────┘
 │
 ▼
┌─────────────┐
│ Projet │ FastAPI complet + tests + Docker
│ Complet │
└─────────────┘
```

---

## Points Clés pour Comprendre le Système

### 1. Séparation des Responsabilités
Chaque composant a un rôle précis et limité

### 2. Robustesse par Design 
Fallbacks à chaque étape critique

### 3. Extensibilité
Architecture modulaire pour ajouts futurs

### 4. Qualité Garantie
Templates éprouvés + validation automatique

### 5. Performance
Pipeline optimisé pour génération rapide

---

Ce guide vous donne une compréhension complète de chaque composant d'AgentForge et de leurs interactions !
