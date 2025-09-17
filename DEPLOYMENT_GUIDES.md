# 🚀 БЕСПЛАТНЫЕ АЛЬТЕРНАТИВЫ RAILWAY

## 📋 ОБЗОР ВАРИАНТОВ

| Платформа | Бесплатно | Python | Docker | БД | Легкость | Ограничения |
|-----------|-----------|--------|--------|----|----------|-------------|
| **Render** | ✅ Полностью | ✅ | ✅ | ✅ PostgreSQL | 🟢 Легко | 750ч/мес, спит после 15мин |
| **Fly.io** | ✅ $5 кредит | ✅ | ✅ | ❌ | 🟡 Средне | Сложная настройка |
| **Heroku** | ✅ Ограничено | ✅ | ❌ | ✅ Add-ons | 🟢 Легко | 1000ч/мес, спит |
| **Railway** | ❌ Платно | ✅ | ✅ | ✅ | 🟢 Легко | Требует оплаты |
| **VPS** | ✅ DigitalOcean | ✅ | ✅ | ✅ | 🟡 Средне | Самостоятельная настройка |

---

## 🥇 **RENDER.COM** (РЕКОМЕНДУЮ)

### ✅ ПЛЮСЫ:
- Полностью бесплатный
- Python + Docker поддержка
- PostgreSQL база данных
- Простая настройка
- HTTPS домен

### ⚠️ ОГРАНИЧЕНИЯ:
- 750 часов работы в месяц
- Спит после 15 минут без активности
- Ограниченная память (512MB)

### 📝 ШАГИ РАЗВЕРТЫВАНИЯ:

1. **Регистрация**: https://render.com → Sign Up (GitHub аккаунт)

2. **Создать сервис**:
   ```
   Dashboard → New → Web Service
   Connect: GitHub
   Repository: MarkGerber1/skin-advisor
   Branch: master
   ```

3. **Настройки**:
   ```
   Name: skincare-bot
   Environment: Docker
   Dockerfile Path: Dockerfile.free
   Branch: master
   ```

4. **Переменные окружения** (Environment):
   ```
   BOT_TOKEN = [ваш токен]
   PORT = 8080
   USE_WEBHOOK = 0
   LOG_LEVEL = INFO
   ```

5. **База данных** (опционально):
   ```
   New → PostgreSQL
   Name: skincare-db
   Database: skincare
   User: skincare_user
   ```
   Добавить переменную: `DATABASE_URL = [URL из PostgreSQL]`

6. **Deploy**: Нажать "Create Web Service"

### 🔄 ПРОБУЖДЕНИЕ ОТ СНА:
Бот просыпается автоматически при получении сообщений через Telegram API.

---

## 🥈 **HEROKU** (КЛАССИКА)

### ✅ ПЛЮСЫ:
- 1000 бесплатных часов/месяц
- Python поддержка
- Add-ons для БД
- Легкая настройка

### ⚠️ ОГРАНИЧЕНИЯ:
- Спит после 30 минут без активности
- Требует Procfile
- Ограниченная память

### 📝 ШАГИ РАЗВЕРТЫВАНИЯ:

1. **Регистрация**: https://heroku.com → Sign Up

2. **Создать Procfile**:
   ```bash
   echo "web: python -m bot.main" > Procfile
   ```

3. **Создать приложение**:
   ```
   Dashboard → New → Create new app
   App name: skincare-bot-telegram
   Region: Europe
   ```

4. **Подключить GitHub**:
   ```
   Deploy → Deployment method → Connect to GitHub
   Repository: MarkGerber1/skin-advisor
   Branch: master
   Enable Automatic Deploys
   ```

5. **Переменные окружения** (Config Vars):
   ```
   BOT_TOKEN = [ваш токен]
   PORT = 8080
   USE_WEBHOOK = 0
   LOG_LEVEL = INFO
   ```

6. **Deploy**: Manual deploy → Deploy Branch

### 🔄 ПРОБУЖДЕНИЕ:
Бот просыпается автоматически при получении сообщений.

---

## 🥉 **FLY.IO** (МОЩНЫЙ)

### ✅ ПЛЮСЫ:
- $5 стартовый кредит
- Docker поддержка
- Глобальная сеть
- Стабильная работа

### ⚠️ ОГРАНИЧЕНИЯ:
- Сложная настройка
- Требует CLI
- Минимальная оплата после кредита

### 📝 ШАГИ РАЗВЕРТЫВАНИЯ:

1. **Регистрация**: https://fly.io → Sign Up

2. **Установить CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

3. **Создать приложение**:
   ```bash
   fly launch
   App Name: skincare-bot
   Organization: personal
   Region: fra (Frankfurt)
   ```

4. **Настроить fly.toml**:
   ```toml
   app = "skincare-bot"
   kill_signal = "SIGINT"
   kill_timeout = 5
   processes = []

   [env]
     BOT_TOKEN = "[ваш токен]"
     PORT = "8080"
     USE_WEBHOOK = "0"

   [experimental]
     allowed_public_ports = []
     auto_rollback = true

   [[services]]
     http_checks = []
     internal_port = 8080
     processes = ["app"]
     protocol = "tcp"
     script_checks = []

     [services.concurrency]
       hard_limit = 25
       soft_limit = 20
       type = "connections"

     [[services.ports]]
       handlers = ["http"]
       port = 80
       force_https = true

     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
       force_https = true

     [[services.tcp_checks]]
       grace_period = "1s"
       interval = "15s"
       restart_limit = 0
       timeout = "2s"
   ```

5. **Deploy**:
   ```bash
   fly deploy
   ```

---

## 🖥️ **VPS DIGITALOCEAN** (САМЫЙ ДЕШЕВЫЙ)

### 💰 СТОИМОСТЬ: $6/месяц

### ✅ ПЛЮСЫ:
- Полный контроль
- Стабильная работа 24/7
- Можно несколько ботов
- Бесплатный домен

### 📝 ШАГИ РАЗВЕРТЫВАНИЯ:

1. **Регистрация**: https://digitalocean.com → $100 кредит на 60 дней

2. **Создать Droplet**:
   ```
   Create → Droplets
   OS: Ubuntu 22.04
   Plan: Basic ($6/month)
   Region: Frankfurt
   Authentication: SSH Key
   ```

3. **Подключиться по SSH**:
   ```bash
   ssh root@YOUR_IP
   ```

4. **Установить Docker**:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo systemctl enable docker
   sudo systemctl start docker
   ```

5. **Клонировать проект**:
   ```bash
   git clone https://github.com/MarkGerber1/skin-advisor.git
   cd skin-advisor
   ```

6. **Создать .env файл**:
   ```bash
   nano .env
   ```
   ```
   BOT_TOKEN=ваш_токен_здесь
   PORT=8080
   USE_WEBHOOK=0
   LOG_LEVEL=INFO
   ```

7. **Запустить контейнер**:
   ```bash
   docker build -f Dockerfile.free -t skincare-bot .
   docker run -d --restart always -p 8080:8080 --env-file .env skincare-bot
   ```

8. **Настроить firewall**:
   ```bash
   sudo ufw allow 22
   sudo ufw allow 8080
   sudo ufw enable
   ```

### 🔄 МОНИТОРИНГ:
```bash
docker ps  # Проверить статус
docker logs <container_id>  # Посмотреть логи
```

---

## 🤖 **КОНФИГУРАЦИЯ БОТА**

### Для бесплатных тарифов:
- **USE_WEBHOOK = 0** (polling режим)
- **PORT = 8080**
- **LOG_LEVEL = INFO**

### Переменные окружения:
```bash
BOT_TOKEN=ваш_токен
PORT=8080
USE_WEBHOOK=0
LOG_LEVEL=INFO
CATALOG_PATH=assets/fixed_catalog.yaml
```

---

## 📊 **СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ**

| Платформа | Время запуска | Стабильность | Цена |
|-----------|---------------|--------------|------|
| Render | 30 сек | 🟡 Средняя | Бесплатно |
| Heroku | 15 сек | 🟡 Средняя | Бесплатно |
| Fly.io | 5 сек | 🟢 Высокая | $5 кредит |
| VPS | Мгновенно | 🟢 Высокая | $6/мес |

---

## 🎯 **РЕКОМЕНДАЦИЯ**

**Для начала: RENDER.COM** 🚀
- Полностью бесплатно
- Легкая настройка
- Хорошая производительность

**Для продакшена: VPS DIGITALOCEAN** 💪
- Стабильная работа
- Полный контроль
- Минимальная цена

