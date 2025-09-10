#!/bin/bash

# Полностью отключаем пейджер для всех команд
export PAGER=cat
export GIT_PAGER=cat
export LESS=""
export LV=""  # Отключаем lv если установлен

echo "🔧 Пейджер полностью отключен"
echo "PAGER=$PAGER"
echo "GIT_PAGER=$GIT_PAGER"
echo "LESS=$LESS"
echo ""

# Выполняем git команды с --no-pager
echo "📊 Git статус:"
git --no-pager status --porcelain
echo ""

echo "📝 Измененные файлы:"
git --no-pager diff --name-only | cat
echo ""

echo "📈 Статистика изменений:"
git --no-pager diff --stat | cat
echo ""

echo "✅ Команды выполнены без зависания!"
