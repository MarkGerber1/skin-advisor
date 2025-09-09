# 🚂 Railway Deployment Guide

## Шаг 1: Подготовка проекта

### ✅ Требуемые файлы (уже готовы):
- `Dockerfile` - Docker конфигурация
- `railway.json` - Railway конфигурация
- `railway.toml` - Альтернативная конфигурация
- `requirements.txt` - Python зависимости
- `start.py` - Точка входа
- `entrypoint.sh` - Docker entrypoint

### 🔧 Переменные окружения

Создайте `.env` файл локально для тестирования:

```bash
# === BOT CONFIGURATION ===
BOT_TOKEN=your_telegram_bot_token_here

# === WEBHOOK CONFIGURATION ===
USE_WEBHOOK=1
WEBHOOK_BASE=https://your-railway-app.railway.app
WEBHOOK_SECRET=your_webhook_secret_here
WEBHOOK_PATH=/webhook
WEBAPP_PORT=8080

# === PARTNER & AFFILIATE ===
AFFILIATE_TAG=skincare_bot
PARTNER_CODE=aff_skincare_bot

# === CATALOG & DATA ===
CATALOG_PATH=assets/fixed_catalog.yaml

# === LOGGING ===
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# === ANALYTICS & METRICS ===
ANALYTICS_ENABLED=1
AB_TESTING=1
```

## Шаг 2: Развертывание на Railway

### 🚀 Через Railway CLI:

```bash
# Установите Railway CLI если нет
npm install -g @railway/cli

# Авторизуйтесь
railway login

# Создайте новый проект
railway init

# Добавьте переменные окружения
railway variables set BOT_TOKEN=your_telegram_bot_token
railway variables set USE_WEBHOOK=1
railway variables set WEBHOOK_BASE=https://your-app.railway.app

# Разверните
railway up
```

### 🚀 Через GitHub:

1. **Создайте GitHub репозиторий:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/your-repo.git
   git push -u origin main
   ```

2. **Подключите к Railway:**
   - Зайдите на [railway.app](https://railway.app)
   - Создайте новый проект
   - Выберите "Deploy from GitHub"
   - Выберите ваш репозиторий

3. **Настройте переменные окружения:**
   В Railway dashboard перейдите в Variables и добавьте:

   | Variable | Value | Description |
   |----------|-------|-------------|
   | `BOT_TOKEN` | `your_bot_token` | Telegram Bot Token |
   | `USE_WEBHOOK` | `1` | Включить webhook режим |
   | `WEBHOOK_BASE` | `https://your-app.railway.app` | URL вашего Railway приложения |
   | `AFFILIATE_TAG` | `skincare_bot` | Тег для партнерских ссылок |
   | `LOG_LEVEL` | `INFO` | Уровень логирования |
   | `ANALYTICS_ENABLED` | `1` | Включить аналитику |

## Шаг 3: Настройка Webhook

### 🔗 Автоматическая настройка:
Бот автоматически настроит webhook при запуске, если `USE_WEBHOOK=1`.

### 🔗 Ручная настройка:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -d "url=https://your-app.railway.app/webhook"
```

## Шаг 4: Проверка развертывания

### 📊 Логи:
```bash
# Посмотреть логи
railway logs

# Или через dashboard
# railway.app → ваш проект → Logs
```

### ✅ Проверка работы:
1. **Webhook URL:** `https://your-app.railway.app/webhook`
2. **Health Check:** `https://your-app.railway.app/health`
3. **Bot Status:** Отправьте `/start` в Telegram

### 🔍 Возможные проблемы:

#### ❌ "BOT_TOKEN is not set":
- Проверьте переменную окружения в Railway dashboard

#### ❌ "Webhook failed":
- Убедитесь что `WEBHOOK_BASE` указывает на ваш Railway URL
- Проверьте логи на наличие ошибок webhook

#### ❌ "Import errors":
- Проверьте что все файлы скопировались в Docker контейнер
- Проверьте `requirements.txt`

#### ❌ "Port already in use":
- Railway автоматически назначает порт
- Не устанавливайте `PORT` переменную вручную

## Шаг 5: Мониторинг

### 📈 Метрики:
- Логи автоматически сохраняются в Railway
- Мониторьте использование CPU/памяти в dashboard
- Настройте alerts для ошибок

### 🔄 Обновления:
```bash
# Обновите код
git add .
git commit -m "Update bot"
git push

# Railway автоматически переразвернет
```

## Шаг 6: Производственные настройки

### 🔒 Безопасность:
- Никогда не храните `BOT_TOKEN` в коде
- Используйте Railway secrets для чувствительных данных
- Настройте firewall правила если нужно

### ⚡ Оптимизация:
- Мониторьте использование ресурсов
- Настройте health checks
- Рассмотрите использование Redis для кэширования

---

## 🎯 Быстрый чек-лист:

- [ ] Создан Railway аккаунт
- [ ] Получен Telegram Bot Token
- [ ] Настроены переменные окружения
- [ ] Проект развернут
- [ ] Webhook настроен
- [ ] Бот отвечает на сообщения
- [ ] Логи проверены

## 🚨 Troubleshooting:

### Локальное тестирование:
```bash
# Установите зависимости
pip install -r requirements.txt

# Создайте .env файл
cp .env.local.example .env

# Запустите локально
python start.py
```

### Распространенные ошибки:
1. **ImportError**: Проверьте что все файлы в Docker
2. **WebhookError**: Проверьте URL и токен
3. **Timeout**: Увеличьте timeout в Railway settings

---

## 📞 Поддержка:

Если возникли проблемы:
1. Проверьте логи в Railway dashboard
2. Убедитесь что все переменные установлены
3. Проверьте webhook URL в Telegram BotFather
4. Создайте issue в GitHub репозитории
