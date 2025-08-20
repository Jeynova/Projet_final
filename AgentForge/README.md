# 🤖 AgentForge v2.0 - Générateur Multi-Agent IA

> **Système multi-agent IA avec interface Flask et sélection LLM temps réel pour génération automatique de projets complets**

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Pipeline](https://img.shields.io/badge/pipeline-100%25%20réussi-brightgreen.svg)
![LLMs](https://img.shields.io/badge/LLMs-Ollama%20%2B%20OpenAI-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎯 Vision du Projet v2.0

**AgentForge v2.0** révolutionne la génération automatique de projets en combinant **6 agents IA spécialisés**, une **interface web moderne Flask** et un **système de fallback multicouches** garantissant 100% de succès.

### ✨ Nouveautés Majeures v2.0
- 🖥️ **Interface Web Flask** - Sélection LLM en temps réel avec indicateurs statut
- 🤖 **Support Multi-LLM** - Ollama local + OpenAI + Mode déterministe  
- 💾 **Persistance SQLite** - Historique complet projets générés
- 🔄 **Architecture LangGraph** - Orchestration multi-agent professionnelle
- 📊 **Pipeline 100% Réussi** - Fallbacks garantissant toujours une génération

### 💡 Philosophie : Multi-Agent + Fallbacks Intelligents

**L'innovation :**
- **6 agents spécialisés** coordonnés par LangGraph
- **Interface utilisateur moderne** avec choix LLM temps réel
- **Système de fallback robuste** - jamais d'échec de génération
- **Templates professionnels** - Code production-ready automatique

**Notre solution :**
- ✅ **LLM pour le parsing** : Comprendre l'intention utilisateur
- ✅ **Générateur déterministe** : Code structuré et prévisible
- ✅ **Templates Jinja2** : Patterns éprouvés réutilisables
- ✅ **Fallbacks intelligents** : Fonctionnel même sans LLM

## 🏗️ Architecture Multi-Agents

### Pipeline Intelligent
```
Prompt utilisateur → spec_extractor → tech_selector → planner → scaffolder 
                                                                      ↓
   tester ← verifier ← ci_agent ← dockerizer ← security_qa ← codegen ← retrieve_recipes
```

### Agents Spécialisés

| Agent | Rôle | Technologie |
|-------|------|-------------|
| **spec_extractor** | Parse le langage naturel → entités structurées | LLM + Regex fallback |
| **tech_selector** | Recommande stack technique (FastAPI/Flask, PostgreSQL/SQLite) | LLM + RAG snippets |
| **codegen** | Génère modèles SQLAlchemy + routes CRUD + tests | Génération déterministe |
| **eval_agent** | Évalue qualité du code généré | Métriques automatisées |
| **planner** | Sélectionne templates appropriés | Règles heuristiques |
| **scaffolder** | Structure projet + fichiers boilerplate | Templates Jinja2 |

## 🎮 Utilisation

### Interface Web (Recommandée)
```powershell
# Démarrage rapide
.\scripts\run_ui.ps1

# Interface disponible sur http://127.0.0.1:5001
```

### Génération CLI
```powershell
# Exemple : API de gestion de flotte
.\scripts\generate.ps1 -Prompt "API pour gestion de flotte avec users(email unique, password_hash) et vehicles(license_plate unique, make, model, year int)" -Name "fleet-api"

# Via Python
python -m orchestrator.graph --prompt "API simple avec produits" --name "shop-api"
```

### Parsing d'Entités Avancé

AgentForge comprend le langage naturel et le convertit en structures de données :

```
Input: "API avec users(email unique, password_hash) et products(name, price float)"

Output: 
- Entité User : [id:int, email:str unique, password_hash:str]
- Entité Product : [id:int, name:str, price:float]
- Routes CRUD générées automatiquement
- Tests PyTest avec FastAPI TestClient
```

## 🔬 Résultats de Tests

### Pipeline Manuel - Score Parfait ✅

```
🔧 Test Pipeline Manuel
==================================================
1️⃣ spec_extractor... ✅ 2 entités parsées
2️⃣ tech_selector... ✅ Tech: fastapi, postgres  
3️⃣ planner... ✅ Preset: api_fastapi_postgres
4️⃣ scaffolder... ✅ Projet créé: 27 fichiers
5️⃣ codegen... ✅ Modèles + Routes + Tests générés
6️⃣ eval_agent... ✅ Score final: 1.0/1.0

📊 Résumé:
   - Entités parsées: 2 (sans doublons)
   - Fichiers générés: 27
   - Score d'évaluation: 1.0/1.0 (100%)
   - Tous fichiers attendus présents ✅

🎉 Pipeline manuel réussi !
```

### Pipeline LangGraph - Score Parfait ✅

```
🔀 Test LangGraph Simplifié
==================================================
🚀 Lancement LangGraph...
✅ Entités parsées: 2
✅ Projet créé: True  
✅ Score final: 1.0/1.0
✅ Logs: 8 étapes

🏆 MISSION ACCOMPLIE - Pipeline 100% opérationnel !
```

### Tests de Robustesse

- ✅ **Fallback sans LLM** : Génération déterministe fonctionnelle
- ✅ **Parsing complexe** : Entités avec contraintes (unique, types, nullable)
- ✅ **Déduplication intelligente** : Plus de doublons Users/User
- ✅ **Validation automatique** : Score pondéré (modèles 40% + routes 40% + tests 20%)

## 🛠️ Installation et Configuration

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
AGENTFORGE_LLM=mock          # Pas de LLM (fallback déterministe)
AGENTFORGE_LLM=openai        # OpenAI GPT (nécessite OPENAI_API_KEY)
AGENTFORGE_LLM=ollama        # Ollama local
```

## 📁 Structure du Projet

```
AgentForge/
├── core/                    # Parseurs et extracteurs
│   ├── llm_client.py       # Interface LLM unifiée
│   ├── spec_extractor.py   # Parsing langage naturel
│   └── mappings.py         # Synonymes et patterns
├── orchestrator/           # Agents et pipeline
│   ├── agents.py          # Agents principaux 
│   ├── graph.py           # Pipeline LangGraph
│   ├── tech_selector_agent.py    # Recommandation tech
│   ├── codegen_agent.py   # Générateur de code
│   └── eval_agent.py      # Évaluateur qualité
├── apps/ui_flask/         # Interface web
│   ├── app.py            # Serveur Flask
│   ├── models.py         # Modèles DB (projets)
│   └── templates/        # Templates HTML
├── templates/             # Templates de génération
│   └── api_fastapi_postgres/  # Template FastAPI
├── rag_snippets/          # Base de connaissances
└── scripts/               # Scripts PowerShell
```

## 🚀 Fonctionnalités Avancées

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

## 📈 Métriques de Performance

### Taux de Réussite : 100%
- Pipeline manuel : ✅ 1.0/1.0
- Pipeline LangGraph : ✅ 1.0/1.0  
- Génération sans LLM : ✅ Fallback fonctionnel

### Couverture Fonctionnelle
- ✅ Parsing entités complexes
- ✅ Génération modèles SQLAlchemy
- ✅ Routes CRUD FastAPI complètes
- ✅ Tests PyTest automatisés
- ✅ Configuration Docker
- ✅ CI/CD GitHub Actions

## 🎓 Pour l'Oral - Points Clés

### Innovation Technique
1. **Approche Hybride** : LLM pour compréhension + générateur déterministe
2. **Robustesse** : Fonctionnel même sans connexion LLM
3. **Qualité** : Templates éprouvés vs génération aléatoire

### Architecture Scalable  
1. **Multi-agents** : Séparation des responsabilités
2. **Pipeline modulaire** : Agents remplaçables
3. **Extensibilité** : Nouveaux templates facilement ajoutables

### Résultats Mesurables
1. **100% de taux de réussite** sur les tests
2. **27 fichiers générés** automatiquement 
3. **Score parfait** en évaluation automatique

### Valeur Business
1. **Gain de temps** : API complète en quelques secondes
2. **Qualité garantie** : Code structuré et maintenable  
3. **Standardisation** : Patterns cohérents entre projets

## 📝 Licence

MIT - Voir [LICENSE](LICENSE) pour plus de détails.

---

**Créé par [Jeynova](https://github.com/Jeynova)** - *Un générateur intelligent qui allie IA et déterminisme pour créer du code de qualité industrielle*