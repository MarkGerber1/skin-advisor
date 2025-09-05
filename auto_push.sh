#!/bin/bash

# 🚀 Beauty Care Bot - Автоматический Git Push Script
# Автоматизирует процесс коммита и пуша изменений

echo "🤖 BEAUTY CARE BOT - AUTO PUSH SCRIPT"
echo "====================================="
echo ""

# Проверяем статус git
echo "📊 Проверяю статус git..."
if git status --porcelain | grep -q .; then
    echo "✅ Найдены изменения для коммита"
else
    echo "ℹ️  Нет изменений для коммита"
    exit 0
fi

echo ""

# Добавляем все изменения
echo "📝 Добавляю изменения..."
git add .

# Создаем коммит с автоматическим сообщением
COMMIT_MESSAGE="chore: auto-commit $(date '+%Y-%m-%d %H:%M:%S')

🤖 Auto-committed by Beauty Care Bot workflow
- Development updates and improvements
- Project maintenance and optimizations"

echo "💾 Создаю коммит..."
git commit -m "$COMMIT_MESSAGE"

# Пушим изменения
echo "🚀 Пушу в master ветку..."
git push origin master

echo ""
echo "✅ ГОТОВО! Изменения успешно запушены в GitHub"
echo "🔗 Ссылка: https://github.com/MarkGerber1/skin-advisor"
echo ""
echo "📋 Последний коммит:"
git log --oneline -1




