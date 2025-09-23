# Render.com Deployment Guide

## 🚀 Быстрое развертывание на Render

### 1. Создание сервиса на Render

1. Перейдите на [render.com](https://render.com)
2. Нажмите **"New"** → **"Web Service"**
3. Выберите **"Connect GitHub"**
4. Найдите и подключите репозиторий `skin-advisor`

### 2. Настройки сервиса

```
Name: skin-advisor-bot
Environment: Docker
Region: Frankfurt (EU Central) - рекомендуется для России
Branch: master
```

### 3. Переменные окружения (Environment Variables)

Добавьте следующие переменные:

```
BOT_TOKEN=ваш_бот_токен_от_BotFather
USE_WEBHOOK=0
CATALOG_PATH=assets/fixed_catalog.yaml
RENDER=1
```

### 4. Build & Deploy

Render автоматически:
- Соберет Docker образ из `Dockerfile`
- Запустит `render_app.py` как веб-сервер
- Откроет порт 8080 (или тот, что назначит Render)
- Запустит бота в фоне

### 5. Проверка развертывания

После успешного деплоя:

1. **Health Check**: `https://your-app-name.onrender.com/health`
   ```json
   {
     "status": "OK",
     "bot_started": true,
     "timestamp": "2024"
   }
   ```

2. **Webhook endpoint**: `https://your-app-name.onrender.com/webhook`

3. **Bot должен автоматически запуститься** и начать обработку сообщений

### 🔧 Troubleshooting

#### Bot не запускается
- Проверьте логи в Render Dashboard → Logs
- Убедитесь, что `BOT_TOKEN` корректный
- Проверьте переменную `USE_WEBHOOK=0` (для polling режима)

#### Health check возвращает ошибку
- Проверьте, что все зависимости установлены в `requirements.txt`
- Убедитесь, что `render_app.py` может импортировать `bot.main`

#### Webhook не работает
- Для production используйте webhook вместо polling
- Настройте webhook URL в BotFather: `https://your-app-name.onrender.com/webhook`

### 📊 Мониторинг

- **Logs**: Render Dashboard → Logs (в реальном времени)
- **Metrics**: CPU, Memory, Response times
- **Health**: `/health` endpoint для automated checks

### 💰 Цена

Render предлагает:
- **Free tier**: 750 часов/месяц, спящий режим после 15 мин бездействия
- **Paid plans**: от $7/месяц для постоянной работы

### 🔄 Обновления

При пуше в `master` branch Render автоматически:
1. Соберет новый Docker образ
2. Запустит zero-downtime deployment
3. Переключит трафик на новую версию

**Готово! Ваш бот теперь работает на Render.com 🎉**
