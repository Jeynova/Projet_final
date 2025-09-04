# Minimal UI launcher - assumes venv already exists
# Usage: .\scripts\run_ui_minimal.ps1

Write-Host "🚀 Starting AgentForge UI (minimal)..." -ForegroundColor Green

# Use existing venv python directly
$pythonExe = ".\.venv\Scripts\python.exe"

if (!(Test-Path $pythonExe)) {
    Write-Host "❌ Virtual environment not found. Run setup first!" -ForegroundColor Red
    Write-Host "Try: .\scripts\run_ui_simple.ps1" -ForegroundColor Yellow
    exit 1
}

# Copy .env if needed
if (!(Test-Path .\.env)) {
    Write-Host "🔧 Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

# Start server directly
Write-Host "🌐 Starting Flask server on http://127.0.0.1:5001" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan

& $pythonExe apps\ui_flask\app.py
