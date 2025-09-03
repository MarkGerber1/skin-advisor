#!/bin/bash

# 🚀 Скрипт развертывания сайта на GitHub Pages
# Использование: ./deploy-site.sh

echo "🎨 Начинаем развертывание сайта Beauty Care..."

# Создаем ветку gh-pages
echo "📋 Создаем ветку gh-pages..."
git checkout -b gh-pages

# Копируем основные файлы
echo "📁 Копируем файлы..."
cp VIEW_ALL.html index.html
cp ui/demo/preview.html demo.html
cp ui/brand/preview.html brand.html
cp ui/brand/convert-svg-to-png.html converter.html
cp ОТЧЕТ_ДЛЯ_ПАРТНЕРА_2.md PARTNER_REPORT_2.md

# Копируем папки
echo "📂 Копируем папки..."
mkdir -p stickers logos
cp -r ui/brand/stickers/* stickers/ 2>/dev/null || true
cp ui/brand/logo.svg logos/
cp ui/brand/logo-dark.svg logos/

# Коммитим изменения
echo "💾 Коммитим изменения..."
git add .
git commit -m "🚀 Deploy demo website for partners

- Main page with all materials overview
- Design system demo
- Brand assets (logos & stickers)
- Partner report
- SVG to PNG converter

Ready for GitHub Pages deployment"

# Push на GitHub
echo "📤 Отправляем на GitHub..."
git push origin gh-pages

echo ""
echo "🎉 Готово!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Зайдите в репозиторий на GitHub"
echo "2. Settings → Pages"
echo "3. Source: 'Deploy from a branch'"
echo "4. Branch: 'gh-pages' → '/ (root)'"
echo "5. Save"
echo ""
echo "🌐 Через 2-3 минуты сайт будет доступен:"
echo "https://markgerber1.github.io/skin-advisor/"
echo ""
echo "📱 Что будет на сайте:"
echo "• Главная: index.html"
echo "• Дизайн-система: demo.html"
echo "• Бренд: brand.html"
echo "• Конвертер: converter.html"
echo "• Отчет: PARTNER_REPORT_2.md"

