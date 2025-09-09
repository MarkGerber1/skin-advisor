@echo off
REM Быстрое развертывание на Railway
REM Запускает полный процесс: GitHub + Railway

echo 🚀 Начинаем автоматическое развертывание...
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден!
    echo 💡 Установите Python и добавьте в PATH
    pause
    exit /b 1
)

REM Запускаем развертывание
python deploy_to_railway.py

REM Проверяем результат
if %errorlevel% equ 0 (
    echo.
    echo 🎉 Развертывание завершено успешно!
    echo 📋 Проверьте RAILWAY_DEPLOYMENT_SUMMARY.md для деталей
) else (
    echo.
    echo ❌ Ошибка при развертывании!
    echo 📋 Проверьте логи выше для диагностики
)

echo.
echo Нажмите любую клавишу для выхода...
pause >nul
