# AgentForge v2.0 - Générateur Multi-Agent IA

> Système multi-agent de génération automatique de projets avec interface Flask et sélection LLM en temps réel

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Pipeline](https://img.shields.io/badge/pipeline-100%25%20réussi-brightgreen.svg)
![LLMs](https://img.shields.io/badge/LLMs-Ollama%20%2B%20OpenAI-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Vision du Projet v2.0

AgentForge v2.0 implémente une approche hybride pour la génération automatique de projets. Le système combine six agents IA spécialisés, une interface web Flask moderne et un système de fallback multicouches garantissant un taux de succès de 100%.

### Fonctionnalités Principales v2.0
- Interface Web Flask avec sélection LLM en temps réel et indicateurs de statut
- Support multi-LLM : Ollama local, OpenAI et mode déterministe 
- Persistance SQLite avec historique complet des projets générés
- Architecture LangGraph pour l'orchestration multi-agent professionnelle
- Pipeline à fallbacks multiples garantissant la génération dans tous les cas

### Approche Technique : Multi-Agent avec Fallbacks Intelligents

Architecture développée autour de :
- Six agents spécialisés coordonnés par LangGraph
- Interface utilisateur moderne avec sélection LLM en temps réel
- Système de fallback robuste éliminant les échecs de génération
- Templates professionnels pour code prêt pour la production

Stratégie technique :
- LLM pour l'analyse et compréhension des intentions utilisateur
- Générateur déterministe pour code structuré et prévisible
- Templates Jinja2 basés sur des patterns industriels éprouvés
- Fallbacks intelligents la fonctionnalité sans dépendance LLM

## Architecture Multi-Agents

### Pipeline de Traitement
```
Prompt utilisateur → spec_extractor → tech_selector → planner → scaffolder 
 ↓
 tester ← verifier ← ci_agent ← dockerizer ← security_qa ← codegen ← retrieve_recipes
```

### Agents Spécialisés

| Agent | Responsabilité | Technologies |
|-------|----------------|-------------|
| spec_extractor | Analyse du langage naturel vers entités structurées | LLM + analyse regex fallback |
| tech_selector | Recommandations stack technique (FastAPI/Flask, PostgreSQL/SQLite) | LLM + base RAG snippets |
| codegen | Génération modèles SQLAlchemy, routes CRUD et tests | Génération déterministe |
| eval_agent | Évaluation qualité du code généré | Métriques automatisées |
| planner | Sélection des templates appropriés | Règles heuristiques |
| scaffolder | Structure projet et fichiers boilerplate | Templates Jinja2 |

## Utilisation

### Interface Web (Recommandé)
```powershell
# Démarrage du serveur Flask
.\scripts\run_ui.ps1

# Interface accessible sur http://127.0.0.1:5001
```

### Génération en Ligne de Commande
```powershell
# Exemple : API de gestion de flotte
.\scripts\generate.ps1 -Prompt "API pour gestion de flotte avec users(email unique, password_hash) et vehicles(license_plate unique, make, model, year int)" -Name "fleet-api"

# Via Python
python -m orchestrator.graph --prompt "API simple avec produits" --name "shop-api"
```

### Analyse d'Entités Avancée

AgentForge analyse le langage naturel et le convertit en structures de données :

```
Entrée: "API avec users(email unique, password_hash) et products(name, price float)"

Sortie: 
- Entité User : [id:int, email:str unique, password_hash:str]
- Entité Product : [id:int, name:str, price:float]
- Routes CRUD générées automatiquement
- Tests PyTest avec FastAPI TestClient
```

## Résultats de Tests

### Pipeline Manuel - Score Parfait

```
Test Pipeline Manuel
==================================================
1. spec_extractor... Réussi - 2 entités analysées
2. tech_selector... Réussi - Tech: fastapi, postgres 
3. planner... Réussi - Preset: api_fastapi_postgres
4. scaffolder... Réussi - Projet créé: 27 fichiers
5. codegen... Réussi - Modèles + Routes + Tests générés
6⃣ eval_agent... Score final: 1.0/1.0

 Résumé:
 - Entités parsées: 2 (sans doublons)
 - Fichiers générés: 27
 - Score d'évaluation: 1.0/1.0 (100%)
 - Tous fichiers attendus présents Pipeline manuel réussi !
```

### Pipeline LangGraph - Score Parfait ```
🔀 Test LangGraph Simplifié
==================================================
 Lancement LangGraph...
Entités parsées: 2
Projet créé: True 
Score final: 1.0/1.0
Logs: 8 étapes

 MISSION ACCOMPLIE - Pipeline 100% opérationnel !
```

### Tests de Robustesse

- Fallback sans LLM : Génération déterministe fonctionnelle
- Parsing complexe : Entités avec contraintes (unique, types, nullable)
- Déduplication intelligente : Plus de doublons Users/User
- Validation automatique : Score pondéré (modèles 40% + routes 40% + tests 20%)

## Installation et Configuration

### Prérequis
- Windows 11
- Python 3.10+ 
- Git
- Docker (optionnel)

### Installation
```powershell
# Clone du projet
git clone https://github.com/Jeynova/Projet_final.git
cd Projet_final/AgentForge

# Configuration environnement
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configuration LLM (optionnel)
copy .env.example .env
# Éditer .env pour configurer OpenAI API Key si souhaité
```

### Configuration LLM

```bash
# .env
AGENTFORGE_LLM=mock # Pas de LLM (fallback déterministe)
AGENTFORGE_LLM=openai # OpenAI GPT (nécessite OPENAI_API_KEY)
AGENTFORGE_LLM=ollama # Ollama local
```

## Structure du Projet

```
AgentForge/
├── core/ # Parseurs et extracteurs
│ ├── llm_client.py # Interface LLM unifiée
│ ├── spec_extractor.py # Parsing langage naturel
│ └── mappings.py # Synonymes et patterns
├── orchestrator/ # Agents et pipeline
│ ├── agents.py # Agents principaux 
│ ├── graph.py # Pipeline LangGraph
│ ├── tech_selector_agent.py # Recommandation tech
│ ├── codegen_agent.py # Générateur de code
│ └── eval_agent.py # Évaluateur qualité
├── apps/ui_flask/ # Interface web
│ ├── app.py # Serveur Flask
│ ├── models.py # Modèles DB (projets)
│ └── templates/ # Templates HTML
├── templates/ # Templates de génération
│ └── api_fastapi_postgres/ # Template FastAPI
├── rag_snippets/ # Base de connaissances
└── scripts/ # Scripts PowerShell
```

## Fonctionnalités Avancées

### Persistance des Projets
- Base SQLite intégrée
- Historique des générations
- Métadonnées et logs sauvegardés

### Build et Déploiement Docker
- Génération automatique de Dockerfile
- Support docker-compose
- Push vers registres (Docker Hub, GHCR)

### RAG Intégré
- Snippets de bonnes pratiques
- Patterns FastAPI, SQLAlchemy, PyTest
- Recommandations contextuelles

### Tests Automatisés
- Génération de tests PyTest
- Tests d'intégration avec TestClient
- Validation automatique du code

## Métriques de Performance

### Taux de Réussite : 100%
- Pipeline manuel : 1.0/1.0
- Pipeline LangGraph : 1.0/1.0 
- Génération sans LLM : Fallback fonctionnel

### Couverture Fonctionnelle
- Parsing entités complexes
- Génération modèles SQLAlchemy
- Routes CRUD FastAPI complètes
- Tests PyTest automatisés
- Configuration Docker
- CI/CD GitHub Actions

## Pour l'Oral - Points Clés

### Innovation Technique
1. Approche Hybride : LLM pour compréhension + générateur déterministe
2. Robustesse : Fonctionnel même sans connexion LLM
3. Qualité : Templates éprouvés vs génération aléatoire

### Architecture Scalable 
1. Multi-agents : Séparation des responsabilités
2. Pipeline modulaire : Agents remplaçables
3. Extensibilité : Nouveaux templates facilement ajoutables

### Résultats Mesurables
1. 100% de taux de réussite sur les tests
2. 27 fichiers générés automatiquement 
3. Score parfait en évaluation automatique

### Valeur Business
1. Gain de temps : API complète en quelques secondes
2. Qualité garantie : Code structuré et maintenable 
3. Standardisation : Patterns cohérents entre projets

## Licence

MIT - Voir [LICENSE](LICENSE) pour plus de détails.

---

Créé par [Jeynova](https://github.com/Jeynova) - *Un générateur intelligent qui allie IA et déterminisme pour créer du code de qualité industrielle*