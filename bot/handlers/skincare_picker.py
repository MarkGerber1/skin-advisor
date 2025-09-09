"""
🛍️ Инлайн-подбор ухода после теста "Портрет лица"
Категории → Товары → Варианты → Корзина с приоритизацией источников
"""
from __future__ import annotations

import os
from typing import List, Dict, Optional, Tuple
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Fix imports for engine modules
try:
    from engine.catalog_store import CatalogStore
    from engine.models import Product
    from engine.selector import SelectorV2
    from engine.selector_schema import canon_slug, safe_get_skincare_data
    from engine.affiliate_validator import AffiliateManager
    from engine.ab_testing import get_ab_testing_framework
    from services.affiliates import build_ref_link
except ImportError:
    print("CRITICAL: Failed to import engine modules, using fallback")
    # Define fallback classes
    class CatalogStore:
        @staticmethod
        def instance(*args):
            return None
    class Product:
        pass
    class SelectorV2:
        pass
    class AffiliateManager:
        def add_affiliate_params(self, url, source, campaign=None):
            return url
        def track_checkout_click(self, *args, **kwargs):
            pass
        def track_external_checkout_opened(self, *args, **kwargs):
            pass
    class ABTestingFramework:
        def log_button_click(self, *args, **kwargs):
            pass
        def log_test_completion(self, *args, **kwargs):
            pass
        def log_add_to_cart(self, *args, **kwargs):
            pass
        def get_category_order_variant(self, user_id):
            return ["cleanser", "toner", "serum", "moisturizer", "eye_care", "sunscreen", "mask"]

        @staticmethod
        def emit_analytics(*args, **kwargs):
            pass

    # Fallback functions for schema
    def canon_slug(slug: str) -> str:
        return slug

    def safe_get_skincare_data(data: Dict, slug: str) -> List:
        if not data or not isinstance(data, dict):
            return []
        return data.get(slug, [])

# Fix import for Railway environment
import sys
import os

# Add project root to sys.path for Railway compatibility
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

# Try multiple possible paths for Railway
possible_paths = [
    project_root,  # Local development
    '/usr/src/app',  # Railway production
    os.path.dirname(project_root),  # Fallback
]

for path in possible_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        print(f"Added to sys.path: {path}")

# Define category constants outside try/except (канонические слаги)
CAT_CLEANSE = "cleanser"
CAT_TONE = "toner"
CAT_SERUM = "serum"
CAT_MOIST = "moisturizer"
CAT_EYE = "eye_care"
CAT_SPF = "sunscreen"
CAT_MASK = "mask"

# Define UI category names outside try/except
CATEGORY_CLEANSER = "Очищение"
CATEGORY_TONER = "Тонизирование"
CATEGORY_SERUM = "Сыворотки"
CATEGORY_MOISTURIZER = "Увлажнение"
CATEGORY_EYE_CARE = "Зона вокруг глаз"
CATEGORY_SUN_PROTECTION = "Солнцезащита"
CATEGORY_MASK = "Снятие макияжа"

# Alias map для категорий - маппинг входных слагов к списку алиасов для поиска
CATEGORY_ALIAS_MAP = {
    "cleanser": ["очищение", "гель для умывания", "пенка", "мицеллярная вода", "мусс", "cleanser", "cleanse", "очищающее средство"],
    "toner": ["тоник", "софтнер", "пилинг", "пилинг-пэды", "пилинг-скатка", "toner", "toning", "тонизирование"],
    "serum": ["сыворотка", "serum"],
    "moisturizer": ["крем", "эмульсия", "гель", "флюид", "масло", "moisturizer", "moisturizing", "увлажнение"],
    "eye_care": ["крем для глаз", "зона вокруг глаз", "eye cream", "eye_care", "глаза", "под глазами"],
    "sunscreen": ["солнцезащита", "spf", "spf крем", "флюид spf", "стик spf", "sunscreen", "sun_protection"],
    "mask": ["маска", "mask", "masks", "снятие макияжа", "makeup_remover"]
}

try:
    from i18n.ru import *
except ImportError:
    # Fallback: try to import directly
    try:
        import i18n.ru as i18n_module
        # Copy all attributes from i18n.ru to current namespace
        import inspect
        current_module = inspect.currentframe().f_globals
        for name in dir(i18n_module):
            if not name.startswith('_'):
                current_module[name] = getattr(i18n_module, name)
    except ImportError as e:
        print(f"CRITICAL: Failed to import i18n.ru: {e}")
        # Define minimal fallback constants
        HEAD_SKINCARE_PICK = "Подборка ухода по результатам"
        SUB_PICK = "Выберите категорию, затем добавьте средства в корзину"

        # Button constants (fallback)
        BTN_CLEANSE = "Очищение"
        BTN_TONE = "Тонизирование"
        BTN_SERUM = "Сыворотки"
        BTN_MOIST = "Увлажнение"
        BTN_EYE = "Зона вокруг глаз"
        BTN_SPF = "Солнцезащита"
        BTN_REMOVER = "Снятие макияжа"
        BTN_CHOOSE_VARIANT = "Выбрать вариант"
        BTN_ADD_TO_CART = "Добавить в корзину"
        BTN_IN_CART = "✓ В корзине"

        # Category constants (already defined above)

        # UI category names (already defined above)
        MSG_ADDED = "Добавлено в корзину: {item}"

        # Display names for categories
        CAT_DISPLAY_NAMES = {
            "cleanser": "Очищение",
            "toner": "Тонизирование",
            "serum": "Сыворотки",
            "moisturizer": "Увлажнение",
            "eye_cream": "Уход за глазами",
            "sunscreen": "Солнцезащита",
            "mask": "Маски"
        }
        MSG_VARIANT_ADDED = "Добавлено в корзину: {brand} {name} ({variant})"
        BADGE_OOS = "Нет в наличии"
        BTN_SHOW_ALTS = "Показать альтернативы"

# Fix import for cart module
try:
    from engine.cart_store import CartStore
    cart_service_available = True
except ImportError:
    print("CRITICAL: Failed to import CartStore, using fallback")
    cart_service_available = False
    class CartStore:
        pass
        # Define fallback functions
        def get_cart_service():
            return None
        class CartServiceError(Exception):
            pass

# Analytics import with fallback
try:
    from engine.analytics import (
        get_analytics_tracker,
        track_skincare_recommendations_viewed,
        track_category_opened,
        track_product_opened,
        track_variant_selected,
        track_oos_shown,
        track_alternatives_shown,
        track_skincare_error,
        track_cart_event
    )
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    def get_analytics_tracker():
        return None
    # Stub functions for fallback
    def track_skincare_recommendations_viewed(*args, **kwargs): pass
    def track_category_opened(*args, **kwargs): pass
    def track_product_opened(*args, **kwargs): pass
    def track_variant_selected(*args, **kwargs): pass
    def track_oos_shown(*args, **kwargs): pass
    def track_alternatives_shown(*args, **kwargs): pass
    def track_skincare_error(*args, **kwargs): pass
    def track_cart_event(*args, **kwargs): pass

router = Router()

# Инициализация affiliate менеджера
try:
    affiliate_manager = AffiliateManager()
except:
    affiliate_manager = AffiliateManager()  # fallback

# Инициализация A/B testing framework
try:
    ab_framework = get_ab_testing_framework()
except:
    ab_framework = ABTestingFramework()  # fallback

# Маппинг категорий на их слаги
CATEGORY_MAPPING = {
    CAT_CLEANSE: CATEGORY_CLEANSER,
    CAT_TONE: CATEGORY_TONER,
    CAT_SERUM: CATEGORY_SERUM,
    CAT_MOIST: CATEGORY_MOISTURIZER,
    CAT_EYE: CATEGORY_EYE_CARE,
    CAT_SPF: CATEGORY_SUN_PROTECTION,
    CAT_MASK: CATEGORY_MASK
}

# Обратный маппинг для поиска товаров по категориям (теперь канонические)
CATEGORY_TO_ENGINE = {
    CAT_CLEANSE: "cleanser",
    CAT_TONE: "toner",
    CAT_SERUM: "serum",
    CAT_MOIST: "moisturizer",
    CAT_EYE: "eye_care",
    CAT_SPF: "sunscreen",
    CAT_MASK: "mask"
}


def _format_price(product: Dict) -> str:
    """Форматирование цены с валютой"""
    price = product.get("price", 0)
    currency = product.get("currency", "RUB")

    if currency in ("RUB", "₽"):
        return f"{int(price)} ₽"
    elif currency == "USD":
        return f"${price:.0f}"
    elif currency == "EUR":
        return f"€{price:.0f}"
    else:
        return f"{int(price)} {currency}"


def _format_source_info(product: Dict) -> str:
    """Форматирование информации об источнике"""
    source_name = product.get("source_name", "")
    price_text = _format_price(product)

    if source_name == "goldapple.ru":
        return f"({SRC_GOLDAPPLE} · {price_text})"
    elif any(domain in source_name for domain in ["sephora.ru", "letu.ru", "rive-gauche.ru"]):
        return f"({SRC_RU_OFFICIAL} · {price_text})"
    elif any(domain in source_name for domain in ["wildberries.ru", "ozon.ru", "yandex.market.ru"]):
        return f"({SRC_RU_MP} · {price_text})"
    else:
        return f"({SRC_INTL} · {price_text})"


def _resolve_product_source(product: Dict) -> Dict:
    """Разрешение источника товара с приоритизацией"""
    # В будущем здесь будет логика source_resolver
    # Пока возвращаем товар как есть
    return product


def _get_products_by_category(user_id: int, category_slug: str, page: int = 1) -> Tuple[List[Dict], int]:
    """Получить товары по категории с пагинацией"""
    try:
        # Нормализуем слаг к каноническому виду
        canonical_slug = canon_slug(category_slug)
        print(f"🔍 Looking for category '{category_slug}' → canonical '{canonical_slug}'")

        # Получаем сохраненный профиль пользователя
        from bot.handlers.user_profile_store import get_user_profile_store
        profile_store = get_user_profile_store()
        user_profile = profile_store.load_profile(user_id)

        if not user_profile:
            print(f"⚠️ No profile found for user {user_id}")
            return [], 0

        # Получаем каталог
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()

        if not catalog:
            print("⚠️ Catalog not loaded")
            return [], 0

        # Используем SelectorV2 для получения рекомендаций
        selector = SelectorV2()
        result = selector.select_products_v2(
            profile=user_profile,
            catalog=catalog,
            partner_code="S1"
        )

        if not result:
            print("⚠️ No results from selector")
            return [], 0

        # Безопасно извлекаем данные по каноническому слагу
        category_products = safe_get_skincare_data(result.get("skincare"), canonical_slug)

        if not category_products:
            print(f"⚠️ No products found for canonical category '{canonical_slug}' (original: '{category_slug}')")
            print(f"   Available categories: {list(result.get('skincare', {}).keys())}")
            return [], 0

        print(f"✅ Found {len(category_products)} products for category '{canonical_slug}'")

        # Приоритизация источников и разрешение
        resolved_products = []
        for product in category_products:
            resolved = _resolve_product_source(product)
            if resolved:
                resolved_products.append(resolved)

        if not resolved_products:
            print(f"⚠️ No resolved products for category '{canonical_slug}'")
            return [], 0

        # Пагинация (8 товаров на страницу)
        per_page = 8
        total_pages = (len(resolved_products) + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        page_products = resolved_products[start_idx:end_idx]

        return page_products, total_pages

    except Exception as e:
        print(f"❌ Error getting products for category {category_slug}: {e}")
        import traceback
        traceback.print_exc()
        return [], 0


# Theme switcher
@router.message(F.text == "/theme")
async def switch_theme(message: Message) -> None:
    """Переключатель тем (светлая/темная)"""
    user_id = message.from_user.id if message.from_user else 0

    # Имитируем переключение темы (в реальности нужно хранить в БД)
    current_theme = "light"  # В реальности брать из user preferences

    if current_theme == "light":
        new_theme = "dark"
        theme_name = "темную"
    else:
        new_theme = "light"
        theme_name = "светлую"

    # Сохранить новую тему для пользователя (в будущем)
    # await save_user_theme(user_id, new_theme)

    await message.answer(
        f"🌙 Тема переключена на {theme_name}!\n\n"
        f"Используйте команду снова для переключения.",
        reply_markup=None
    )

@router.callback_query(F.data == "skincare_picker:start")
async def start_skincare_picker(cb: CallbackQuery, state: FSMContext) -> None:
    """Запуск подбора ухода после теста"""
    try:
        user_id = cb.from_user.id

        # Аналитика
        track_skincare_recommendations_viewed(user_id)

        # A/B testing: логируем клик по кнопке (будет обновлено после определения категорий)

        # Получаем доступные категории из результатов теста
        data = await state.get_data()
        skin_analysis = data.get("skin_analysis", {})
        skin_type = skin_analysis.get("type", "normal")
        concerns = skin_analysis.get("concerns", [])

        # A/B testing: получаем порядок категорий для пользователя
        category_order = ab_framework.get_category_order_variant(user_id)

        # Определяем релевантные категории на основе типа кожи и проблем
        base_categories = [
            (CAT_CLEANSE, BTN_CLEANSE),
            (CAT_TONE, BTN_TONE),
            (CAT_SERUM, BTN_SERUM),
            (CAT_MOIST, BTN_MOIST)
        ]

        # Добавляем специфические категории
        additional_categories = []
        if any(concern in ["aging", "dark_circles", "puffiness"] for concern in concerns):
            additional_categories.append((CAT_EYE, BTN_EYE))

        if any(concern in ["pigmentation", "sun_damage"] for concern in concerns):
            additional_categories.append((CAT_SPF, BTN_SPF))

        # Объединяем все категории
        all_categories = base_categories + additional_categories

        # A/B testing: сортируем категории согласно варианту
        available_categories = []
        for cat_slug in category_order:
            for cat_tuple in all_categories:
                if cat_tuple[0] == cat_slug:
                    available_categories.append(cat_tuple)
                    break

        # Маски всегда доступны
        available_categories.append((CAT_MASK, BTN_REMOVER))

        # A/B testing: логируем клик по кнопке с количеством категорий
        ab_framework.log_button_click(user_id, "category_order_experiment", len(available_categories))

        # Создаем клавиатуру с категориями
        buttons = []
        for slug, name in available_categories:
            buttons.append([InlineKeyboardButton(
                text=name,
                callback_data=f"c:cat:{slug}"
            )])

        # Добавляем кнопки навигации
        buttons.append([
            InlineKeyboardButton(text=BTN_BACK, callback_data="back:skincare_results"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")
        ])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await cb.message.edit_text(
            f"🛍️ **{HEAD_SKINCARE_PICK}**\n\n"
            f"{SUB_PICK}\n\n"
            f"**Ваш тип кожи:** {skin_type}\n"
            f"**Основные проблемы:** {', '.join(concerns[:3]) if concerns else 'Нет специфических проблем'}",
            reply_markup=kb
        )

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in start_skincare_picker: {e}")
        await cb.answer("⚠️ Ошибка при запуске подбора")


@router.callback_query(F.data.startswith("c:cat:"))
async def show_category_products(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать товары в выбранной категории"""
    try:
        # Парсим callback
        parts = cb.data.split(":")
        if len(parts) < 3:
            await cb.answer("❌ Неверный формат")
            return

        category_slug = parts[2]
        page = 1

        # Если указана страница
        if len(parts) > 3 and parts[3].startswith("p"):
            try:
                page = int(parts[3][1:])
            except ValueError:
                page = 1

        user_id = cb.from_user.id

        # Аналитика
        track_category_opened(user_id, category_slug)

        # Получаем товары категории
        products, total_pages = _get_products_by_category(user_id, category_slug, page)

        if not products:
            # Нет товаров в категории - показываем альтернативы
            category_name = CATEGORY_MAPPING.get(category_slug, category_slug)

            # Находим альтернативные категории
            alternative_buttons = []
            try:
                from bot.handlers.user_profile_store import get_user_profile_store
                profile_store = get_user_profile_store()
                user_profile = profile_store.load_profile(user_id)

                if user_profile:
                    # Получаем все доступные категории из профиля
                    catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
                    catalog_store = CatalogStore.instance(catalog_path)
                    catalog = catalog_store.get()

                    selector = SelectorV2()
                    result = selector.select_products_v2(
                        profile=user_profile,
                        catalog=catalog,
                        partner_code="S1"
                    )

                    skincare_data = result.get("skincare", {})

                    # Добавляем кнопки альтернативных категорий с товарами
                    for alt_slug, alt_name in CATEGORY_MAPPING.items():
                        if alt_slug != category_slug:
                            # Используем канонические слаги для поиска
                            alt_canonical = canon_slug(alt_slug)
                            alt_products = safe_get_skincare_data(skincare_data, alt_canonical)
                            if alt_products:  # Только если есть товары
                                alternative_buttons.append([
                                    InlineKeyboardButton(
                                        text=f"🔄 {alt_name}",
                                        callback_data=f"c:cat:{alt_slug}"
                                    )
                                ])
            except Exception as e:
                print(f"⚠️ Error loading alternatives: {e}")

            # Создаем клавиатуру
            buttons = alternative_buttons + [
                [InlineKeyboardButton(text=BTN_BACK, callback_data="c:back:categories")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
            ]

            kb = InlineKeyboardMarkup(inline_keyboard=buttons)

            message_text = (
                f"😔 **{category_name}**\n\n"
                f"К сожалению, подходящие продукты в этой категории сейчас недоступны.\n\n"
            )

            if alternative_buttons:
                message_text += "**Попробуйте альтернативы:**\n"
            else:
                message_text += "Попробуйте другие категории или вернитесь позже."

            await cb.message.edit_text(message_text, reply_markup=kb)
            await cb.answer("Категория пуста")
            return

        # Создаем список товаров
        text_lines = [f"🛍️ **{CATEGORY_MAPPING.get(category_slug, category_slug)}**"]

        if total_pages > 1:
            text_lines.append(f"Страница {page}/{total_pages}")

        text_lines.append("")

        buttons = []

        for i, product in enumerate(products, 1):
            # Форматируем строку товара
            brand = product.get("brand", "")
            name = product.get("name", "")
            source_info = _format_source_info(product)

            text_lines.append(f"{i}. {brand} {name}")
            text_lines.append(f"   {source_info}")

            # Проверяем наличие товара
            in_stock = product.get("in_stock", True)
            has_variants = len(product.get("variants", [])) > 1

            # Создаем кнопки для товара
            if in_stock:
                if has_variants:
                    # Товар с вариантами
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"📦 Выбрать {i}",
                            callback_data=f"c:prd:{product.get('id', '')}"
                        )
                    ])
                else:
                    # Товар без вариантов - сразу добавить в корзину
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"➕ Добавить {i}",
                            callback_data=f"c:add:{product.get('id', '')}:default"
                        )
                    ])
            else:
                # Товар не в наличии
                buttons.append([
                    InlineKeyboardButton(
                        text=f"❌ Нет в наличии {i}",
                        callback_data=f"c:oos:{product.get('id', '')}"
                    )
                ])

            text_lines.append("")

        # Навигация по страницам
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text=BTN_PREV,
                callback_data=f"c:cat:{category_slug}:p{page-1}"
            ))

        nav_buttons.append(InlineKeyboardButton(
            text=BTN_BACK,
            callback_data="skincare_result:products"
        ))

        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text=BTN_NEXT,
                callback_data=f"c:cat:{category_slug}:p{page+1}"
            ))

        buttons.append(nav_buttons)

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await cb.message.edit_text("\n".join(text_lines), reply_markup=kb)
        await cb.answer()

    except Exception as e:
        print(f"❌ Error in show_category_products: {e}")
        await cb.answer("⚠️ Ошибка при показе товаров")


@router.callback_query(F.data.startswith("c:prd:"))
async def show_product_variants(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать варианты товара"""
    try:
        # Парсим callback
        parts = cb.data.split(":")
        if len(parts) < 3:
            await cb.answer("❌ Неверный формат")
            return

        product_id = parts[2]
        user_id = cb.from_user.id

        # Аналитика
        track_product_opened(user_id, product_id, "category_view")

        # Affiliate отслеживание открытия товара
        try:
            affiliate_manager.emit_analytics('product_opened', {
                'pid': product_id,
                'source': 'skincare_picker',
                'user_id': user_id
            })
        except Exception as e:
            print(f"[WARNING] Product open tracking error: {e}")

        # Находим товар (пока используем заглушку, в будущем из каталога)
        # TODO: Получить товар из каталога по ID

        # Создаем варианты товара (заглушка)
        variants = [
            {"id": "variant_30ml", "name": "30 мл", "price": 2500, "in_stock": True},
            {"id": "variant_50ml", "name": "50 мл", "price": 3200, "in_stock": True},
            {"id": "variant_100ml", "name": "100 мл", "price": 4800, "in_stock": False}
        ]

        text_lines = ["📦 **Выберите вариант товара**\n"]
        buttons = []

        for i, variant in enumerate(variants, 1):
            price_text = _format_price({"price": variant["price"], "currency": "RUB"})

            text_lines.append(f"{i}. {variant['name']} • {price_text}")

            if variant["in_stock"]:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"➕ Добавить {i}",
                        callback_data=f"c:add:{product_id}:{variant['id']}"
                    )
                ])
            else:
                text_lines[-1] += f" ({BADGE_OOS})"
                buttons.append([
                    InlineKeyboardButton(
                        text=f"🔄 Альтернативы {i}",
                        callback_data=f"c:alt:{product_id}:{variant['id']}"
                    )
                ])

            text_lines.append("")

        # Кнопка назад
        buttons.append([
            InlineKeyboardButton(text=BTN_BACK, callback_data="c:back:category")
        ])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await cb.message.edit_text("\n".join(text_lines), reply_markup=kb)
        await cb.answer()

    except Exception as e:
        print(f"❌ Error in show_product_variants: {e}")
        await cb.answer("⚠️ Ошибка при показе вариантов")


@router.callback_query(F.data.startswith("c:add:"))
async def add_product_to_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Добавить товар в корзину"""
    try:
        # Парсим callback
        parts = cb.data.split(":")
        if len(parts) < 4:
            await cb.answer("❌ Неверный формат")
            return

        product_id = parts[2]
        variant_id = parts[3] if parts[3] != "default" else None
        user_id = cb.from_user.id

        # Проверяем доступность сервиса корзины
        if not cart_service_available:
            await cb.answer(MSG_ADD_FAILED)
            return

        try:
            cart_store = store  # Используем унифицированный store
            # Находим продукт для генерации партнерской ссылки
            product_data = None
            try:
                selector = SelectorV2()
                products = selector.select_products(user_id, category="all", limit=100)
                for prod in products:
                    if str(prod.get('id', '')) == product_id:
                        product_data = prod
                        break
            except Exception as e:
                print(f"Warning: Could not find product data for {product_id}: {e}")

            # Генерируем партнерскую ссылку
            ref_link = None
            if product_data:
                try:
                    ref_link = build_ref_link(product_data, "skincare_recommendation")
                except Exception as e:
                    print(f"Warning: Could not generate affiliate link: {e}")

            # Добавляем товар в корзину
            cart_item = cart_store.add_item(
                user_id=user_id,
                product_id=product_id,
                variant_id=variant_id,
                qty=1,
                ref_link=ref_link
            )

            # Аналитика
            track_cart_event("product_added_to_cart", user_id,
                pid=product_id,
                vid=variant_id or "default",
                source=cart_item.ref_link or "unknown",
                price=cart_item.price,
                category=cart_item.category
            )

            # Affiliate отслеживание
            try:
                # Определяем источник по ref_link
                source = "unknown"
                if cart_item.ref_link:
                    if "goldapple" in cart_item.ref_link.lower():
                        source = "goldapple"
                    elif "wildberries" in cart_item.ref_link.lower() or "marketplace" in cart_item.ref_link.lower():
                        source = "ru_marketplace"
                    elif "official" in cart_item.ref_link.lower():
                        source = "ru_official"
                    elif "amazon" in cart_item.ref_link.lower() or "sephora" in cart_item.ref_link.lower():
                        source = "intl_authorized"

                # Отслеживаем клик по checkout
                affiliate_manager.track_checkout_click(
                    items_count=1,
                    total=float(cart_item.price) if cart_item.price else 0,
                    currency='RUB',
                    source=source,
                    product_ids=[product_id]
                )

                # Отслеживаем открытие внешнего checkout
                if cart_item.ref_link:
                    affiliate_manager.track_external_checkout_opened(
                        partner=source.title(),
                        url=cart_item.ref_link,
                        items_count=1
                    )

            except Exception as e:
                print(f"[WARNING] Affiliate tracking error: {e}")

            # A/B testing: логируем добавление в корзину
            try:
                ab_framework.log_add_to_cart(user_id, "category_order_experiment", 1)
            except Exception as e:
                print(f"[WARNING] A/B tracking error: {e}")

            # Формируем сообщение об успехе
            variant_text = f" ({cart_item.variant_name})" if cart_item.variant_name else ""
            item_name = f"{cart_item.brand or ''} {cart_item.name or ''}".strip()
            message = MSG_VARIANT_ADDED.format(
                brand=cart_item.brand or "",
                name=cart_item.name or "",
                variant=cart_item.variant_name or "стандарт"
            )

            await cb.answer(message, show_alert=True)

            # Обновляем кнопку на "✓ В корзине"
            # TODO: Обновить кнопку в интерфейсе

        except CartServiceError as e:
            print(f"❌ Cart service error: {e}")
            await cb.answer(MSG_ADD_FAILED)

            # Аналитика ошибки
            track_skincare_error(user_id, e.code.value if hasattr(e, 'code') else "unknown", "cart_add")

    except Exception as e:
        print(f"❌ Unexpected error in add_product_to_cart: {e}")
        await cb.answer(MSG_ADD_FAILED)


@router.callback_query(F.data.startswith("c:oos:"))
async def show_out_of_stock_alternatives(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать альтернативы для недоступного товара"""
    try:
        # Парсим callback
        parts = cb.data.split(":")
        if len(parts) < 3:
            await cb.answer("❌ Неверный формат")
            return

        product_id = parts[2]
        user_id = cb.from_user.id

        # Аналитика
        if ANALYTICS_AVAILABLE:
            analytics = get_analytics_tracker()
            analytics.track_event("oos_shown", user_id, {"pid": product_id})

        # TODO: Найти альтернативы в той же категории и ценовой группе

        # Заглушка с альтернативными товарами
        alternatives = [
            {"id": "alt_1", "name": "Альтернатива 1", "brand": "Brand A", "price": 2200},
            {"id": "alt_2", "name": "Альтернатива 2", "brand": "Brand B", "price": 2400},
            {"id": "alt_3", "name": "Альтернатива 3", "brand": "Brand C", "price": 2100}
        ]

        text_lines = [f"🔄 **Альтернативы для товара**\n"]
        buttons = []

        for i, alt in enumerate(alternatives, 1):
            price_text = _format_price({"price": alt["price"], "currency": "RUB"})
            text_lines.append(f"{i}. {alt['brand']} {alt['name']} • {price_text}")

            buttons.append([
                InlineKeyboardButton(
                    text=f"➕ Добавить {i}",
                    callback_data=f"c:add:{alt['id']}:default"
                )
            ])

            text_lines.append("")

        buttons.append([
            InlineKeyboardButton(text=BTN_BACK, callback_data="c:back:category")
        ])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await cb.message.edit_text("\n".join(text_lines), reply_markup=kb)

        # Аналитика показа альтернатив
        track_alternatives_shown(user_id, product_id, "unknown", len(alternatives))

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in show_out_of_stock_alternatives: {e}")
        await cb.answer("⚠️ Ошибка при показе альтернатив")


@router.callback_query(F.data == "c:back:categories")
async def back_to_categories(cb: CallbackQuery, state: FSMContext) -> None:
    """Вернуться к выбору категорий"""
    await start_skincare_picker(cb, state)


@router.callback_query(F.data == "c:back:category")
async def back_to_category(cb: CallbackQuery, state: FSMContext) -> None:
    """Вернуться к списку товаров категории"""
    # TODO: Восстановить предыдущее состояние категории
    await start_skincare_picker(cb, state)


async def get_user_profile(user_id: int):
    """Получить профиль пользователя"""
    try:
        from bot.handlers.user_profile_store import get_user_profile_store
        store = get_user_profile_store()
        return await store.get_profile(user_id)
    except Exception as e:
        print(f"❌ Error getting user profile: {e}")
        return None


async def get_skincare_recommendations(user_id: int, profile):
    """Получить рекомендации по уходу для пользователя"""
    try:
        if SELECTOR_AVAILABLE:
            # Используем настоящий селектор
            selector = SelectorV2()
            result = selector.select_products_v2(profile, "skincare")
            return result.get("skincare", {})
        else:
            # Фолбэк с тестовыми данными
            return {
                "cleanser": [
                    {"id": "test_cleanser", "brand": "Test Brand", "name": "Test Cleanser", "price": 1500, "currency": "RUB"}
                ],
                "toner": [
                    {"id": "test_toner", "brand": "Test Brand", "name": "Test Toner", "price": 1200, "currency": "RUB"}
                ]
            }
    except Exception as e:
        print(f"❌ Error getting skincare recommendations: {e}")
        return {}


@router.callback_query(F.data == "skincare:show_all")
async def skincare_show_all(cb: CallbackQuery) -> None:
    """Показать полный список всех рекомендаций skincare"""
    try:
        print(f"📋 skincare:show_all callback from user {cb.from_user.id}")

        # Получаем профиль пользователя для персонализации
        user_id = cb.from_user.id
        profile = await get_user_profile(user_id)

        if not profile:
            await cb.answer("⚠️ Профиль не найден. Пожалуйста, пройдите тест заново.")
            return

        # Получаем рекомендации для пользователя
        recommendations = await get_skincare_recommendations(user_id, profile)

        if not recommendations:
            await cb.answer("⚠️ Рекомендации не найдены. Пожалуйста, пройдите тест заново.")
            return

        # Формируем полный список всех товаров
        text_lines = ["🛍️ **Все рекомендации по уходу за кожей**\n"]
        buttons = []

        total_products = 0
        for category, products in recommendations.items():
            if products:
                text_lines.append(f"\n📦 **{CAT_DISPLAY_NAMES.get(category, category.title())}**")
                for product in products:
                    total_products += 1
                    price_text = _format_price(product)
                    text_lines.append(f"• {product['brand']} {product['name']} • {price_text}")

                    # Добавляем кнопку для каждого товара
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"➕ Добавить",
                            callback_data=f"c:add:{product['id']}:default"
                        )
                    ])

        text_lines.append(f"\n📊 Всего товаров: {total_products}")

        # Добавляем кнопки навигации
        buttons.append([
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back:main"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="skincare:show_all")
        ])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await cb.message.edit_text("\n".join(text_lines), reply_markup=kb, parse_mode="Markdown")

        # Аналитика
        if ANALYTICS_AVAILABLE:
            analytics = get_analytics_tracker()
            analytics.track_event("skincare_show_all", user_id, {"total_products": total_products})

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in skincare_show_all: {e}")
        await cb.answer("⚠️ Ошибка при показе полного списка рекомендаций")
