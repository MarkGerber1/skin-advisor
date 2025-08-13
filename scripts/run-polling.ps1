$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent)
if (-not (Test-Path .\venv\Scripts\python.exe)) { Write-Host "Run scripts/setup.ps1 first" -ForegroundColor Yellow; exit 1 }
Write-Host "Starting bot (polling)..." -ForegroundColor Cyan
& .\venv\Scripts\python.exe -m app.main
