@echo off
echo === DEPLOY CHANGES TO PRODUCTION ===
echo.

echo Testing imports first...
python test_imports.py

echo.
echo Step 1: Add all changes...
git add .

echo Step 2: Commit with message...
git commit -m "feat(skincare): inline подбор и доб. в корзину после теста

- Добавлена система инлайн-подбора ухода после теста Портрет лица
- Категории → Товары → Варианты → Корзина с приоритизацией источников
- GA → RU Official → RU MP → INTL приоритизация
- Идемпотентная корзина с валидацией variant_id
- Защита от двойного клика (debounce)
- Полная аналитика всех действий пользователя
- 8 товаров на страницу с пагинацией"

echo Step 3: Push to origin master...
git push origin master

echo Step 4: Check status...
git status

echo.
echo === DEPLOY COMPLETE ===
echo Changes should be live in Railway within 2-3 minutes
pause
