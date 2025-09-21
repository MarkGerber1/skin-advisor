# �� Skin Advisor Bot

## 🚀 DEPLOYMENT

**Last smoke deploy:** $(date +"%Y-%m-%d %H:%M:%S")
**Preview test:** feature branch for PR testing
**Auto-deploy test:** $(date +"%Y-%m-%d %H:%M:%S")
**Railway auto-deploy:** enabled $(date +"%Y-%m-%d %H:%M:%S")

### Railway (Production)
```bash
# Environment Variables
BOT_TOKEN=your_telegram_bot_token_here
USE_WEBHOOK=0  # Use polling for Railway
PORT=8080
DEBUG=0
```

### Railway with Webhook (Alternative)
```bash
# For webhook mode (requires public HTTPS URL)
USE_WEBHOOK=1
WEBHOOK_URL=https://your-railway-app.railway.app
WEBHOOK_PATH=/webhook
```

### Local Development
```bash
# Copy environment template
cp env.example .env

# Install dependencies
pip install -r requirements.txt

# Run bot
python bot/main.py
```

## 🚀 АВТОМАТИЧЕСКИЙ PUSH

### Быстрые команды для коммита и пуша:

```bash
# Автоматический коммит и пуш всех изменений
git ac

# Коммит с пользовательским сообщением
git acm "feat: add new feature"

# Ручной запуск
./quick_commit.sh "Your message"
```

### Git Hooks:
- **post-commit hook** автоматически пушит после каждого коммита
- Все изменения сразу попадают в GitHub без дополнительных команд

---

## 📋 ПОЛНЫЙ ПРОМПТ И ТРЕБОВАНИЯ

### Роль и стек технологий
**Роль:** Ведущий Python-инженер и продуктовый разработчик  
**Стек:** Python 3.11, aiogram v3 (FSM), pydantic v2, ruamel.yaml, docker-compose  
**Цель:** Исправить логику бота и интегрировать движок подбора с валидным каталогом fixed_catalog.yaml

---

## 🎯 ЭПИКИ ДЛЯ РЕАЛИЗАЦИИ

### Эпик A — Последовательная логика диагностики (FSM), без параллельных тестов

**Требования:**
- Реализовать один активный поток за раз: сначала базовый тип кожи (dry/oily/combo/sensitive/normal), затем состояния (sensitivity, dehydration, acne и т.д.)
- Никаких «одновременных» тестов. Кнопка «Сформировать отчёт» активируется только после прохождения всех обязательных шагов
- Использовать aiogram FSM: состояния `B1_TYPE → B2_CONCERNS → B3_CONFIRM → B4_REPORT` для кожи, и `A1_UNDERTONE → A2_VALUE → A3_HAIR → A4_BROWS → A5_EYES → A6_CONTRAST → A7_REPORT` для палитры
- CallbackQuery обрабатывать централизованно, проверять шаблон callback_data (prefix+step+field+value) и гасить «дребезг» двойных кликов (answerCallbackQuery + идемпотентность по message_id/state)
- При генерации отчёта редактировать исходное сообщение (edit_message_text + InlineKeyboardMarkup), не показывать «Пока нет отчёта…»

**Критерии приёмки:**
- Пользователь не может выбрать несколько независимых тестов и получить мусор
- FSM разрешает ровно один путь, кнопка «Отчёт» неактивна пока не собраны все поля
- Нет сообщений «Пока нет отчёта» после нажатия «Сформировать отчёт»

### Эпик B — Единое меню и UX

**Требования:**
- Меню по макету: Главный экран: [Палитрометр — мой идеальный цвет] [Диагностика кожи PRO] и снизу ⓘ О боте | 🛒 Моя подборка | ⚙️ Настройки
- Убрать дубли («Пройти анкету», «Тесты кожи», «Мои рекомендации» и т.д.)
- Добавить заглушку-лоадер при сборке отчёта и чёткие тосты-уведомления об ошибках

### Эпик C — Движок подбора и интеграция с каталогом

**1) Схема данных (pydantic v2)**

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Literal, List, Optional

Undertone = Literal["cool","warm","neutral","olive"]
Finish = Literal["matte","natural","dewy","satin","shimmer"]

class Shade(BaseModel):
    name: str
    code: Optional[str] = None
    undertone: Optional[Undertone] = None
    color_family: Optional[str] = None

class Product(BaseModel):
    id: str
    brand: str
    line: Optional[str] = None
    name: str
    category: str
    subcategory: Optional[str] = None
    texture: Optional[str] = None
    finish: Optional[Finish] = None
    shade: Optional[Shade] = None
    volume_ml: Optional[float] = None
    weight_g: Optional[float] = None
    spf: Optional[int] = None
    actives: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    price: Optional[float] = None
    price_currency: Optional[str] = None
    link: Optional[HttpUrl] = None
    in_stock: Optional[bool] = None
    source: Optional[str] = None

class UserProfile(BaseModel):
    undertone: Optional[Undertone] = None
    season: Optional[str] = None
    season_subtype: Optional[str] = None
    value: Optional[str] = None
    chroma: Optional[str] = None
    contrast: Optional[str] = None
    eye_color: Optional[str] = None
    hair_depth: Optional[str] = None
    skin_type: Optional[Literal["dry","oily","combo","sensitive","normal"]] = None
    concerns: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
```

**2) Загрузка каталога (ruamel.yaml + валидация)**

```python
from ruamel.yaml import YAML
from pydantic import ValidationError

def load_catalog(path: str) -> list[Product]:
    yaml = YAML(typ="rt")
    data = yaml.load(open(path, "r", encoding="utf-8"))
    items = data.get("products", [])
    out: list[Product] = []
    for raw in items:
        try:
            out.append(Product.model_validate(raw))
        except ValidationError:
            # логировать и продолжить
            pass
    return out
```

**3) Функция подбора (ядро):**

```python
from .models import UserProfile, Product

def select_products(user_profile: UserProfile, catalog: list[Product], partner_code: str, redirect_base: str | None = None) -> dict:
    return {"skincare": {...}, "makeup": {...}}
```

### Эпик D — Интеграция: «как это внедрим»

**Требования:**
- Загружать `fixed_catalog.yaml` из `data/` (или S3; путь в ENV `CATALOG_PATH`)
- По завершении потока A или B формировать `UserProfile` и вызывать `select_products(...)`
- Рендерить сообщение c `InlineKeyboardMarkup` и кнопками «Купить» (с партнёрским кодом/редиректом)
- Сохранять профиль и рекомендации в БД по `user_id` (sqlite/postgres)

**Пример кода:**
```python
from engine.catalog import load_catalog
from engine.models import UserProfile
from engine.selector import select_products

catalog = load_catalog(os.getenv("CATALOG_PATH", "data/fixed_catalog.yaml"))
result = select_products(
    user_profile=UserProfile(**profile_dict),
    catalog=catalog,
    partner_code=os.getenv("PARTNER_CODE", "aff_123"),
    redirect_base=os.getenv("REDIRECT_BASE")
)
```

### Эпик E — Производительность каталога (кеш + hot-reload)

**Требования:**
- Процесс‑глобальный кеш `CatalogStore` (потокобезопасный), загрузка 1 раз и hot‑reload при изменении файла (по сигнатуре `size+mtime`)
- На старте бота — прелоад кеш. В хендлерах — брать каталог из кеша

### Эпик F — JSONL‑логгинг ValidationError + ротация

**Требования:**
- Все ошибки валидации из `load_catalog` пишутся в `logs/catalog_errors.jsonl` (RotatingFileHandler)
- Формат одной строки — JSON с `ts, level, msg, payload{index,id,errors,...}`

### Эпик G — Бэкап перед правкой каталога

**Требования:**
- Перед любыми изменениями `catalog_user.yaml` создавать бэкап `*.bak` через `shutil.copy2`
- По желанию: писать diff в `logs/catalog_diff.patch` через `difflib.unified_diff`

---

## 🏗️ СТРУКТУРА ПРОЕКТА

```
/bot
  main.py
  handlers/
    start.py
    flow_palette.py      # A*
    flow_skincare.py     # B*
  ui/
    keyboards.py
    render.py            # форматирование отчётов
/engine
  models.py
  catalog.py
  selector.py
/tools
  catalog_lint_fix.py
  demo_user_profile.py
configs/
  config.example.toml
data/
  fixed_catalog.yaml     # загружаем сюда
```

---

## 🔧 ИСПРАВЛЕНИЯ КОНКРЕТНЫХ ПРОБЛЕМ

- **FSM:** запрет параллельных веток; кнопка «Сформировать отчёт» активна только при полном профиле
- **UX:** убрать «Пока нет отчёта…», добавить лоадер и `edit_message_text` с результатом
- **Рендер:** AM/PM/Weekly и Макияж (Лицо/Брови/Глаза/Губы) с кликабельными ссылками
- **Меню:** единообразие кнопок по макету
- **Техсбои:** унификация обработки `CallbackQuery`, тайм‑ауты, защита от двойных кликов, явные переходы состояний; логирование исключений и неожиданных `callback_data`

---

## 🧪 ТЕСТИРОВАНИЕ

### Юнит‑ и интеграционные тесты (pytest)

- **FSM:** happy‑path и прерывание/возврат
- **Валидация YAML:** `load_catalog` на «плохом» и «починенном» файле
- **`select_products`:** моки каталога → проверка, что слоты заполнены ≥1 SKU
- **Snapshot‑тест** форматирования сообщений

### Готовность к релизу (DoD)

- `make test` зелёный, `ruff`/`mypy` чисто
- `fixed_catalog.yaml` валиден, нет «other» и «1000 руб»
- В демо‑боте: прохожу A или B → получаю отчёт и кликаю «Купить»

---

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
CATALOG_PATH=data/fixed_catalog.yaml
PARTNER_CODE=aff_123
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
railway variables set CATALOG_PATH=data/fixed_catalog.yaml
railway variables set PARTNER_CODE=aff_123
```

3. **Деплой:**
```bash
railway up
```

---

## 📊 Мониторинг и логи

### Логирование
- Подробные логи загрузки каталога
- Статистика рекомендаций
- Отслеживание ошибок

### Метрики
- Количество загруженных товаров
- Фильтрация по наличию
- Статистика замен

---

## 🔄 CI/CD

### GitHub Actions
- Автоматическое тестирование
- Линтинг кода (black, ruff)
- Деплой на Railway

### Railway
- Автоматический деплой из main ветки
- Управление переменными окружения
- Мониторинг приложения

---

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

---

## 📞 Поддержка

- **Сайт:** stasya-makeuphair.ru
- **Автор:** Стасья Цуняк
- **Разработчик:** Ларин Р.Р. (@MagnatMark)

## 📄 Лицензия

Проект разработан для персонального использования.

---

## 📚 Источники

- Telegram Bot API
- Aiogram FSM
- Pydantic v2
- ruamel.yaml
- ISO 4217


# Test commit for auto-deploy
