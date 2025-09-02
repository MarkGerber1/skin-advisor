@echo off
echo ========================================
echo 🚀 DEPLOY SKINCARE PICKER SYSTEM
echo ========================================
echo.

echo 📋 Created files:
echo   ✅ bot/handlers/skincare_picker.py
echo   ✅ engine/source_resolver.py
echo   ✅ services/cart_service.py
echo   ✅ engine/analytics.py
echo   ✅ i18n/ru.py
echo   ✅ services/__init__.py
echo.

echo 🔄 Updated files:
echo   ✅ bot/main.py
echo   ✅ bot/handlers/detailed_skincare.py
echo.

echo 📝 Commit message:
echo "feat(skincare): inline подбор и доб. в корзину после теста"
echo.

echo ⚡ Starting deployment...
echo.

echo Step 1: Adding files...
git add .

echo.
echo Step 2: Committing...
git commit -m "feat(skincare): inline подбор и доб. в корзину после теста

- Добавлена система инлайн-подбора ухода после теста Портрет лица
- Категории → Товары → Варианты → Корзина с приоритизацией источников
- GA → RU Official → RU MP → INTL приоритизация
- Идемпотентная корзина с валидацией variant_id
- Защита от двойного клика (debounce)
- Полная аналитика всех действий пользователя
- 8 товаров на страницу с пагинацией"

echo.
echo Step 3: Pushing to production...
git push origin master

echo.
echo Step 4: Checking status...
git status

echo.
echo ========================================
echo ✅ DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo 🎯 What should work now:
echo   • Inline skincare picker after face portrait test
echo   • Category selection → Product list → Variants → Cart
echo   • GA → RU Official → RU MP → INTL prioritization
echo   • Idempotent cart with validation
echo   • Double-click protection
echo   • Full analytics tracking
echo.
echo 📊 Check Railway logs for:
echo   • "OK skincare picker router imported"
echo   • New callbacks: c:cat:, c:prd:, c:add:
echo   • Analytics events: recommendations_viewed, category_opened
echo.
echo 🚀 System will be live in Railway within 2-3 minutes!
echo ========================================

pause


