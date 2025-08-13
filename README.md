#  Skin Advisor Telegram Bot

![Bot Logo](https://i.imgur.com/example.png) **Skin Advisor** — это ваш персональный косметолог-консультант в Telegram. Бот проводит детальную диагностику кожи на основе анкеты и формирует персональные рекомендации по уходу и макияжу со ссылками на покупку.

## 🚀 Основные возможности

* **🧪 Детальная анкета:** Пошаговый опрос для определения типа, состояний и особенностей вашей кожи.
* **📊 Точная диагностика:** Алгоритм определяет тип кожи, подтон, колорит и ключевые состояния (обезвоженность, чувствительность, акне и т.д.).
* **🛍️ Персональные рекомендации:** Бот подбирает утренний, вечерний и еженедельный уход, а также декоративную косметику.
* **🛒 Ссылки на покупку:** Для каждого продукта предоставляются ссылки на популярные маркетплейсы (`Ozon`, `Wildberries`, `Золотое Яблоко`) в трех ценовых категориях.
* **📜 Правила совместимости:** Бот предупреждает о правилах введения активных ингредиентов (ретиноиды, кислоты) и их сочетаемости.
* **📄 Экспорт результатов:** Скачать отчет о диагностике и рекомендациях в PDF.
* **🔐 Админ‑панель:** `/admin`, `/stats`, `/update_products` (+ загрузка `products.json` прямо в чат). Доступ ограничен через `ADMIN_IDS`.

## ⚙️ Запуск

1. Python 3.11+, создайте `.env` на основе `.env.example` и заполните `BOT_TOKEN`, `ADMIN_IDS`.
2. Установка зависимостей:
   - Windows PowerShell:
     - `python -m venv venv`
     - `./venv/Scripts/Activate.ps1`
     - `pip install -r requirements.txt`
3. Запуск в режиме разработки (polling):
   - `python app/main.py`

## 🌐 Прод‑запуск (Webhook)

- В `.env` установите: `RUN_MODE=webhook`, `WEBHOOK_URL=https://<ваш_домен>/webhook`, `WEBHOOK_HOST=0.0.0.0`, `WEBHOOK_PORT=8080`.
- Приложение само поднимет HTTP‑сервер и зарегистрирует вебхук.

### Быстрый старт через ngrok (локально)
1. `ngrok http 8080`
2. Возьмите HTTPS URL вида `https://<subdomain>.ngrok.io` и подставьте в `WEBHOOK_URL=https://<subdomain>.ngrok.io/webhook`.
3. Запустите бот: `python app/main.py` (режим webhook).

### Схема Nginx (пример)
- Прокси на локальный порт приложения:

```
location /webhook {
    proxy_pass http://127.0.0.1:8080/webhook;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Убедитесь, что домен доступен по HTTPS (например, через Let’s Encrypt).

## 🧰 Админ‑команды
- `/admin` — приветствие админа
- `/stats` — статистика: пользователи, анкеты, диагнозы
- `/update_products` — инструкция по загрузке каталога, затем отправьте в чат файл `products.json` (application/json). Каталог перезагрузится без перезапуска бота.

## 📦 Стек технологий
- Python 3.11, Aiogram 3, SQLAlchemy (async) + SQLite, Pydantic, FPDF2, Docker
