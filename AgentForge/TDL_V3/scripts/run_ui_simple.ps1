# Simple UI launcher for AgentForge
# Usage: .\scripts\run_ui_simple.ps1

Write-Host "🚀 Starting AgentForge UI..." -ForegroundColor Green

# 1) Create venv if needed
if (!(Test-Path .\.venv\Scripts\Activate.ps1)) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# 2) Activate venv and set paths
Write-Host "🔧 Setting up virtual environment..." -ForegroundColor Yellow
if (Test-Path .\.venv\Scripts\python.exe) {
    $pythonPath = ".\\.venv\\Scripts\\python.exe"
} else {
    $pythonPath = "python"
}

# 3) Upgrade pip
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Yellow
& $pythonPath -m pip install --upgrade pip

# 4) Install requirements
Write-Host "📋 Installing dependencies..." -ForegroundColor Yellow
& $pythonPath -m pip install -r requirements.txt

# 5) Copy .env if needed
if (!(Test-Path .\.env)) {
    Write-Host "🔧 Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

# 6) Start Flask server
Write-Host "🌐 Starting Flask server on http://127.0.0.1:5001" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan

$env:FLASK_APP = "apps/ui_flask/app.py"
$env:FLASK_ENV = "development"
& $pythonPath -m flask run --port 5001 --debug
