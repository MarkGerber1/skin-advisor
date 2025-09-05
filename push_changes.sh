#!/bin/bash

# Скрипт для быстрого коммита и пуша изменений
# Использование: ./push_changes.sh "commit message"

if [ $# -eq 0 ]; then
    echo "❌ Ошибка: Укажите сообщение коммита"
    echo "Использование: ./push_changes.sh \"commit message\""
    exit 1
fi

COMMIT_MESSAGE="$1"

echo "🚀 Быстрый коммит и пуш..."
echo "📝 Сообщение: $COMMIT_MESSAGE"
echo ""

# Добавляем все изменения
echo "➕ Добавление файлов..."
git add .

# Проверяем есть ли что коммитить
if git diff --cached --quiet; then
    echo "⚠️  Нет изменений для коммита"
    exit 0
fi

# Коммитим
echo "💾 Создание коммита..."
if git commit -m "$COMMIT_MESSAGE"; then
    echo "✅ Коммит создан успешно"
else
    echo "❌ Ошибка при создании коммита"
    exit 1
fi

# Пушим
echo "📤 Отправка в репозиторий..."
if git push origin $(git branch --show-current); then
    echo "✅ Изменения отправлены в репозиторий!"
    echo ""
    echo "🔗 Репозиторий: https://github.com/MarkGerber1/skin-advisor"
    echo "📊 Последний коммит: $(git log --oneline -1)"
else
    echo "❌ Ошибка при отправке в репозиторий"
    echo "💡 Возможно есть конфликты - попробуйте git pull --rebase"
    exit 1
fi

echo ""
echo "🎉 Готово! Изменения в репозитории."




