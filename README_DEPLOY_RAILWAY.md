Deploy to Railway (PaaS)

Проект готов к запуску как один веб‑сервис Railway:
- POST `/tg/<WEBHOOK_SECRET>` — Telegram webhook
- GET `/healthz` — проверка живости
- GET `/version` — версия приложения
- GET `/r` — редирект с логированием кликов (302)

Что уже настроено
- Procfile: `web: python -m app.main --mode=webhook`
- Учёт переменной `PORT` и домена Railway (`RAILWAY_PUBLIC_DOMAIN`/`RAILWAY_STATIC_URL`).
- На старте:
  - миграции SQLite (`data/app.db`)
  - автосборка URL вебхука `https://<domain>/tg/<WEBHOOK_SECRET>` и попытка `setWebhook`.
  - если `REDIRECT_BASE` пуст, подставляется `https://<domain>/r`.

Переменные окружения (Railway → Settings → Variables)
- BOT_TOKEN: токен бота
- WEBHOOK_SECRET: секретная часть URL (например, 32+ символа)
- USER_DISCOUNT: 0.05 (по умолчанию)
- OWNER_COMMISSION: 0.10 (по умолчанию)
- DEEPLINK_NETWORK: опционально
- PARTNER_SUBID: опционально
- REDIRECT_BASE: можно оставить пустым (будет `https://<domain>/r`)
- CATALOG_PATH: опционально (если нужен кастомный каталог)

Том (Volume)
- Railway → Storage → Add Volume
  - Size: ≥ 1 GB
  - Mount Path: `/app/data`
  - (опционально) второй Volume на `/app/logs`

Деплой из GitHub
1. Push в GitHub репозиторий (в корне проекта уже есть `Procfile`).
2. Railway → New Project → New Service → Deploy from Repo.
3. Указать репозиторий, дождаться сборки (Nixpacks определит Python и Procfile).
4. В Variables задать значения (см. выше). В Storage добавить Volume и примонтировать.
5. После запуска в логах появятся строки вида:
   - `boot: mode=webhook port=<PORT> webhook_base=<url> redirect_base=<url>`
   - `webhook: set ok url=<url>` (или предупреждение, если установка не удалась)

Проверка
- `GET https://<service>.up.railway.app/healthz` → `ok`
- `GET https://<service>.up.railway.app/version` → `{ "version": "..." }`
- Через Railway → Shell выполнить:
  - `python -m app.webctl info` — проверить URL вебхука
  - `python -m app.webctl set` — вручную перевыставить вебхук (если домен сменился)

Заметки
- Файловая система эфемерная, поэтому SQLite живёт в Volume `/app/data/app.db`.
- Логи можно писать в `/app/logs` при наличии второго Volume.
- REDIRECT_BASE по умолчанию строится от Railway домена, можно переопределить в Variables.


