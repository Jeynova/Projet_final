# Usage: .\scripts\run_ui.ps1 [-OpenAI] [-Ollama]
param([switch]$OpenAI, [switch]$Ollama)

# 1) Venv prêt ?
if (!(Test-Path .\.venv\Scripts\Activate.ps1)) {
  py -3.10 -m venv .venv
}

.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel

# 2) Calcule le hash des fichiers de requirements
$files = @(".\requirements.txt")
if ($OpenAI -and (Test-Path .\requirements-llm-openai.txt)) { $files += ".\requirements-llm-openai.txt" }
if ($Ollama -and (Test-Path .\requirements-llm-ollama.txt)) { $files += ".\requirements-llm-ollama.txt" }

$combined = ""
foreach ($f in $files) { $combined += (Get-FileHash $f -Algorithm SHA256).Hash }
$bytes = [Text.Encoding]::UTF8.GetBytes($combined)
$sha256 = [System.Security.Cryptography.SHA256]::Create()
$hashBytes = $sha256.ComputeHash($bytes)
$curHash = [Convert]::ToHexString($hashBytes)
$sha256.Dispose()

$hashFile = ".\.venv\req.sha256"
$needInstall = $true
if (Test-Path $hashFile) {
  $prevContent = Get-Content $hashFile -ErrorAction SilentlyContinue
  if ($prevContent) {
    $prev = $prevContent.ToString().Trim()
    if ($prev -eq $curHash) { $needInstall = $false }
  }
}

# 3) Installe seulement si nécessaire
if ($needInstall) {
  pip install -r requirements.txt
  if ($OpenAI -and (Test-Path .\requirements-llm-openai.txt)) { pip install -r requirements-llm-openai.txt }
  if ($Ollama -and (Test-Path .\requirements-llm-ollama.txt)) { pip install -r requirements-llm-ollama.txt }
  Set-Content -Path $hashFile -Value $curHash
  Write-Host "Dependencies (re)installed." -ForegroundColor Green
} else {
  Write-Host "Dependencies unchanged - no installation needed." -ForegroundColor Cyan
}

# 4) Lance l'UI
$env:FLASK_APP = "apps/ui_flask/app.py"
$env:FLASK_ENV = "development"
python -m flask run --port 5001 --debug