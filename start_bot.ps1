# Skin Advisor Bot - Startup Script
# Автор: Ларин Р.Р. (@MagnatMark)

Write-Host "🧴 Skin Advisor Bot - Запуск..." -ForegroundColor Green

# Пути к виртуальному окружению
$venvPath = ".venv\Scripts\python.exe"
$altVenvPath = "venv\Scripts\python.exe"

# Функция загрузки .env (если есть)
function Import-DotEnv {
    param([string]$path = ".env")
    if (Test-Path $path) {
        Get-Content $path | ForEach-Object {
            if ($_ -match '^(\s*#|\s*$)') { return }
            if ($_ -match '^(?<k>[^=\s]+)\s*=\s*(?<v>.*)$') {
                $k = $Matches['k']
                $v = $Matches['v'].Trim().Trim('"').Trim("'")
                [System.Environment]::SetEnvironmentVariable($k, $v, 'Process')
            }
        }
        Write-Host "✓ Загружены переменные из .env" -ForegroundColor Green
    }
}

# Останавливаем предыдущие процессы Python
Write-Host "🛑 Остановка предыдущих процессов..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Определяем Python
$pythonPath = $null
if (Test-Path $venvPath) {
    $pythonPath = $venvPath
    Write-Host "✓ Найдено виртуальное окружение: .venv" -ForegroundColor Green
} elseif (Test-Path $altVenvPath) {
    $pythonPath = $altVenvPath
    Write-Host "✓ Найдено виртуальное окружение: venv" -ForegroundColor Green
} else {
    # Пытаемся создать .venv автоматически
    Write-Host "⚙ Создаю виртуальное окружение (.venv)..." -ForegroundColor Yellow
    try {
        python -m venv .venv
        if (Test-Path $venvPath) {
            $pythonPath = $venvPath
            & $pythonPath -m pip install -U pip
            & $pythonPath -m pip install -r requirements.txt
            Write-Host "✓ .venv создано и зависимости установлены" -ForegroundColor Green
        } else {
            Write-Host "⚠ Не удалось создать .venv — используем системный Python" -ForegroundColor Yellow
            $pythonPath = "python"
        }
    } catch {
        Write-Host "⚠ Ошибка создания .venv — используем системный Python" -ForegroundColor Yellow
        $pythonPath = "python"
    }
}

# Загружаем .env (если есть)
Import-DotEnv

# Дефолты окружения
if (-not $env:CATALOG_PATH) {
    $env:CATALOG_PATH = "assets\fixed_catalog.yaml"
}
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = "."

# Проверка токена
if (-not $env:BOT_TOKEN) {
    Write-Host "❌ BOT_TOKEN не задан. Укажи в .env или перед запуском: $env:BOT_TOKEN=..." -ForegroundColor Red
    exit 1
}

# Запускаем бота
Write-Host "🚀 Запуск бота в режиме polling..." -ForegroundColor Green
Write-Host "🐍 Python: $pythonPath" -ForegroundColor Cyan
Write-Host "📁 Каталог: $(Get-Location)" -ForegroundColor Cyan

try {
    & $pythonPath -m bot.main
} catch {
    Write-Host "❌ Ошибка запуска: $_" -ForegroundColor Red
    Write-Host "💡 Проверь: .venv активирован, зависимости установлены, BOT_TOKEN в .env" -ForegroundColor Yellow
}

Write-Host "👋 Бот остановлен." -ForegroundColor Green


