$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\backend"
& .\.venv\Scripts\Activate.ps1
pytest tests/ -v --tb=short
