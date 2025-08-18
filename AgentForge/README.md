# AgentForge (MVP J1)

Windows 11 · Python 3.10 · MIT

## Lancer l'UI
```powershell
# PowerShell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
flask --app apps/ui_flask/app.py run --port 5001 --debug