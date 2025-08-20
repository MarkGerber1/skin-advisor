# Skin Advisor Bot - Startup Script
# Автор: Ларин Р.Р. (@MagnatMark)

Write-Host "🧴 Skin Advisor Bot - Запуск..." -ForegroundColor Green

# Проверяем наличие виртуального окружения
$venvPath = ".venv\Scripts\python.exe"
$altVenvPath = "venv\Scripts\python.exe"

if (Test-Path $venvPath) {
    $pythonPath = $venvPath
    Write-Host "✓ Найдено виртуальное окружение: .venv" -ForegroundColor Green
} elseif (Test-Path $altVenvPath) {
    $pythonPath = $altVenvPath
    Write-Host "✓ Найдено виртуальное окружение: venv" -ForegroundColor Green
} else {
    Write-Host "⚠ Виртуальное окружение не найдено. Используем системный Python." -ForegroundColor Yellow
    $pythonPath = "python"
}

# Останавливаем предыдущие процессы Python
Write-Host "🛑 Остановка предыдущих процессов..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Переходим в директорию бота
Set-Location -LiteralPath ".skin-advisor"

# Устанавливаем переменные окружения
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = "."

# Запускаем бота
Write-Host "🚀 Запуск бота в режиме polling..." -ForegroundColor Green
Write-Host "📁 Рабочая директория: $(Get-Location)" -ForegroundColor Cyan
Write-Host "🐍 Python: $pythonPath" -ForegroundColor Cyan

try {
    & $pythonPath -m app.main --mode=polling
} catch {
    Write-Host "❌ Ошибка запуска: $_" -ForegroundColor Red
    Write-Host "💡 Попробуйте:" -ForegroundColor Yellow
    Write-Host "   1. Активировать виртуальное окружение: .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "   2. Установить зависимости: pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "   3. Проверить токен бота в переменных окружения" -ForegroundColor Yellow
}

Write-Host "👋 Бот остановлен." -ForegroundColor Green


