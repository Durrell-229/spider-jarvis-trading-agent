Write-Host "Arrêt des processus Spider Jarvis..." -ForegroundColor Yellow
foreach ($port in 8000,5173) {
  $c = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
  if ($c) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Write-Host "Arrêté."
