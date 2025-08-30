@echo off
REM Максимально простой запуск - без проверок
cd /d "%~dp0"
.venv\Scripts\python.exe -m bot.main
pause

