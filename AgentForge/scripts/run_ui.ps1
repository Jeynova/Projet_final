# Usage:  .\scripts\run_ui.ps1
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
$env:FLASK_APP = "apps/ui_flask/app.py"
$env:FLASK_ENV = "development"
flask run --port 5001