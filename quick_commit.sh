#!/bin/bash

# 🚀 Beauty Care - Quick Commit & Push
# Быстрый коммит всех изменений с автоматическим пушем

echo "⚡ BEAUTY CARE - QUICK COMMIT"
echo "============================"

# Проверяем изменения
if git status --porcelain | grep -q .; then
    echo "📝 Найдены изменения..."

    # Добавляем все
    git add .

    # Коммит с сообщением
    if [ -n "$1" ]; then
        MESSAGE="$1"
    else
        MESSAGE="chore: quick commit $(date '+%Y-%m-%d %H:%M')"
    fi

    git commit -m "$MESSAGE"

    # Пуш
    echo "🚀 Пушу в GitHub..."
    git push origin master

    echo ""
    echo "✅ ГОТОВО! Изменения запушены"
    echo "🔗 https://github.com/MarkGerber1/skin-advisor"

else
    echo "ℹ️  Нет изменений для коммита"
fi

