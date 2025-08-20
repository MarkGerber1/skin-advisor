СОЗДАЙ README файл и весь промпт скопируй туда, оттуда будешь выдергивать информацию и делать пока все не выполнишь, и не предоставишь отчет!

Роль: ты — ведущий Python-инженер и продуктовый разработчик. Стек: Python 3.11, aiogram v3 (FSM), pydantic v2, ruamel.yaml, docker-compose. Цель — исправить логику бота и интегрировать движок подбора с валидным каталогом fixed_catalog.yaml.

## 1) Что нужно сделать (эпики)

### Эпик A — Последовательная логика диагностики (FSM), без параллельных тестов

- Реализуй один активный поток за раз. Сначала базовый тип кожи (dry/oily/combo/sensitive/normal), затем состояния (sensitivity, dehydration, acne и т. д.).
- Никаких «одновременных» тестов. Кнопка «Сформировать отчёт» активируется только после прохождения всех обязательных шагов.
- Используй aiogram FSM: состояния `B1_TYPE → B2_CONCERNS → B3_CONFIRM → B4_REPORT`. Для палитры — `A1_UNDERTONE → A2_VALUE → A3_HAIR → A4_BROWS → A5_EYES → A6_CONTRAST → A7_REPORT`.
- CallbackQuery обрабатывай централизованно, проверяй шаблон callback_data (prefix+step+field+value) и гаси «дребезг» двойных кликов (answerCallbackQuery + идемпотентность по message_id/state).
- При генерации отчёта редактируй исходное сообщение (edit_message_text + InlineKeyboardMarkup), не показывай «Пока нет отчёта…».

Критерии приёмки:

- Пользователь не может выбрать несколько независимых тестов и получить мусор.
- FSM разрешает ровно один путь, кнопка «Отчёт» неактивна пока не собраны все поля.
- Нет сообщений «Пока нет отчёта» после нажатия «Сформировать отчёт».

### Эпик B — Единое меню и UX

- Меню по макету: Главный экран: [Палитрометр — мой идеальный цвет] [Диагностика кожи PRO] и снизу ⓘ О боте | 🛒 Моя подборка | ⚙️ Настройки.
- Убери дубли («Пройти анкету», «Тесты кожи», «Мои рекомендации» и т. д.).
- Добавь заглушку-лоадер при сборке отчёта и чёткие тосты-уведомления об ошибках.

### Эпик C — Движок подбора и интеграция с каталогом

1) Схема данных (pydantic v2)

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

2) Загрузка каталога (ruamel.yaml + валидация)

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

3) Функция подбора (ядро):

```python
from .models import UserProfile, Product

def select_products(user_profile: UserProfile, catalog: list[Product], partner_code: str, redirect_base: str | None = None) -> dict:
    return {"skincare": {...}, "makeup": {...}}
```

---

## Δ PATCH (Эпики E–G)

### Эпик E — Производительность каталога (кеш + hot-reload)
- Процесс‑глобальный кеш `CatalogStore` (потокобезопасный), загрузка 1 раз и hot‑reload при изменении файла (по сигнатуре `size+mtime`).
- На старте бота — прелоад кеш. В хендлерах — брать каталог из кеша.

### Эпик F — JSONL‑логгинг ValidationError + ротация
- Все ошибки валидации из `load_catalog` пишутся в `logs/catalog_errors.jsonl` (RotatingFileHandler).
- Формат одной строки — JSON с `ts, level, msg, payload{index,id,errors,...}`.

### Эпик G — Бэкап перед правкой каталога
- Перед любыми изменениями `catalog_user.yaml` создавать бэкап `*.bak` через `shutil.copy2`.
- По желанию: писать diff в `logs/catalog_diff.patch` через `difflib.unified_diff`.

---

## 2) Структура проекта (создать/обновить)

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

## 3) Интеграция: «как это внедрим»

- Загружаем `fixed_catalog.yaml` из `data/` (или S3; путь в ENV `CATALOG_PATH`).
- По завершении потока A или B формируем `UserProfile` и вызываем `select_products(...)`.
- Рендерим сообщение c `InlineKeyboardMarkup` и кнопками «Купить» (с партнёрским кодом/редиректом).
- Сохраняем профиль и рекомендации в БД по `user_id` (sqlite/postgres).

Пример кода:

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

## 4) Исправления конкретных проблем

- FSM: запрет параллельных веток; кнопка «Сформировать отчёт» активна только при полном профиле.
- UX: убрать «Пока нет отчёта…», добавить лоадер и `edit_message_text` с результатом.
- Рендер: AM/PM/Weekly и Макияж (Лицо/Брови/Глаза/Губы) с кликабельными ссылками.
- Меню: единообразие кнопок по макету.
- Техсбои: унификация обработки `CallbackQuery`, тайм‑ауты, защита от двойных кликов, явные переходы состояний; логирование исключений и неожиданных `callback_data`.

## 5) Юнит‑ и интеграционные тесты (pytest)

- FSM: happy‑path и прерывание/возврат.
- Валидация YAML: `load_catalog` на «плохом» и «починенном» файле.
- `select_products`: моки каталога → проверка, что слоты заполнены ≥1 SKU.
- Snapshot‑тест форматирования сообщений.

## 6) Готовность к релизу (DoD)

- `make test` зелёный, `ruff`/`mypy` чисто.
- `fixed_catalog.yaml` валиден, нет «other» и «1000 руб».
- В демо‑боте: прохожу A или B → получаю отчёт и кликаю «Купить».

---

### Источники
- Telegram Bot API
- Aiogram FSM
- Pydantic v2
- ruamel.yaml
- ISO 4217
```


