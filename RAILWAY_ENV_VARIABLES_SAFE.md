# 🚂 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ДЛЯ RAILWAY (БЕЗОПАСНАЯ ВЕРСИЯ)

## ⚠️ ВАЖНО: НЕТ РЕАЛЬНЫХ ТОКЕНОВ!
Это безопасная версия руководства без чувствительных данных.

## 📋 ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ

### 🤖 ТЕЛЕГРАМ БОТ
```
BOT_TOKEN = ВАШ_БОТ_TOKEN_ЗДЕСЬ
```

### 👥 АДМИНИСТРАТОРЫ
```
ADMIN_IDS = ВАШ_TELEGRAM_ID_ЗДЕСЬ
```

## 🌐 WEBHOOK НАСТРОЙКИ (ОБЯЗАТЕЛЬНЫЕ ДЛЯ RAILWAY)

### 🔗 WEBHOOK КОНФИГУРАЦИЯ
```
USE_WEBHOOK = 1
WEBHOOK_BASE = https://your-project-name.railway.app
WEBHOOK_SECRET = ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_ЗДЕСЬ
WEBHOOK_PATH = /webhook
WEBAPP_PORT = 8080
```

## 📁 КАТАЛОГ ПРОДУКТОВ

### 📋 ПУТЬ К КАТАЛОГУ
```
CATALOG_PATH = assets/fixed_catalog.yaml
```

## 🏷️ ПАРТНЕРСКИЕ ПРОГРАММЫ (ОПЦИОНАЛЬНО)

### 🤝 АФФИЛИАТ КОНФИГУРАЦИЯ
```
AFFILIATE_TAG = skincare_bot
PARTNER_CODE = aff_skincare_bot
REDIRECT_BASE = https://goldapple.ru
DEEPLINK_NETWORK = goldapple
USER_DISCOUNT = 0.05
OWNER_COMMISSION = 0.10
```

## 🗄️ БАЗА ДАННЫХ

### 💾 DATABASE НАСТРОЙКИ
```
DATABASE_URL = sqlite:///data/bot.db
```

## 📊 ЛОГИРОВАНИЕ

### 📝 LOG НАСТРОЙКИ
```
LOG_LEVEL = INFO
LOG_FILE = logs/bot.log
CATALOG_ERRORS_FILE = logs/catalog_errors.jsonl
```

## 📈 АНАЛИТИКА

### 📊 АНАЛИТИЧЕСКИЕ НАСТРОЙКИ
```
ANALYTICS_ENABLED = 1
AB_TESTING = 1
```

## 🔧 РАЗРАБОТКА

### ⚙️ DEBUG НАСТРОЙКИ
```
DEBUG = 0
DEVELOPMENT_MODE = 0
```

## 🤖 ВНЕШНИЕ API (ОПЦИОНАЛЬНО)

### 🔑 OPENAI API
```
OPENAI_API_KEY = ВАШ_OPENAI_API_KEY_ЗДЕСЬ
```

---

## 🎯 МИНИМАЛЬНЫЙ НАБОР ДЛЯ ЗАПУСКА

### ✅ ОБЯЗАТЕЛЬНО:
```
BOT_TOKEN = ВАШ_БОТ_TOKEN_ЗДЕСЬ
ADMIN_IDS = ВАШ_TELEGRAM_ID_ЗДЕСЬ
USE_WEBHOOK = 1
WEBHOOK_BASE = https://your-project-name.railway.app
CATALOG_PATH = assets/fixed_catalog.yaml
```

### 📝 В Railway Dashboard:
1. **Settings** → **Variables**
2. **Добавить каждую переменную**
3. **Сохранить**
4. **Передеплойть**

---

## 🚀 ПОЛНЫЙ СПИСОК (КОПИРОВАТЬ В RAILWAY):

```bash
BOT_TOKEN=ВАШ_БОТ_TOKEN_ЗДЕСЬ
ADMIN_IDS=ВАШ_TELEGRAM_ID_ЗДЕСЬ
USE_WEBHOOK=1
WEBHOOK_BASE=https://your-project-name.railway.app
WEBHOOK_SECRET=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_ЗДЕСЬ
WEBHOOK_PATH=/webhook
WEBAPP_PORT=8080
CATALOG_PATH=assets/fixed_catalog.yaml
AFFILIATE_TAG=skincare_bot
PARTNER_CODE=aff_skincare_bot
DATABASE_URL=sqlite:///data/bot.db
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
ANALYTICS_ENABLED=1
AB_TESTING=1
DEBUG=0
DEVELOPMENT_MODE=0
```

## 📋 ГДЕ НАЙТИ WEBHOOK_BASE:

После первого деплоя в Railway появится URL вида:
`https://your-project-name.railway.app`

Используйте этот URL как значение для `WEBHOOK_BASE`.

## 🔐 WEBHOOK_SECRET:

Можно сгенерировать случайную строку, например:
`webhook_secret_$(date +%s)_$RANDOM`

Или просто: `skincare_bot_webhook_secret_2024`

---

## 🛡️ БЕЗОПАСНОСТЬ:

- ✅ **НЕТ реальных токенов** в этом файле
- ✅ **НЕТ чувствительных данных**
- ✅ **Только шаблоны** для заполнения
- ✅ **Безопасно** публиковать в репозитории

## ✅ ГОТОВО К ЗАПУСКУ! 🚀
