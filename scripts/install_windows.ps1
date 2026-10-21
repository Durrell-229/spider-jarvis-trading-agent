# Spider Jarvis — Installation Windows
$ErrorActionPreference = "Stop"
Write-Host "=== Spider Jarvis Trading Agent — Installation ===" -ForegroundColor Cyan

$py = python --version 2>&1
if ($LASTEXITCODE -ne 0) { Write-Error "Python 3.12+ requis"; exit 1 }
Write-Host "Python: $py"

$node = node --version 2>&1
if ($LASTEXITCODE -ne 0) { Write-Error "Node.js 18+ requis"; exit 1 }
Write-Host "Node: $node"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "`n[1/4] Environnement virtuel Python..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.venv")) {
  python -m venv backend\.venv
}
& backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

Write-Host "`n[2/4] Configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Fichier .env créé (mode paper par défaut)"
}

Write-Host "`n[3/4] Dépendances frontend..." -ForegroundColor Yellow
Set-Location frontend
npm install
npm install zustand
Set-Location $root

Write-Host "`n[4/4] Terminé." -ForegroundColor Green
Write-Host "Lancez: .\scripts\start_windows.ps1"
Write-Host "MODE: PAPER TRADING (aucun ordre réel)"
