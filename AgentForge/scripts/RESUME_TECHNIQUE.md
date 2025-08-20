# AgentForge v2.0 - Résumé Technique

## Description
AgentForge v2.0 est un système multi-agent de génération automatique de projets développé en Python. Le système combine l'intelligence artificielle (LLM) avec des algorithmes déterministes pour assurer une génération fiable de projets d'applications web.

## Architecture Technique
- **Orchestration**: LangGraph pour coordination multi-agent  
- **Interface**: Flask avec sélection LLM en temps réel
- **Base de données**: SQLite pour persistance des projets
- **Templates**: Jinja2 pour génération de code structuré
- **LLM Support**: Ollama local et OpenAI API

## Agents Spécialisés
1. **Spec Extractor**: Analyse du langage naturel vers structures de données
2. **Tech Selector**: Recommandations technologiques automatisées
3. **Planner**: Sélection de templates projet appropriés
4. **Scaffolder**: Génération de structure de fichiers
5. **Codegen**: Production de code métier et tests
6. **Eval Agent**: Validation et scoring qualité

## Résultats
- Taux de succès: 100% (fallbacks garantis)
- Templates supportés: FastAPI + PostgreSQL/SQLite
- Code généré: Modèles ORM, routes CRUD, tests unitaires
- Containerisation: Docker et Docker Compose automatiques
- CI/CD: GitHub Actions configuré automatiquement

## Technologies
- Python 3.10+, Flask 3.0, LangGraph 0.2, SQLAlchemy 2.0
- Pydantic 2.8, Ollama, OpenAI API, Jinja2 Templates
- Docker, PostgreSQL, SQLite, Pytest, GitHub Actions

---
Documentation technique professionnelle - AgentForge v2.0
