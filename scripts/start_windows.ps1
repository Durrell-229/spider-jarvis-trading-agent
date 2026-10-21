# Spider Jarvis — Démarrage
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

Write-Host "=== Démarrage Spider Jarvis (PAPER TRADING) ===" -ForegroundColor Cyan

$backend = Start-Process -PassThru -NoNewWindow -FilePath "backend\.venv\Scripts\python.exe" -ArgumentList "-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--reload" -WorkingDirectory "$root\backend"
Write-Host "Backend PID: $($backend.Id) → http://localhost:8000"

Start-Sleep -Seconds 2

$frontend = Start-Process -PassThru -NoNewWindow -FilePath "npm" -ArgumentList "run","dev","--","--host" -WorkingDirectory "$root\frontend"
Write-Host "Frontend PID: $($frontend.Id) → http://localhost:5173"

Write-Host "`nOuvrez http://localhost:5173"
Write-Host "API docs: http://localhost:8000/docs"
Write-Host "Safety: http://localhost:8000/api/safety"
