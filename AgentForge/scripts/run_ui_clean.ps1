# Simple UI launcher without hash checking
# Usage: .\scripts\run_ui_clean.ps1

Write-Host "Starting AgentForge UI..." -ForegroundColor Green

# 1) Create and activate venv
if (!(Test-Path .\.venv\Scripts\Activate.ps1)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
Write-Host "Virtual environment activated" -ForegroundColor Cyan

# 2) Upgrade pip
python -m pip install --upgrade pip

# 3) Install requirements
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# 4) Copy env file if needed
if (!(Test-Path .\.env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

# 5) Start Flask
Write-Host "Starting Flask server on http://127.0.0.1:5001" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

$env:FLASK_APP = "apps/ui_flask/app.py"
$env:FLASK_ENV = "development"
python -m flask run --port 5001 --debug
