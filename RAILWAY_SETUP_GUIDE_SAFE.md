# 🚂 ПОДРОБНАЯ НАСТРОЙКА RAILWAY ПРОЕКТА (БЕЗОПАСНАЯ ВЕРСИЯ)

## ⚠️ ВАЖНО: НЕТ РЕАЛЬНЫХ ТОКЕНОВ!
Это безопасная версия руководства без чувствительных данных.

## ШАГ 1: Проверка доступа к Railway

### 🔍 Проверьте Railway Dashboard:
1. Зайдите: https://railway.app/dashboard
2. Посмотрите список проектов
3. Если проектов нет → создайте новый

## ШАГ 2: Создание нового проекта

### 📝 Если у вас нет проекта:

1. **Нажмите:** "New Project"
2. **Выберите:** "Deploy from GitHub"
3. **Подключите GitHub:**
   - Нажмите "Connect GitHub"
   - Авторизуйтесь в GitHub
   - Выберите репозиторий: `MarkGerber1/skin-advisor`
   - Branch: `master`

### 📝 Если проект уже есть:

1. **Найдите проект** в списке
2. **Перейдите в проект**
3. **Проверьте вкладки:**
   - Settings → GitHub (должно быть подключено)
   - Deployments (история деплоев)

## ШАГ 3: Настройка переменных окружения

### ⚙️ В Railway Dashboard:

1. **Перейдите:** Settings → Variables
2. **Добавьте переменные:**

```
BOT_TOKEN = ВАШ_БОТ_TOKEN_ЗДЕСЬ
ADMIN_IDS = ВАШ_TELEGRAM_ID_ЗДЕСЬ
USE_WEBHOOK = 1
WEBHOOK_BASE = https://your-project-name.railway.app
WEBHOOK_SECRET = ВАШ_СЕКРЕТНЫЙ_КЛЮЧ_ЗДЕСЬ
CATALOG_PATH = assets/fixed_catalog.yaml
```

## ШАГ 4: Проверка подключения к GitHub

### 🔗 В Settings → GitHub:

- ✅ Repository: `MarkGerber1/skin-advisor`
- ✅ Branch: `master`
- ✅ Auto-deploy: `ON`
- ✅ Status: Connected

## ШАГ 5: Ручной деплой (если автоматический не работает)

### 🚀 В Railway Dashboard:

1. **Перейдите во вкладку:** "Deployments"
2. **Если видите кнопку "Deploy"** → нажмите
3. **Если кнопки нет:**
   - Перейдите: Settings → GitHub
   - Нажмите "Reconnect" или "Connect Repository"
   - Выберите репозиторий заново

## ШАГ 6: Проверка статуса

### 📊 После деплоя:

1. **Service Status:** должен стать "Active"
2. **URL:** появится ссылка на ваше приложение
3. **Logs:** проверьте логи на ошибки

## 🔍 ДИАГНОСТИКА ПРОБЛЕМ

### ❌ "Repository not found":
- Проверьте права доступа к репозиторию
- Убедитесь что репозиторий публичный или у вас есть доступ

### ❌ "No deployments":
- Проверьте подключение к GitHub
- Попробуйте "Reconnect Repository"

### ❌ "Build failed":
- Проверьте логи билда
- Убедитесь что все зависимости указаны в requirements.txt

## 🆘 ЕСЛИ НИЧЕГО НЕ ПОМОГАЕТ

### 📞 Создайте новый проект:

1. **Удалите старый проект** (если есть проблемы)
2. **Создайте новый:**
   - New Project → Deploy from GitHub
   - Выберите репозиторий
   - Настройте переменные окружения
   - Deploy

### 📞 Или используйте Railway CLI локально:

```bash
# Установите Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Авторизуйтесь
railway login

# Подключитесь к проекту
railway link

# Деплойте
railway up
```

## ✅ ПРОВЕРКА ГОТОВНОСТИ

После успешного деплоя:
- ✅ Бот должен отвечать на команды
- ✅ Корзина должна работать
- ✅ Все callback'ы должны обрабатываться
- ✅ В логах не должно быть ошибок

---

## 🛡️ БЕЗОПАСНОСТЬ:

- ✅ **НЕТ реальных токенов** в этом файле
- ✅ **НЕТ чувствительных данных**
- ✅ **Только шаблоны** для заполнения
- ✅ **Безопасно** публиковать в репозитории

---

## 📋 КРАТКАЯ ИНСТРУКЦИЯ

1. **Dashboard:** https://railway.app/dashboard
2. **New Project** → **Deploy from GitHub**
3. **Connect:** `MarkGerber1/skin-advisor`
4. **Branch:** `master`
5. **Variables:** добавьте BOT_TOKEN и другие
6. **Deploy**

**Готово!** 🚀
