param(
  [string]$NgrokPath = "ngrok",
  [string]$Port = "8080"
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent)

if (-not (Test-Path .\venv\Scripts\python.exe)) { Write-Host "Run scripts/setup.ps1 first" -ForegroundColor Yellow; exit 1 }

Write-Host "Starting ngrok on port $Port..." -ForegroundColor Cyan
Start-Process -FilePath $NgrokPath -ArgumentList @("http", $Port) -WindowStyle Minimized
Start-Sleep -Seconds 3

try {
  $tunnels = Invoke-RestMethod http://127.0.0.1:4040/api/tunnels
  $publicUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -First 1).public_url
  if (-not $publicUrl) { throw "No https tunnel found" }
} catch {
  Write-Error "Cannot get ngrok public URL. Ensure ngrok is running."
  exit 1
}

# Patch .env to webhook base (preserve other lines)
Write-Host "Configuring .env WEBHOOK_BASE=$publicUrl ..." -ForegroundColor Cyan
$envPath = ".env"
if (-not (Test-Path $envPath)) { Copy-Item .env.example .env }
$content = Get-Content $envPath
if ($content -match "^WEBHOOK_BASE=") {
  $content = $content -replace '^WEBHOOK_BASE=.*$', "WEBHOOK_BASE=$publicUrl"
} else {
  $content += "`nWEBHOOK_BASE=$publicUrl"
}
Set-Content -Encoding UTF8 $envPath $content

Write-Host "Registering webhook..." -ForegroundColor Green
& .\venv\Scripts\python.exe -m app.webctl set

Write-Host "Run webhook mode:" -ForegroundColor Green
Write-Host ".\\venv\\Scripts\\python.exe -m app.main --mode=webhook" -ForegroundColor Green
Write-Host "Webhook URL: $publicUrl/tg/<your_secret> (stored in .env WEBHOOK_SECRET)" -ForegroundColor Green

