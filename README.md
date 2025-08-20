# 🧴 Skin Advisor Bot

Весь исходный промпт со спецификацией: см. файл `PROMPT_FULL.md`.

Telegram бот для подбора уходовой косметики и макияжа на основе персонального профиля пользователя.

## 🚀 Быстрый старт

### Локальная разработка

1. **Клонирование и настройка:**
```bash
git clone <repository-url>
cd "чат бот поуходу за кожей"
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Настройка переменных окружения:**
Создайте файл `.env` в корне проекта:
```env
BOT_TOKEN=your_telegram_bot_token
WEBHOOK_SECRET=your_webhook_secret
WEBAPP_PORT=8080
REDIRECT_BASE=https://your-domain.com
DEEPLINK_NETWORK=your_partner_network
USER_DISCOUNT=0.05
OWNER_COMMISSION=0.10
```

3. **Запуск бота:**
```bash
python -m bot.main
```

### Развертывание на Railway

1. **Подготовка к деплою:**
```bash
# Установка Railway CLI
npm install -g @railway/cli

# Авторизация
railway login --browserless

# Создание проекта
railway init

# Привязка к существующему проекту
railway link
```

2. **Настройка переменных окружения:**
```bash
railway variables set BOT_TOKEN=your_telegram_bot_token
railway variables set WEBHOOK_SECRET=your_webhook_secret
railway variables set WEBAPP_PORT=8080
railway variables set REDIRECT_BASE=https://your-railway-domain.railway.app
railway variables set DEEPLINK_NETWORK=your_partner_network
railway variables set USER_DISCOUNT=0.05
railway variables set OWNER_COMMISSION=0.10
```

3. **Деплой:**
```bash
railway up
```

## 📁 Структура проекта

```
bot/
  main.py
  handlers/
    start.py
    flow_palette.py
    flow_skincare.py
  ui/
    keyboards.py
    render.py
engine/
  __init__.py
  models.py
  catalog.py
  catalog_store.py
  logging_setup.py
  selector.py
tools/
  catalog_lint_fix.py
  demo_user_profile.py
tests/
  test_catalog_load.py
  test_selector.py
  test_render.py
configs/
  config.example.toml
data/
  fixed_catalog.yaml
Dockerfile
docker-compose.yml
pyproject.toml
requirements.txt
README.md
PROMPT_FULL.md
```

## 🧪 Тестирование

### Запуск тестов
```bash
cd .skin-advisor
python -m pytest tests/ -v
```

### Основные тесты
- `test_onboarding_profile.py` - Тестирование онбординга
- `test_test_result_texts.py` - Тестирование результатов тестов
- `test_cart_flow.py` - Тестирование корзины
- `test_menu_integrity.py` - Тестирование меню
- `test_reco_hub.py` - Тестирование хаба рекомендаций

## 🔧 Основные функции

### 1. Онбординг пользователя
- Сбор имени, возраста, пола
- Сохранение в профиль пользователя
- Персональные рекомендации

### 2. Диагностические тесты
- Тест типа кожи
- Тест склонности к акне
- Автоматическое формирование отчётов

### 3. Система рекомендаций
- Подбор товаров по профилю
- Фильтрация по наличию (`only_in_stock`)
- Интеграция с корзиной

### 4. Корзина покупок
- Добавление товаров
- Расчёт скидки (5% пользователю)
- Комиссия владельца (10%)

### 5. Отчёты
- PDF отчёты без ссылок
- JSON экспорт
- Сохранение истории

## 🎯 Ключевые особенности

### StateFilter и FSM
**StateFilter(None)** - фильтр состояний для кнопок меню:
- Кнопки работают только в обычном состоянии
- Не мешают прохождению анкет/тестов
- `/menu` - принудительный выход из любого состояния

### Централизованная загрузка каталога
- Кеш через `engine.CatalogStore` (горячая перезагрузка по сигнатуре файла)
- JSONL-логирование ошибок валидации: `logs/catalog_errors.jsonl`

### Система скидок
- 5% скидка пользователю
- 10% комиссия владельца (скрыта от пользователя)
- Автоматический расчёт итоговой суммы

## 📊 Мониторинг и логи

### Логирование
- Подробные логи загрузки каталога
- Статистика рекомендаций
- Отслеживание ошибок

### Метрики
- Количество загруженных товаров
- Фильтрация по наличию
- Статистика замен

## 🔄 CI/CD

### GitHub Actions
- Автоматическое тестирование
- Линтинг кода (black, ruff)
- Деплой на Railway

### Railway
- Автоматический деплой из main ветки
- Управление переменными окружения
- Мониторинг приложения

## 🛠️ Устранение неполадок

### Проблемы с запуском
1. Проверьте токен бота
2. Убедитесь в правильности переменных окружения
3. Проверьте наличие каталога товаров

### Проблемы с рекомендациями
1. Проверьте файл каталога
2. Убедитесь в режиме `only_in_stock`
3. Проверьте логи загрузки

### Проблемы с деплоем
1. Проверьте `.railwayignore`
2. Убедитесь в правильности `railway.toml`
3. Проверьте переменные окружения

## 📞 Поддержка

- **Сайт:** stasya-makeuphair.ru
- **Автор:** Стасья Цуняк
- **Разработчик:** Ларин Р.Р. (@MagnatMark)

## 📄 Лицензия

Проект разработан для персонального использования.


