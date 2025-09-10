#!/bin/bash

echo "🧹 Начинаю очистку проекта..."

# Удаляем Python кэш
echo "Удаляю Python кэш файлы..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Удаляем лог файлы
echo "Удаляю лог файлы..."
find . -name "*.log" -delete

# Удаляем временные файлы
echo "Удаляю временные файлы..."
find . -name "*.tmp" -o -name "*~" -o -name "*.bak" -o -name "*.orig" -o -name "*.swp" -o -name "*.swo" -delete

# Очищаем кэш
echo "Очищаю кэш директории..."
rm -rf .mypy_cache .pytest_cache .ruff_cache

echo "✅ Очистка завершена!"
echo "📊 Статистика после очистки:"
du -sh .
