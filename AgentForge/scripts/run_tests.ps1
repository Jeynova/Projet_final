# AgentForge - Script de Test Complet
# Exécute toute la suite de validation

Write-Host "🎯 AGENTFORGE - VALIDATION COMPLÈTE" -ForegroundColor Cyan
Write-Host "Système de test automatisé" -ForegroundColor Gray
Write-Host ("="*80) -ForegroundColor Gray

$ROOT = Split-Path -Parent $PSScriptRoot
$SCRIPTS_DIR = Join-Path $ROOT "scripts"

Write-Host "📁 Répertoire: $ROOT" -ForegroundColor Gray
Write-Host "🕐 Début: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# Vérification Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "🐍 Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python non trouvé ! Installez Python 3.8+" -ForegroundColor Red
    exit 1
}

# Vérification des dépendances
Write-Host "`n📦 Vérification des dépendances..." -ForegroundColor Yellow

$requirements = Join-Path $ROOT "requirements.txt"
if (Test-Path $requirements) {
    Write-Host "✅ requirements.txt trouvé" -ForegroundColor Green
    
    # Installation des dépendances
    Write-Host "⬇️ Installation/Mise à jour des dépendances..." -ForegroundColor Yellow
    pip install -r $requirements
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Problème avec les dépendances, continue quand même..." -ForegroundColor Yellow
    } else {
        Write-Host "✅ Dépendances OK" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️ requirements.txt non trouvé" -ForegroundColor Yellow
}

# Vérification des scripts de test
Write-Host "`n🔍 Vérification des scripts de test..." -ForegroundColor Yellow

$testScripts = @(
    "test_comprehensive.py",
    "benchmark.py", 
    "stress_test.py",
    "ui_integration_test.py",
    "run_all_tests.py"
)

$missingScripts = @()
foreach ($script in $testScripts) {
    $scriptPath = Join-Path $SCRIPTS_DIR $script
    if (Test-Path $scriptPath) {
        Write-Host "✅ $script" -ForegroundColor Green
    } else {
        Write-Host "❌ $script" -ForegroundColor Red
        $missingScripts += $script
    }
}

if ($missingScripts.Count -gt 0) {
    Write-Host "`n❌ Scripts manquants: $($missingScripts -join ', ')" -ForegroundColor Red
    Write-Host "Impossible de continuer" -ForegroundColor Red
    exit 1
}

# Nettoyage des anciens résultats
Write-Host "`n🧹 Nettoyage des anciens résultats..." -ForegroundColor Yellow

$resultFiles = @(
    "test_comprehensive_results.json",
    "benchmark_results.json", 
    "stress_test_results.json",
    "ui_integration_test_results.json",
    "master_test_report.json"
)

foreach ($file in $resultFiles) {
    $filePath = Join-Path $ROOT $file
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force
        Write-Host "🗑️ Supprimé: $file" -ForegroundColor Gray
    }
}

# Option de test rapide ou complet
Write-Host "`n🎯 MODE DE TEST:" -ForegroundColor Cyan
Write-Host "1. Test Rapide (Tests complets uniquement)" -ForegroundColor White
Write-Host "2. Test Complet (Tous les tests)" -ForegroundColor White
Write-Host "3. Test Stress uniquement" -ForegroundColor White
Write-Host "4. Test Interface uniquement" -ForegroundColor White

$choice = Read-Host "Choisissez (1-4) [défaut: 2]"
if (-not $choice) { $choice = "2" }

switch ($choice) {
    "1" {
        Write-Host "🚀 Lancement du test rapide..." -ForegroundColor Green
        $testScript = Join-Path $SCRIPTS_DIR "test_comprehensive.py"
        python $testScript
    }
    "2" {
        Write-Host "🚀 Lancement de la suite complète..." -ForegroundColor Green
        $testScript = Join-Path $SCRIPTS_DIR "run_all_tests.py"
        python $testScript
    }
    "3" {
        Write-Host "🔥 Lancement des tests de stress..." -ForegroundColor Green
        $testScript = Join-Path $SCRIPTS_DIR "stress_test.py"
        python $testScript
    }
    "4" {
        Write-Host "🌐 Lancement des tests d'interface..." -ForegroundColor Green
        $testScript = Join-Path $SCRIPTS_DIR "ui_integration_test.py"
        python $testScript
    }
    default {
        Write-Host "❌ Choix invalide" -ForegroundColor Red
        exit 1
    }
}

$exitCode = $LASTEXITCODE

# Affichage des résultats
Write-Host "`n📊 RÉSULTATS DISPONIBLES:" -ForegroundColor Cyan

foreach ($file in $resultFiles) {
    $filePath = Join-Path $ROOT $file
    if (Test-Path $filePath) {
        $sizeKB = [math]::Round((Get-Item $filePath).Length / 1KB, 1)
        Write-Host "📄 $file ($sizeKB KB)" -ForegroundColor Green
    }
}

# Conclusion
Write-Host "`n" -NoNewline
Write-Host ("="*80) -ForegroundColor Gray

if ($exitCode -eq 0) {
    Write-Host "🎉 TESTS RÉUSSIS !" -ForegroundColor Green
    Write-Host "AgentForge validé avec succès" -ForegroundColor White
} else {
    Write-Host "⚠️ TESTS PARTIELS" -ForegroundColor Yellow
    Write-Host "Voir les détails ci-dessus" -ForegroundColor White
}

Write-Host "🕐 Fin: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# Proposition d'ouverture des résultats
$openResults = Read-Host "`nOuvrir le dossier des résultats ? (y/n)"
if ($openResults -eq "y" -or $openResults -eq "Y") {
    Invoke-Item $ROOT
}

exit $exitCode
