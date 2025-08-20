# AgentForge v2.0 - Générateur Multi-Agent de Projets

> Système intelligent de génération automatique d'APIs avec architecture multi-agent et fallbacks robustes

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Pipeline](https://img.shields.io/badge/pipeline-100%25%20success-brightgreen.svg)
![LLMs](https://img.shields.io/badge/LLMs-Ollama%20%2B%20OpenAI-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Vue d'ensemble

AgentForge v2.0 est un générateur intelligent qui transforme des descriptions en langage naturel en projets d'API complets et prêts pour la production. Le système utilise une architecture multi-agent sophistiquée avec des fallbacks garantissant un taux de succès de 100%.

### Caractéristiques principales

- Intelligence LLM avancée : Analyse contextuelle avec Ollama (llama3.1) et OpenAI
- Interface Web moderne : Sélection LLM en temps réel avec feedback visuel
- Génération intelligente : Entités automatiquement inférées depuis le langage naturel 
- Architecture LangGraph : Orchestration multi-agent sophistiquée
- Persistance complète : Base SQLite avec historique et métadonnées
- Code production-ready : Templates industriels avec tests automatisés

### Prototypage rapide

Le cœur du système repose sur l'intelligence artificielle :
- Analyse sémantique : Compréhension des intentions métier depuis le langage naturel
- Inférence d'entités : Extraction automatique de modèles de données complexes
- Recommandations contextuelles : Choix technologiques basés sur l'analyse du besoin
- Fallbacks configurables : Mode déterministe disponible en cas de besoin

## Exemple Concret : API de Gestion de Tâches

### Description du besoin
```
"Créer une API pour gérer des tâches avec users(email unique, password_hash, created_at) 
et tasks(title, description, status enum, due_date optional, completed boolean, user_id FK)"
```

### Génération automatique

Étape 1 : Analyse du langage naturel
```python
# AgentForge identifie automatiquement :
entities = [
 User(id=int, email=str(unique=True), password_hash=str, created_at=datetime),
 Task(id=int, title=str, description=str, status=TaskStatus, 
 due_date=datetime(nullable=True), completed=bool, user_id=int(FK))
]
```

Étape 2 : Sélection technique automatique
- Framework: FastAPI (détecté via analyse pattern)
- Base de données: PostgreSQL (recommandé pour production) 
- ORM: SQLAlchemy 2.0 (async)
- Tests: PyTest + FastAPI TestClient

Étape 3 : Génération de code complet

<details>
<summary> Structure générée (27 fichiers)</summary>

```
task-api/
├── src/
│ ├── __init__.py
│ ├── main.py # FastAPI app avec routes
│ ├── db.py # Configuration SQLAlchemy async 
│ ├── security.py # JWT auth + password hashing
│ ├── models/
│ │ ├── __init__.py
│ │ ├── user.py # User SQLAlchemy model
│ │ └── task.py # Task SQLAlchemy model 
│ ├── schemas/
│ │ ├── __init__.py
│ │ ├── user.py # Pydantic schemas
│ │ └── task.py # Pydantic schemas
│ └── routes/
│ ├── __init__.py
│ ├── health.py # Health check endpoint
│ ├── auth.py # Login/register routes
│ ├── users.py # CRUD users
│ └── tasks.py # CRUD tasks + filtering
├── tests/
│ ├── __init__.py
│ ├── conftest.py # PyTest fixtures + test DB
│ ├── test_users.py # Tests CRUD users 
│ ├── test_tasks.py # Tests CRUD tasks
│ └── test_auth.py # Tests authentication
├── docker-compose.yml # PostgreSQL + app services
├── Dockerfile # Multi-stage Python build
├── requirements.txt # Dependencies avec versions
├── .env.example # Variables d'environnement
├── .gitignore # Git ignore patterns
└── README.md # Documentation projet
```
</details>

Code généré - Exemple modèle Task :
```python
# src/models/task.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from src.db import Base
import enum

class TaskStatus(enum.Enum):
 TODO = "todo"
 IN_PROGRESS = "in_progress" 
 COMPLETED = "completed"

class Task(Base):
 __tablename__ = "tasks"
 
 id = Column(Integer, primary_key=True, index=True)
 title = Column(String(255), nullable=False)
 description = Column(Text)
 status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
 due_date = Column(DateTime, nullable=True)
 completed = Column(Boolean, default=False)
 user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
 
 # Relation
 owner = relationship("User", back_populates="tasks")
```

Routes CRUD générées automatiquement :
```python
# src/routes/tasks.py
@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, current_user: User = Depends(get_current_user)):
 # Création avec validation + ownership

@router.get("/", response_model=List[TaskResponse]) 
async def list_tasks(skip: int = 0, limit: int = 100, status: TaskStatus = None):
 # Liste avec pagination + filtrage

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate):
 # Mise à jour avec validation
```

Tests automatisés :
```python
# tests/test_tasks.py
def test_create_task(client, auth_headers):
 response = client.post("/tasks/", json={
 "title": "Test task",
 "description": "Test description" 
 }, headers=auth_headers)
 assert response.status_code == 201
 assert response.json()["title"] == "Test task"
```

### Résultat final

Commande de génération :
```bash
python -m orchestrator.graph --prompt "API tâches avec users et tasks" --name "task-api"
```

## Intelligence LLM en Action

### Analyse Contextuelle Avancée

Input : `"API de gestion de tâches avec users(email unique, password_hash, created_at) et tasks(title, description, status enum, due_date optional, completed boolean, user_id FK)"`

LLM Processing :
```
Ollama llama3.1:latest analyse et identifie :
├── Entité User : email (unique), password_hash, created_at 
├── Entité Task : title, description, status, due_date (nullable), completed, user_id
├── Relation : User 1-to-Many Tasks (foreign key)
├── Types inférés : DateTime, Boolean, Enum
└── Contraintes : Unique, Foreign Key, Nullable
```

Génération Intelligente :
- Modèles SQLAlchemy : Relations correctement définies
- Schémas Pydantic : Validation automatique des types
- Routes FastAPI : CRUD avec filtrage par propriétaire
- Tests PyTest : Scénarios d'usage métier générés

### Pipeline LLM Multi-Agent

```
Prompt utilisateur 
 ↓ [LLM Analysis]
spec_extractor → Entités + Relations + Contraintes
 ↓ [LLM Recommendations] 
tech_selector → Stack technique optimale
 ↓ [Deterministic Generation]
planner → scaffolder → codegen → eval_agent
```

Temps de génération : ~3-5 secondes avec LLM 
Fichiers créés : 27 fichiers complets et cohérents 
Fallback disponible : Mode déterministe configurable
| codegen | Génération modèles SQLAlchemy, routes CRUD et tests | Génération déterministe |
| eval_agent | Évaluation qualité du code généré | Métriques automatisées |

## Utilisation

### Interface Web (Recommandé)
```bash
# Démarrage du serveur Flask
.\scripts\run_ui.ps1

# Interface accessible sur http://127.0.0.1:5001
# - Sélection LLM en temps réel (Ollama/OpenAI/Mock)
# - Génération interactive avec feedback visuel
# - Historique des projets générés
```

### Ligne de Commande
```bash
# Génération rapide
python -m orchestrator.graph --prompt "API de blog avec posts et comments" --name "blog-api"

# Avec sélection LLM spécifique 
python -m orchestrator.graph --prompt "E-commerce avec products et orders" --name "shop-api" --llm ollama

# Script PowerShell
.\scripts\generate.ps1 -Prompt "API CRM avec contacts et companies" -Name "crm-api"
```

### Patterns de Prompt Supportés

Entities simples :
```
"API avec users et products"
→ Génère User et Product avec relations basiques
```

Entities avec contraintes :
``` 
"API avec users(email unique, password_hash) et orders(total float, status enum)"
→ Génère contraintes unique, types spécialisés, enums
```

Relations complexes :
```
"API avec authors, books(author_id FK) et reviews(book_id FK, rating int)" 
→ Génère relations One-to-Many avec clés étrangères
```

## Démonstration LLM

### Exemple de Session LLM Complète

Prompt utilisateur : `"API blog avec posts et comments"`

Trace d'exécution LLM :
```
Démarrage Pipeline LangGraph avec Ollama
├── spec_extractor: Analyse du prompt par llama3.1:latest
│ ├── Détection entités: Post, Comment 
│ ├── Inférence relations: Post 1-to-Many Comments
│ └── Types générés: title:str, content:text, created_at:datetime
├── tech_selector: Recommandations LLM
│ ├── Framework: FastAPI (détecté pattern API REST)
│ ├── Database: PostgreSQL (relation complexe détectée)
│ └── ORM: SQLAlchemy async (modern stack)
├── planner: Template api_fastapi_postgres sélectionné
├── scaffolder: 27 fichiers générés
├── codegen: Code métier généré avec relations
└── eval_agent: Score 1.0/1.0 - Validation complète
```

Résultat : API complète en 4.2 secondes avec modèles, routes CRUD, tests et Docker

### Avantages de l'Approche LLM

Intelligence contextuelle :
- Détection automatique des patterns métier
- Inférence des relations entre entités 
- Recommandations stack adaptées au contexte
- Génération de noms d'endpoints cohérents

Flexibilité :
- Support de prompts en langage naturel libre
- Adaptation aux conventions de nommage 
- Gestion des cas d'usage complexes
- Extensibilité via base RAG intégrée

Fiabilité :
- Fallback déterministe configurable si LLM indisponible
- Validation systématique des sorties LLM
- Logging complet pour debugging et monitoring

## Installation et Configuration

### Prérequis système
- OS : Windows 10/11, macOS, ou Linux
- Python : 3.10 ou supérieur
- Git : Pour cloner le repository
- Docker : Optionnel, pour les projets générés

### Installation rapide

```bash
# 1. Cloner le projet
git clone https://github.com/Jeynova/Projet_final.git
cd Projet_final/AgentForge

# 2. Environnement virtuel
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux 
source .venv/bin/activate

# 3. Installation des dépendances
pip install -r requirements.txt

# 4. Configuration (optionnel)
copy .env.example .env # Windows
cp .env.example .env # macOS/Linux
```

### Configuration LLM

Option 1 : Ollama local (recommandé)
```bash
# Installation Ollama
curl -fsSL https://ollama.ai/install.sh | sh # Linux/macOS
# Ou télécharger depuis https://ollama.ai pour Windows

# Téléchargement du modèle
ollama pull llama3.1:latest

# Configuration AgentForge 
# .env
AGENTFORGE_LLM=ollama
```

Option 2 : OpenAI API
```bash
# .env 
AGENTFORGE_LLM=openai
OPENAI_API_KEY=sk-your-api-key-here
```

Option 3 : Mode déterministe (fallback)
```bash
# .env
AGENTFORGE_LLM=mock
# Génération sans LLM - patterns prédéfinis
```

### Démarrage

```bash
# Interface web (recommandé)
.\scripts\run_ui.ps1 # Windows
./scripts/run_ui.sh # macOS/Linux

# Test rapide en ligne de commande
python -m orchestrator.graph --prompt "API simple avec users" --name "test-api"
```

## Structure du Projet

```
AgentForge/
├── core/ # Moteur de parsing et LLM
│ ├── llm_client.py # Interface unifiée LLM (Ollama/OpenAI)
│ ├── spec_extractor.py # Parsing langage naturel → entités
│ ├── specs.py # Classes de données (Entity, Field)
│ └── mappings.py # Synonymes et patterns de reconnaissance
├── orchestrator/ # Agents et orchestration 
│ ├── agents.py # Agent principal avec LangGraph
│ ├── graph.py # Pipeline et workflow
│ ├── project_spec.py # Specifications des projets
│ └── utils.py # Utilitaires communs
├── apps/ # Interface utilisateur
│ └── ui_flask/ # Interface web Flask
│ ├── app.py # Serveur Flask + routes
│ ├── models.py # Modèles DB (projets générés)
│ ├── templates/ # Templates HTML/Jinja2
│ └── static/ # CSS, JS, assets
├── templates/ # Templates de génération
│ └── api_fastapi_postgres/ # Template FastAPI complet
│ ├── src/ # Code source généré
│ ├── tests/ # Tests automatisés
│ ├── docker-compose.yml.j2
│ └── Dockerfile.j2
├── rag_snippets/ # Base de connaissances 
│ ├── fastapi_patterns.md # Bonnes pratiques FastAPI
│ ├── sqlalchemy_mapping.md # Patterns SQLAlchemy
│ └── testing_patterns.md # Patterns de tests
└── scripts/ # Scripts d'automatisation
 ├── generate.ps1 # Génération PowerShell
 ├── run_ui.ps1 # Démarrage interface
 └── professionalize_docs.py # Outils maintenance
```

## Fonctionnalités Avancées

### Persistance intelligente
- Base SQLite intégrée : Stockage de tous les projets générés
- Historique complet : Prompt original, entités extraites, métadonnées
- Recherche et réutilisation : Interface web pour parcourir les anciens projets
- Export/Import : Sauvegarde et restauration des projets

### Conteneurisation automatique
```yaml
# docker-compose.yml généré automatiquement
version: '3.8'
services:
 api:
 build: .
 ports: ["8000:8000"]
 environment:
 - DATABASE_URL=postgresql://user:pass@db:5432/dbname
 depends_on: [db]
 
 db:
 image: postgres:15
 environment:
 POSTGRES_DB: your_api_db
 POSTGRES_USER: user
 POSTGRES_PASSWORD: password
```

### RAG et recommendations
- Snippets contextuels : Patterns FastAPI, SQLAlchemy, PyTest intégrés
- Recommendations tech : Choix automatique basé sur les besoins détectés
- Bonnes pratiques : Code généré selon les standards industriels
- Optimisations : Index de DB, validation Pydantic, gestion d'erreurs

### Tests complets automatisés
```python
# Exemple de test généré automatiquement
@pytest.fixture
def test_client():
 with TestClient(app) as client:
 yield client

def test_create_user(test_client):
 response = test_client.post("/users/", json={
 "email": "test@example.com",
 "password": "testpass123"
 })
 assert response.status_code == 201
 assert "id" in response.json()
```

## Technologies et Stack

### Core Framework
- Python 3.10+ : Langage principal avec support async/await
- LangGraph 0.2 : Orchestration multi-agent et workflow management
- SQLAlchemy 2.0 : ORM moderne avec support async 
- Pydantic 2.8 : Validation de données et sérialisation
- FastAPI : Framework web moderne pour APIs générées
- Flask 3.0 : Interface utilisateur et dashboard

### Intelligence Artificielle 
- Ollama : LLM local avec support llama3.1:latest
- OpenAI API : Integration GPT-3.5/GPT-4 pour analyse complexe
- Fallback heuristique : Parsing déterministe sans dépendance LLM
- RAG intégré : Base de connaissances avec snippets techniques

### Infrastructure et Déploiement
- Docker : Conteneurisation automatique des projets générés 
- PostgreSQL/SQLite : Support multi-base selon les besoins
- Jinja2 : Templates de génération de code
- PyTest : Framework de tests avec fixtures avancées

## Cas d'Usage

### Développement d'entreprise
```
Input: "API RH avec employees(name, email unique, department, salary float, hire_date) et departments(name unique, budget float)"

Output: 
- API complète avec authentification JWT
- Modèles avec relations et contraintes 
- Tests unitaires et d'intégration
- Documentation OpenAPI automatique
- Configuration Docker production-ready
```

### Prototypage rapide
```
Input: "Blog API avec posts et comments"

Output en ~3 secondes:
- Structure FastAPI complète
- CRUD pour chaque entité 
- Base de données SQLite
- Interface Swagger générée
- Tests PyTest fonctionnels
```

### Projets étudiants/apprentissage
```
Input: "API e-commerce avec products, orders, customers"

Output pédagogique:
- Code commenté et structuré
- Patterns industriels appliqués
- Tests comme documentation vivante 
- Containerisation pour démo
- README détaillé
```

## Contributions et Développement

### Architecture extensible

Le système est conçu pour une extension facile :

```python
# Ajout d'un nouveau template
templates/
└── api_django_mysql/ # Nouveau template Django
 ├── manage.py.j2 # Template Django
 ├── models.py.j2 # Models Django ORM
 └── views.py.j2 # ViewSets DRF
```

### Ajout d'agents spécialisés
```python 
# orchestrator/new_agent.py
class SecurityAgent:
 def analyze_security_requirements(self, entities):
 # Analyse automatique des besoins sécurité
 return security_recommendations
```

### Tests et qualité
```bash
# Tests unitaires
pytest tests/

# Tests d'intégration 
pytest tests/integration/

# Coverage
pytest --cov=orchestrator --cov=core

# Linting
flake8 orchestrator/ core/
black orchestrator/ core/
```

## Roadmap et Évolutions

### Version 2.1 (Planifiée)
- [ ] Support templates React/Vue.js frontend 
- [ ] Integration CI/CD automatique (GitHub Actions)
- [ ] Support Kubernetes manifests
- [ ] Monitoring et observabilité intégrés

### Version 2.2 (Futures)
- [ ] Support multi-tenant avec isolation 
- [ ] Templates microservices avec service mesh
- [ ] Integration avec cloud providers (AWS/GCP/Azure)
- [ ] Analytics et métriques d'usage avancées

## License et Support

Ce projet est publié sous licence MIT. Voir [LICENSE](LICENSE) pour les détails complets.

### Support communautaire
- Issues GitHub : Bug reports et feature requests
- Documentation : Wiki avec guides détaillés 
- Discussions : Q&A et partage d'expériences

---

AgentForge v2.0 - *Générateur intelligent combinant IA et déterminisme pour du code de qualité industrielle*

Développé par [Jeynova](https://github.com/Jeynova) | [Documentation complète](docs/) | [Exemples](examples/)