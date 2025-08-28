param([switch]$OpenAI, [switch]$Ollama, [switch]$Agentic)

Write-Host "🚀 AgentForge Setup Script" -ForegroundColor Green
Write-Host "=========================="

# Create virtual environment
Write-Host "📦 Creating virtual environment..."
py -3.10 -m venv .venv
if (-not $?) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate and upgrade pip
Write-Host "🔧 Activating environment and upgrading pip..."
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel

# Install base requirements
Write-Host "📦 Installing base requirements..."
pip install -r requirements.txt

# Install optional LLM providers
if ($OpenAI) {
    Write-Host "🧠 Installing OpenAI provider..."
    if (Test-Path .\requirements-llm-openai.txt) {
        pip install -r requirements-llm-openai.txt
    }
}

if ($Ollama) {
    Write-Host "🦙 Installing Ollama provider..."
    if (Test-Path .\requirements-llm-ollama.txt) {
        pip install -r requirements-llm-ollama.txt
    }
}

# Install agentic dependencies
if ($Agentic) {
    Write-Host "🤖 Installing agentic dependencies..."
    if (Test-Path .\requirements-agentic.txt) {
        pip install -r requirements-agentic.txt
        Write-Host "✅ Agentic mode enabled! Set AGENTFORGE_AGENTIC=1 in .env" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  requirements-agentic.txt not found" -ForegroundColor Yellow
    }
}

deactivate
Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Activate: .\.venv\Scripts\Activate.ps1"
Write-Host "2. Configure .env file for your LLM provider"
Write-Host "3. Test: python -m orchestrator.graph --prompt 'test' --name 'test'"
