#!/bin/bash

# Отключаем пейджер для всех команд
export PAGER=cat
export GIT_PAGER=cat
export LESS=""

echo "🔧 Настройки терминала исправлены:"
echo "PAGER=$PAGER"
echo "GIT_PAGER=$GIT_PAGER"
echo "LESS=$LESS"
echo ""

# Выполняем команду git status
echo "📊 Git статус:"
git --no-pager status --porcelain
echo ""

# Показываем измененные файлы
echo "📝 Измененные файлы:"
git --no-pager diff --name-only
echo ""

# Показываем краткую статистику
echo "📈 Статистика изменений:"
git --no-pager diff --stat
echo ""

echo "✅ Проверка завершена без зависания!"
