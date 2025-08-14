param(
  [string]$BotToken = "",
  [string]$AdminIds = "123456789"
)

$ErrorActionPreference = 'Stop'
Write-Host "=== Skin Advisor setup ===" -ForegroundColor Cyan

function Ensure-Tool($name, $checkCmd, $installCmd) {
  try { & $checkCmd | Out-Null; return $true } catch { }
  if ($installCmd) {
    Write-Host "Installing $name..." -ForegroundColor Yellow
    & $installCmd
    return $true
  }
  return $false
}

# 0) Go to repo root if script launched from elsewhere
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location ($scriptDir | Split-Path -Parent)

# 1) Ensure Python
$pythonOk = $false
try { python --version | Out-Null; $pythonOk = $true } catch { $pythonOk = $false }
if (-not $pythonOk) {
  Write-Host "Python not found. Installing via winget..." -ForegroundColor Yellow
  & winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements --silent | Out-Null
  $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
}

try { python --version } catch { throw "Python is not available after installation. Please reopen PowerShell and rerun." }

# 2) Create venv
if (-not (Test-Path .\venv\Scripts\python.exe)) {
  Write-Host "Creating venv..." -ForegroundColor Yellow
  python -m venv venv
}

# 3) Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -m pip install --upgrade pip
& .\venv\Scripts\python.exe -m pip install -r requirements.txt

# 4) .env
$envPath = ".env"
if (-not (Test-Path $envPath)) {
  Write-Host "Creating .env..." -ForegroundColor Yellow
  $defaultToken = if ($BotToken) { $BotToken } else { "YOUR_TELEGRAM_BOT_TOKEN" }
  @(
    "BOT_TOKEN=`"$defaultToken`"",
    "ADMIN_IDS=`"$AdminIds`"",
    "RUN_MODE=`"polling`"",
    "WEBHOOK_URL=`"`"",
    "WEBHOOK_HOST=`"0.0.0.0`"",
    "WEBHOOK_PORT=`"8080`""
  ) | Set-Content -Encoding UTF8 $envPath
}

# 5) DB init happens on first run inside app

# 6) Run tests
Write-Host "Running tests..." -ForegroundColor Yellow
try { & .\venv\Scripts\python.exe -m pytest -q } catch { Write-Warning "Tests failed or pytest not found." }

Write-Host "Setup completed." -ForegroundColor Green
Write-Host "Use scripts/run-polling.ps1 to start in polling mode, or scripts/run-webhook-ngrok.ps1 for webhook via ngrok." -ForegroundColor Green


