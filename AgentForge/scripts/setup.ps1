param([switch]$OpenAI, [switch]$Ollama, [switch]$Agentic)

Write-Host "🚀 Setup AgentForge..." -ForegroundColor Green

# Créer l'environnement virtuel
py -3.10 -m venv .venv
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Échec création venv" -ForegroundColor Red
    exit 1
}

# Activer l'environnement
.\.venv\Scripts\Activate.ps1

# Mise à jour pip
python -m pip install --upgrade pip setuptools wheel

# Installation de base
pip install -r requirements.txt

# Installations optionnelles
if ($OpenAI) { 
    if (Test-Path .\requirements-llm-openai.txt) { 
        Write-Host "📦 Installation OpenAI..." -ForegroundColor Yellow
        pip install -r requirements-llm-openai.txt 
    } 
}
if ($Ollama) { 
    if (Test-Path .\requirements-llm-ollama.txt) { 
        Write-Host "📦 Installation Ollama..." -ForegroundColor Yellow
        pip install -r requirements-llm-ollama.txt 
    } 
}
if ($Agentic) { 
    if (Test-Path .\requirements-agentic.txt) { 
        Write-Host "📦 Installation Agentic (smolagents)..." -ForegroundColor Yellow
        pip install -r requirements-agentic.txt 
    } else {
        Write-Host "⚠️ requirements-agentic.txt non trouvé" -ForegroundColor Yellow
    }
}

deactivate
Write-Host "✅ Setup terminé avec succès !" -ForegroundColor Green
