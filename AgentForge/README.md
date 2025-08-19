# AgentForge (MVP J1)

Windows 11 · Python 3.10 · MIT

## Configuration

1. Copiez le fichier de configuration :
```powershell
copy .env.example .env
```

2. Éditez `.env` pour configurer votre provider LLM :
- `AGENTFORGE_LLM=mock` (par défaut, pas de LLM)
- `AGENTFORGE_LLM=openai` (avec votre clé API OpenAI)
- `AGENTFORGE_LLM=ollama` (avec Ollama local)

## Lancer l'UI
```powershell
# Via script PowerShell (recommandé)
.\scripts\run_ui.ps1

# Ou manuellement
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app apps/ui_flask/app.py run --port 5001 --debug
```

## Génération CLI
```powershell
# Générer un projet via ligne de commande
.\scripts\generate.ps1 -Prompt "API FastAPI pour gestion de flotte avec JWT" -Name "fleet-api"

# Ou manuellement
python -m orchestrator.graph --prompt "API FastAPI simple" --name "test-api"
```

## Templates Disponibles
- `api_fastapi_postgres` : API FastAPI + PostgreSQL + Docker
- `api_flask_sqlite` : API Flask + SQLite + Docker

## Architecture

### Modules
- `core/` : Extraction de spécifications (LLM + heuristique)
- `orchestrator/` : Pipeline d'agents LangGraph 
- `apps/ui_flask/` : Interface web Flask
- `templates/` : Templates Jinja2 pour génération de code
- `scripts/` : Scripts PowerShell pour Windows

### Pipeline d'Agents
1. **spec_extractor** : Convertit prompt → ProjectSpec
2. **planner** : Sélectionne le template approprié
3. **scaffolder** : Génère la structure de fichiers
4. **security_qa** : Ajoute outils de sécurité
5. **dockerizer** : Configure Docker
6. **ci_agent** : Ajoute CI/CD GitHub Actions
7. **tester** : Lance les tests
8. **verifier** : Valide le résultat final