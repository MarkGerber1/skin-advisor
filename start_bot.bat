@echo off
chcp 65001 >nul
echo ====================================
echo 🧴 Skin Advisor Bot - Windows Start
echo ====================================

REM Переходим в папку проекта
cd /d "%~dp0"

REM Проверяем наличие venv
if exist ".venv\Scripts\python.exe" (
    echo ✓ Найдено виртуальное окружение
    set PYTHON_PATH=.venv\Scripts\python.exe
) else (
    echo ❌ Виртуальное окружение не найдено
    echo Создайте его командой: python -m venv .venv
    pause
    exit /b 1
)

REM Устанавливаем кодировку
set PYTHONIOENCODING=utf-8
set PYTHONPATH=.

REM Проверяем .env
if exist ".env" (
    echo ✓ Найден файл .env
) else (
    echo ⚠ Файл .env не найден
    echo Создайте его и добавьте BOT_TOKEN=your_token_here
)

REM Запускаем бота
echo 🚀 Запуск бота...
"%PYTHON_PATH%" -m bot.main

echo.
echo 👋 Бот остановлен
pause

