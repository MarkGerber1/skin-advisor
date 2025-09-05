@echo off
REM 🚀 Beauty Care Bot - Автоматический Git Push Script (Windows)
REM Автоматизирует процесс коммита и пуша изменений

echo 🤖 BEAUTY CARE BOT - AUTO PUSH SCRIPT
echo =====================================
echo.

REM Проверяем статус git
echo 📊 Проверяю статус git...
git status --porcelain > temp_status.txt
if %errorlevel% neq 0 (
    echo ❌ Ошибка при проверке статуса git
    del temp_status.txt 2>nul
    pause
    exit /b 1
)

findstr /r /c:".*" temp_status.txt >nul
if %errorlevel% equ 0 (
    echo ✅ Найдены изменения для коммита
) else (
    echo ℹ️  Нет изменений для коммита
    del temp_status.txt 2>nul
    exit /b 0
)
del temp_status.txt

echo.

REM Добавляем все изменения
echo 📝 Добавляю изменения...
git add .
if %errorlevel% neq 0 (
    echo ❌ Ошибка при добавлении файлов
    pause
    exit /b 1
)

REM Создаем коммит с автоматическим сообщением
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set DATE=%%c-%%a-%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME=%%a:%%b

set COMMIT_MESSAGE=chore: auto-commit %DATE% %TIME%^^^

🤖 Auto-committed by Beauty Care Bot workflow^^^
- Development updates and improvements^^^
- Project maintenance and optimizations

echo 💾 Создаю коммит...
git commit -m "%COMMIT_MESSAGE%"
if %errorlevel% neq 0 (
    echo ❌ Ошибка при создании коммита
    pause
    exit /b 1
)

REM Пушим изменения
echo 🚀 Пушу в master ветку...
git push origin master
if %errorlevel% neq 0 (
    echo ❌ Ошибка при пуше изменений
    pause
    exit /b 1
)

echo.
echo ✅ ГОТОВО! Изменения успешно запушены в GitHub
echo 🔗 Ссылка: https://github.com/MarkGerber1/skin-advisor
echo.
echo 📋 Последний коммит:
git log --oneline -1

echo.
echo 🎯 Для следующего авто-пуша просто запустите этот файл снова!
pause



