#!/bin/bash

# Полностью безопасный способ выполнения git команд без пейджера
# Используем перенаправление вывода в файлы

echo "🔧 Безопасное выполнение Git команд..."
echo "======================================"

# Создаем временный файл для вывода
TEMP_FILE="/tmp/git_output_$$.txt"

# Выполняем команды с перенаправлением вывода
echo "📊 Git статус:" > "$TEMP_FILE"
git --no-pager status --porcelain >> "$TEMP_FILE" 2>&1
echo "" >> "$TEMP_FILE"

echo "📝 Измененные файлы:" >> "$TEMP_FILE"
git --no-pager diff --name-only >> "$TEMP_FILE" 2>&1
echo "" >> "$TEMP_FILE"

echo "📈 Статистика изменений:" >> "$TEMP_FILE"
git --no-pager diff --stat >> "$TEMP_FILE" 2>&1
echo "" >> "$TEMP_FILE"

echo "✅ Выполнение завершено!" >> "$TEMP_FILE"

# Выводим содержимое файла
cat "$TEMP_FILE"

# Очищаем временный файл
rm -f "$TEMP_FILE"

echo ""
echo "🎉 Готово! Команды выполнены без зависания!"
