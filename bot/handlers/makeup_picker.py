#!/usr/bin/env python3
"""
Инлайн-подбор декоративной косметики после теста «Тон&Сияние»
Выбор оттенков на основе профиля пользователя, прямое добавление в корзину
"""
import os
import sys
from typing import List, Dict, Optional, Tuple
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Добавляем пути для импорта
possible_paths = [
    os.getcwd(),
    os.path.join(os.getcwd(), "bot"),
    os.path.join(os.getcwd(), "engine"),
    os.path.join(os.getcwd(), "services"),
    os.path.join(os.getcwd(), "i18n")
]
for path in possible_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        print(f"Added to sys.path: {path}")

# Import constants from i18n with fallback
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
        HEAD_MAKEUP_PICK = "Подборка макияжа по результатам"
        SUB_PICK_MAKEUP = "Выберите категорию и оттенки"

        # Button constants (fallback)
        BTN_MAKEUP_TONE = "Тон/BB/CC"
        BTN_MAKEUP_CONCEALER = "Консилер"
        BTN_MAKEUP_CORRECTOR = "Корректор"
        BTN_MAKEUP_POWDER = "Пудра"
        BTN_MAKEUP_BLUSH = "Румяна"
        BTN_MAKEUP_BRONZER = "Бронзер"
        BTN_MAKEUP_CONTOUR = "Скульптор"
        BTN_MAKEUP_HIGHLIGHTER = "Хайлайтер"
        BTN_MAKEUP_BROWS = "Брови"
        BTN_MAKEUP_EYESHADOW = "Тени"
        BTN_MAKEUP_EYELINER = "Лайнер/Карандаш"
        BTN_MAKEUP_MASCARA = "Тушь"
        BTN_MAKEUP_LIPS = "Губы"
        BTN_CHOOSE_SHADE = "Выбрать оттенок"
        BTN_ADD_TO_CART = "Добавить в корзину"
        BTN_IN_CART = "✓ В корзине"
        BADGE_OOS = "Нет в наличии"
        BTN_SHOW_ALTS = "Показать альтернативы"
        MSG_ADDED = "Добавлено в корзину: {item}"
        MSG_VARIANT_ADDED = "Добавлено в корзину: {brand} {name} ({variant})"

        # Category constants
        CAT_TONE = "foundation"
        CAT_CONCEALER = "concealer"
        CAT_CORRECTOR = "corrector"
        CAT_POWDER = "powder"
        CAT_BLUSH = "blush"
        CAT_BRONZER = "bronzer"
        CAT_CONTOUR = "contour"
        CAT_HIGHLIGHTER = "highlighter"
        CAT_BROWS = "brows"
        CAT_EYESHADOW = "eyeshadow"
        CAT_EYELINER = "eyeliner"
        CAT_MASCARA = "mascara"
        CAT_LIPS = "lips"

        # UI category names (sync with i18n)
        CATEGORY_TONE = BTN_MAKEUP_TONE
        CATEGORY_CONCEALER = BTN_MAKEUP_CONCEALER
        CATEGORY_CORRECTOR = BTN_MAKEUP_CORRECTOR
        CATEGORY_POWDER = BTN_MAKEUP_POWDER
        CATEGORY_BLUSH = BTN_MAKEUP_BLUSH
        CATEGORY_BRONZER = BTN_MAKEUP_BRONZER
        CATEGORY_CONTOUR = BTN_MAKEUP_CONTOUR
        CATEGORY_HIGHLIGHTER = BTN_MAKEUP_HIGHLIGHTER
        CATEGORY_BROWS = BTN_MAKEUP_BROWS
        CATEGORY_EYESHADOW = BTN_MAKEUP_EYESHADOW
        CATEGORY_EYELINER = BTN_MAKEUP_EYELINER
        CATEGORY_MASCARA = BTN_MAKEUP_MASCARA
        CATEGORY_LIPS = BTN_MAKEUP_LIPS

# Fix import for services module
try:
    from services.cart_service import get_cart_service, CartServiceError
except ImportError:
    print("⚠️ cart_service not available, using fallback")
    def get_cart_service():
        return None
    class CartServiceError(Exception):
        pass

# Fix import for engine modules
try:
    from engine.catalog_store import CatalogStore
    from engine.models import Product, UserProfile
    from engine.source_resolver import SourceResolver
    from engine.affiliate_validator import AffiliateManager
    ENGINE_AVAILABLE = True

    # Create resolver instance
    resolver = SourceResolver()

    def resolve_source(product):
        """Wrapper function for resolve_source method"""
        try:
            return resolver.resolve_source(product)
        except Exception as e:
            print(f"❌ Error resolving source: {e}")
            return type('ResolvedProduct', (), {
                'source_name': 'Неизвестный магазин',
                'priority': 999,
                'source_type': 'unknown',
                'domain': 'unknown',
                'currency': 'RUB',
                'is_affiliate': False
            })()

except ImportError as e:
    print(f"⚠️ Engine modules not available: {e}")
    ENGINE_AVAILABLE = False

    class CatalogStore:
        @staticmethod
        def instance(*args):
            return None

    class Product:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class UserProfile:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class SourceResolver:
        def resolve_source(self, product):
            return type('ResolvedProduct', (), {
                'source_name': 'Неизвестный магазин',
                'priority': 999,
                'source_type': 'unknown',
                'domain': 'unknown',
                'currency': 'RUB',

    class AffiliateManager:
        def add_affiliate_params(self, url, source, campaign=None):
            return url
        def track_checkout_click(self, *args, **kwargs):
            pass
        def track_external_checkout_opened(self, *args, **kwargs):
            pass
        def get_affiliate_url(self, *args, **kwargs):
            return args[0] if args else ""
        class analytics:
            @staticmethod
            def emit(*args, **kwargs):
                pass
                'is_affiliate': False
            })()

    resolver = SourceResolver()

    def resolve_source(product):
        return resolver.resolve_source(product)

# Analytics import with fallback
try:
    from engine.analytics import (
        get_analytics_tracker,
        track_recommendations_viewed,
        track_category_opened,
        track_product_opened,
        track_shade_selected,
        track_oos_shown,
        track_alternatives_shown,
        track_error,
        track_cart_event
    )
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    def get_analytics_tracker():
        return None
    # Stub functions for fallback
    def track_recommendations_viewed(*args, **kwargs): pass
    def track_category_opened(*args, **kwargs): pass
    def track_product_opened(*args, **kwargs): pass
    def track_shade_selected(*args, **kwargs): pass
    def track_oos_shown(*args, **kwargs): pass
    def track_alternatives_shown(*args, **kwargs): pass
    def track_error(*args, **kwargs): pass
    def track_cart_event(*args, **kwargs): pass

router = Router()

# Инициализация affiliate менеджера
try:
    affiliate_manager = AffiliateManager()
except:
    affiliate_manager = AffiliateManager()  # fallback

# Categories for makeup picker
MAKEUP_CATEGORIES = [
    (CAT_TONE, BTN_MAKEUP_TONE),
    (CAT_CONCEALER, BTN_MAKEUP_CONCEALER),
    (CAT_CORRECTOR, BTN_MAKEUP_CORRECTOR),
    (CAT_POWDER, BTN_MAKEUP_POWDER),
    (CAT_BLUSH, BTN_MAKEUP_BLUSH),
    (CAT_BRONZER, BTN_MAKEUP_BRONZER),
    (CAT_CONTOUR, BTN_MAKEUP_CONTOUR),
    (CAT_HIGHLIGHTER, BTN_MAKEUP_HIGHLIGHTER),
    (CAT_BROWS, BTN_MAKEUP_BROWS),
    (CAT_EYESHADOW, BTN_MAKEUP_EYESHADOW),
    (CAT_EYELINER, BTN_MAKEUP_EYELINER),
    (CAT_MASCARA, BTN_MAKEUP_MASCARA),
    (CAT_LIPS, BTN_MAKEUP_LIPS)
]


def select_shades(profile: UserProfile, product: Product) -> List[Dict]:
    """
    Выбор подходящих оттенков на основе профиля пользователя
    Учитывает сезон, подтон, цвет глаз, волос, контраст
    Возвращает список вариантов в порядке релевантности
    """
    if not ENGINE_AVAILABLE or not profile or not product:
        return []

    try:
        # Извлекаем параметры профиля
        undertone = profile.undertone if hasattr(profile, 'undertone') else 'neutral'
        season = profile.season if hasattr(profile, 'season') else 'neutral'
        eye_color = getattr(profile, 'eye_color', None)
        hair_color = getattr(profile, 'hair_color', '')
        contrast_level = getattr(profile, 'contrast_level', 'medium')
        makeup_style = getattr(profile, 'makeup_style', '')

        # Получаем категорию продукта для специфической логики
        product_category = getattr(product, 'category', '')

        # Расширенная логика маппинга оттенков
        shade_mapping = {
            'foundation': {
                'warm': ['warm beige', 'golden', 'peach', 'honey', 'amber'],
                'cool': ['cool beige', 'ash', 'rose beige', 'porcelain', 'ivory'],
                'neutral': ['neutral beige', 'nude', 'buff', 'taupe', 'sand']
            },
            'blush': {
                'warm': ['peach', 'coral', 'salmon', 'apricot', 'mauve'],
                'cool': ['rose', 'berry', 'dusty rose', 'cool pink', 'plum'],
                'neutral': ['nude', 'dusty mauve', 'soft rose', 'cinnamon']
            },
            'eyeshadow': {
                'warm': ['golden', 'copper', 'bronze', 'taupe', 'cinnamon'],
                'cool': ['charcoal', 'navy', 'emerald', 'violet', 'silver'],
                'neutral': ['brown', 'gray', 'olive', 'beige', 'nude']
            },
            'lipstick': {
                'warm': ['coral', 'peach', 'terracotta', 'cinnamon', 'mauve'],
                'cool': ['berry', 'cool pink', 'plum', 'fuchsia', 'cherry'],
                'neutral': ['nude', 'dusty rose', 'taupe', 'auburn', 'brick']
            },
            'highlighter': {
                'warm': ['golden', 'peach', 'copper', 'champagne'],
                'cool': ['silver', 'rose gold', 'platinum', 'diamond'],
                'neutral': ['beige', 'cream', 'nude', 'bronze']
            }
        }

        # Специфическая логика для цвета глаз
        eye_color_mapping = {
            'blue': ['warm', 'golden', 'copper'],  # Голубые глаза + теплые тона
            'green': ['warm', 'golden', 'emerald'],  # Зеленые глаза + комплементарные
            'brown': ['neutral', 'taupe', 'bronze'],  # Карие глаза + нейтральные
            'gray': ['cool', 'silver', 'charcoal'],  # Серые глаза + холодные
            'hazel': ['warm', 'golden', 'cinnamon']  # Ореховые глаза + теплые
        }

        # Специфическая логика для цвета волос
        hair_color_mapping = {
            'blonde': ['warm', 'golden', 'peach'],  # Светлые волосы + теплые тона
            'brunette': ['neutral', 'taupe', 'auburn'],  # Темные волосы + нейтральные
            'red': ['warm', 'coral', 'cinnamon'],  # Рыжие волосы + теплые тона
            'black': ['cool', 'charcoal', 'navy'],  # Черные волосы + холодные
            'gray': ['cool', 'silver', 'platinum']  # Седые волосы + холодные
        }

        # Логика контраста
        contrast_mapping = {
            'high': ['cool', 'charcoal', 'navy', 'black'],  # Высокий контраст + насыщенные
            'low': ['warm', 'peach', 'beige', 'nude'],  # Низкий контраст + мягкие
            'medium': ['neutral', 'taupe', 'brown', 'rose']  # Средний контраст + сбалансированные
        }

        # Определяем предпочтительные оттенки
        preferred_shades = []

        # Базовые предпочтения по подтону
        base_mapping = shade_mapping.get(product_category, {}).get(undertone, ['nude'])
        preferred_shades.extend(base_mapping)

        # Учитываем цвет глаз
        if eye_color:
            eye_mapping = eye_color_mapping.get(eye_color, [])
            preferred_shades.extend(eye_mapping)

        # Учитываем цвет волос
        if hair_color:
            hair_mapping = hair_color_mapping.get(hair_color.lower(), [])
            preferred_shades.extend(hair_mapping)

        # Учитываем контраст
        contrast_mapping_list = contrast_mapping.get(contrast_level, [])
        preferred_shades.extend(contrast_mapping_list)

        # Удаляем дубликаты и сохраняем порядок
        seen = set()
        preferred_shades = [x for x in preferred_shades if not (x in seen or seen.add(x))]

        # Если предпочтений мало, добавляем базовые
        if len(preferred_shades) < 3:
            preferred_shades.extend(['nude', 'beige', 'neutral'])

        # Фильтруем варианты продукта
        suitable_variants = []
        if hasattr(product, 'variants') and product.variants:
            for variant in product.variants:
                variant_name = getattr(variant, 'name', '').lower()
                variant_type = getattr(variant, 'type', '').lower()
                variant_undertone = getattr(variant, 'undertone', '').lower()

                relevance_score = 0.0

                # Проверяем совпадения с предпочтениями
                for i, shade in enumerate(preferred_shades):
                    weight = 1.0 - (i * 0.1)  # Чем раньше в списке, тем выше вес

                    if shade in variant_name or shade in variant_type or shade in variant_undertone:
                        relevance_score = max(relevance_score, weight)
                        break

                # Дополнительные бонусы
                if undertone and undertone in variant_undertone:
                    relevance_score += 0.3

                if relevance_score > 0:
                    suitable_variants.append({
                        'variant': variant,
                        'relevance_score': min(relevance_score, 1.0)
                    })

        # Если нет точных совпадений, берем первые доступные варианты
        if not suitable_variants and hasattr(product, 'variants') and product.variants:
            for variant in product.variants[:3]:  # Максимум 3 варианта
                suitable_variants.append({
                    'variant': variant,
                    'relevance_score': 0.3
                })

        # Сортируем по релевантности
        suitable_variants.sort(key=lambda x: x['relevance_score'], reverse=True)

        return suitable_variants

    except Exception as e:
        print(f"❌ Error in select_shades: {e}")
        return []


async def get_makeup_products_for_category(category_slug: str, user_profile: Optional[UserProfile] = None) -> Tuple[List[Dict], int]:
    """
    Получить продукты для категории с учетом профиля пользователя
    """
    try:
        if not ENGINE_AVAILABLE:
            print(f"⚠️ Engine not available, returning empty for {category_slug}")
            return [], 0

        # Получаем каталог
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()

        if not catalog:
            print(f"❌ No catalog loaded for {category_slug}")
            return [], 0

        # Фильтруем продукты по категории
        category_products = []
        for product in catalog:
            if hasattr(product, 'category') and product.category == category_slug:
                category_products.append(product)

        if not category_products:
            print(f"❌ No products found for category {category_slug}")
            return [], 0

        # Преобразуем в формат для отображения
        result_products = []
        for product in category_products[:8]:  # Максимум 8 товаров на страницу
            # Выбираем подходящие оттенки
            suitable_shades = select_shades(user_profile, product)

            product_dict = {
                'product_id': getattr(product, 'id', str(id(product))),
                'name': getattr(product, 'name', 'Без названия'),
                'brand': getattr(product, 'brand', 'Бренд'),
                'price': getattr(product, 'price', 0),
                'currency': getattr(product, 'currency', 'RUB'),
                'in_stock': getattr(product, 'in_stock', True),
                'ref_link': getattr(product, 'ref_link', ''),
                'category': category_slug,
                'suitable_shades': suitable_shades,
                'has_variants': len(suitable_shades) > 0
            }
            result_products.append(product_dict)

        return result_products, len(category_products)

    except Exception as e:
        print(f"❌ Error getting makeup products for category {category_slug}: {e}")
        return [], 0


@router.callback_query(F.data == "makeup_picker:start")
async def start_makeup_picker(cb: CallbackQuery, state: FSMContext) -> None:
    """Запуск подбора макияжа после теста"""
    try:
        user_id = cb.from_user.id if cb.from_user else 0

        # Аналитика
        if ANALYTICS_AVAILABLE:
            track_recommendations_viewed(user_id, branch="makeup")

        # Получаем профиль пользователя из состояния
        data = await state.get_data()
        user_profile = None
        if 'profile' in data:
            # Преобразуем dict обратно в UserProfile
            profile_data = data['profile']
            if ENGINE_AVAILABLE:
                from engine.models import UserProfile, Season, Undertone, EyeColor
                user_profile = UserProfile(**profile_data)

        await cb.message.edit_text(
            f"💄 **{HEAD_MAKEUP_PICK}**\n\n"
            f"_{SUB_PICK_MAKEUP}_\n\n"
            f"Выберите категорию средств:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=name, callback_data=f"m:cat:{slug}")]
                for slug, name in MAKEUP_CATEGORIES
            ] + [
                [InlineKeyboardButton(text="◀️ Назад к результатам", callback_data="back:results")]
            ])
        )

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in start_makeup_picker: {e}")
        await cb.answer("⚠️ Ошибка при запуске подбора")


@router.callback_query(F.data.startswith("m:cat:"))
async def show_makeup_category(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать продукты в категории"""
    try:
        # Парсим callback_data: m:cat:<slug> или m:cat:<slug>:p<page>
        data_parts = cb.data.split(":")
        category_slug = data_parts[2]
        page = int(data_parts[3][1:]) if len(data_parts) > 3 and data_parts[3].startswith("p") else 1

        user_id = cb.from_user.id if cb.from_user else 0

        # Аналитика
        if ANALYTICS_AVAILABLE:
            track_category_opened(user_id, category_slug)

        # Получаем профиль пользователя
        data = await state.get_data()
        user_profile = None
        if 'profile' in data and ENGINE_AVAILABLE:
            from engine.models import UserProfile
            user_profile = UserProfile(**data['profile'])

        # Получаем продукты для категории
        products, total_count = await get_makeup_products_for_category(category_slug, user_profile)

        if not products:
            await cb.message.edit_text(
                f"❌ В категории **{dict(MAKEUP_CATEGORIES)[category_slug]}** пока нет подходящих продуктов.\n\n"
                f"Попробуйте выбрать другую категорию:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=name, callback_data=f"m:cat:{slug}")]
                    for slug, name in MAKEUP_CATEGORIES
                ] + [
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="makeup_picker:start")]
                ])
            )
            return

        # Формируем сообщение
        category_name = dict(MAKEUP_CATEGORIES)[category_slug]
        text = f"💄 **{category_name}**\n\n"

        # Пагинация
        items_per_page = 8
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_products = products[start_idx:end_idx]
        total_pages = (total_count + items_per_page - 1) // items_per_page

        # Создаем кнопки для продуктов
        buttons = []
        for i, product in enumerate(page_products, start_idx + 1):
            has_variants = product.get('has_variants', False)
            in_stock = product.get('in_stock', True)

            # Формируем текст кнопки
            button_text = f"{i}. {product['brand']} {product['name']}"
            if not in_stock:
                button_text += f" ({BADGE_OOS})"
            elif has_variants:
                button_text += " (выбрать оттенок)"

            # Обрезаем текст если слишком длинный
            if len(button_text) > 50:
                button_text = button_text[:47] + "..."

            # Добавляем кнопку
            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"m:prd:{product['product_id']}"
                )
            ])

        # Добавляем кнопки навигации
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"m:cat:{category_slug}:p{page-1}"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"m:cat:{category_slug}:p{page}"))

        if nav_buttons:
            buttons.append(nav_buttons)

        # Добавляем кнопку "Назад"
        buttons.append([
            InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="makeup_picker:start")
        ])

        await cb.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in show_makeup_category: {e}")
        await cb.answer("⚠️ Ошибка загрузки категории")


@router.callback_query(F.data.startswith("m:prd:"))
async def show_makeup_product(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать детали продукта с кнопкой выбора оттенков"""
    try:
        product_id = cb.data.split(":")[2]
        user_id = cb.from_user.id if cb.from_user else 0

        # Аналитика
        if ANALYTICS_AVAILABLE:
            track_product_opened(user_id, product_id, "makeup_picker")

        # Affiliate отслеживание открытия товара
        try:
            affiliate_manager.analytics.emit('product_opened', {
                'pid': product_id,
                'source': 'makeup_picker',
                'user_id': user_id
            })
        except Exception as e:
            print(f"⚠️ Product open tracking error: {e}")

        # Получаем продукт из каталога
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()

        product = None
        for p in catalog or []:
            if getattr(p, 'id', str(id(p))) == product_id:
                product = p
                break

        if not product:
            await cb.answer("⚠️ Продукт не найден")
            return

        # Формируем сообщение
        brand = getattr(product, 'brand', 'Бренд')
        name = getattr(product, 'name', 'Название')
        price = getattr(product, 'price', 0)
        currency = getattr(product, 'currency', 'RUB')
        in_stock = getattr(product, 'in_stock', True)

        text = f"💄 **{brand} {name}**\n\n"
        text += f"💰 Цена: {price} {currency}\n"
        text += f"📦 В наличии: {'✅' if in_stock else '❌'}\n\n"

        # Проверяем наличие вариантов
        has_variants = hasattr(product, 'variants') and product.variants and len(product.variants) > 0

        if has_variants:
            text += f"🎨 Доступно {len(product.variants)} оттенков\n\n"
            text += "Выберите оттенок для добавления в корзину:"
        else:
            text += "🎨 Этот продукт доступен в одном варианте\n\n"
            text += "Добавить в корзину?"

        # Создаем кнопки
        buttons = []

        if has_variants and len(product.variants) > 1:
            # Кнопка для выбора оттенков
            buttons.append([
                InlineKeyboardButton(
                    text="🎨 Выбрать оттенок",
                    callback_data=f"m:opt:{product_id}"
                )
            ])
        elif has_variants and len(product.variants) == 1:
            # Один вариант - сразу добавляем
            variant = product.variants[0]
            buttons.append([
                InlineKeyboardButton(
                    text=f"🛍️ {BTN_ADD_TO_CART}",
                    callback_data=f"m:add:{product_id}:{getattr(variant, 'id', str(id(variant)))}"
                )
            ])
        else:
            # Нет вариантов - добавляем без variant_id
            buttons.append([
                InlineKeyboardButton(
                    text=f"🛍️ {BTN_ADD_TO_CART}",
                    callback_data=f"m:add:{product_id}:default"
                )
            ])

        # Кнопка "Назад"
        buttons.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="makeup_picker:start")
        ])

        await cb.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in show_makeup_product: {e}")
        await cb.answer("⚠️ Ошибка загрузки продукта")


@router.callback_query(F.data.startswith("m:opt:"))
async def show_makeup_shade_options(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать варианты оттенков для выбора"""
    try:
        product_id = cb.data.split(":")[2]
        user_id = cb.from_user.id if cb.from_user else 0

        # Получаем продукт из каталога
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()

        product = None
        for p in catalog or []:
            if getattr(p, 'id', str(id(p))) == product_id:
                product = p
                break

        if not product or not hasattr(product, 'variants') or not product.variants:
            await cb.answer("⚠️ Варианты не найдены")
            return

        # Получаем профиль пользователя для персонализации
        data = await state.get_data()
        user_profile = None
        if 'profile' in data and ENGINE_AVAILABLE:
            from engine.models import UserProfile
            user_profile = UserProfile(**data['profile'])

        # Выбираем подходящие оттенки
        suitable_shades = select_shades(user_profile, product)

        # Формируем сообщение
        brand = getattr(product, 'brand', 'Бренд')
        name = getattr(product, 'name', 'Название')

        text = f"💄 **{brand} {name}**\n\n"
        text += "🎨 **Выберите оттенок:**\n\n"

        # Создаем кнопки для вариантов
        buttons = []

        if suitable_shades:
            text += "**Рекомендуемые для вашего типа:**\n"
            for i, shade_info in enumerate(suitable_shades[:6], 1):  # Максимум 6 вариантов
                variant = shade_info['variant']
                variant_name = getattr(variant, 'name', f'Вариант {i}')
                undertone = getattr(variant, 'undertone', 'neutral')
                relevance = shade_info.get('relevance_score', 0.5)

                # Индикатор релевантности
                stars = "⭐" * int(relevance * 3) if relevance >= 0.7 else "☆"

                button_text = f"{stars} {variant_name}"
                if undertone:
                    button_text += f" ({undertone})"
                if len(button_text) > 35:
                    button_text = button_text[:32] + "..."

                buttons.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"m:add:{product_id}:{getattr(variant, 'id', str(id(variant)))}"
                    )
                ])
        else:
            # Показываем все доступные варианты
            for i, variant in enumerate(product.variants[:6], 1):
                variant_name = getattr(variant, 'name', f'Вариант {i}')
                undertone = getattr(variant, 'undertone', 'neutral')

                button_text = f"{i}. {variant_name}"
                if undertone:
                    button_text += f" ({undertone})"
                if len(button_text) > 35:
                    button_text = button_text[:32] + "..."

                buttons.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"m:add:{product_id}:{getattr(variant, 'id', str(id(variant)))}"
                    )
                ])

        # Добавляем кнопку "Показать все" если много вариантов
        if len(product.variants) > 6:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📋 Показать все ({len(product.variants)})",
                    callback_data=f"m:all:{product_id}"
                )
            ])

        # Кнопка "Назад"
        buttons.append([
            InlineKeyboardButton(text="◀️ Назад к продукту", callback_data=f"m:prd:{product_id}")
        ])

        await cb.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in show_makeup_shade_options: {e}")
        await cb.answer("⚠️ Ошибка загрузки оттенков")


@router.callback_query(F.data.startswith("m:add:"))
async def add_makeup_to_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Добавить продукт в корзину"""
    try:
        # Парсим callback_data: m:add:<product_id>:<variant_id>
        parts = cb.data.split(":")
        product_id = parts[2]
        variant_id = parts[3] if len(parts) > 3 else None

        user_id = cb.from_user.id if cb.from_user else 0

        # Получаем сервис корзины
        cart_service = get_cart_service()
        if not cart_service:
            await cb.answer("⚠️ Сервис корзины недоступен")
            return

        # Получаем продукт из каталога
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()

        product = None
        variant = None
        for p in catalog or []:
            if getattr(p, 'id', str(id(p))) == product_id:
                product = p
                # Ищем вариант
                if variant_id and hasattr(p, 'variants'):
                    for v in p.variants:
                        if getattr(v, 'id', str(id(v))) == variant_id:
                            variant = v
                            break
                break

        if not product:
            await cb.answer("⚠️ Продукт не найден")
            return

        # Добавляем в корзину
        try:
            cart_item = cart_service.add_item(
                user_id=user_id,
                product_id=product_id,
                variant_id=variant_id,
                qty=1
            )

            # Аналитика
            if ANALYTICS_AVAILABLE:
                track_cart_event("product_added_to_cart", user_id,
                    pid=product_id,
                    vid=variant_id or "default",
                    source=getattr(product, 'source', 'unknown'),
                    price=getattr(product, 'price', 0),
                    category=getattr(product, 'category', 'makeup')
                )

                # Аналитика выбора оттенка
                if variant_id and variant:
                    track_shade_selected(user_id, product_id, variant_id,
                        undertone=getattr(variant, 'undertone', 'unknown'))

            # Affiliate отслеживание
            try:
                # Определяем источник
                source = getattr(product, 'source', 'unknown')
                if not source or source == 'unknown':
                    # Определяем по URL или названию
                    product_url = getattr(product, 'link', '')
                    if product_url:
                        if "goldapple" in product_url.lower():
                            source = "goldapple"
                        elif "wildberries" in product_url.lower() or "marketplace" in product_url.lower():
                            source = "ru_marketplace"
                        elif "official" in product_url.lower():
                            source = "ru_official"
                        elif "amazon" in product_url.lower() or "sephora" in product_url.lower():
                            source = "intl_authorized"

                # Отслеживаем клик по checkout
                price = float(getattr(product, 'price', 0))
                affiliate_manager.track_checkout_click(
                    items_count=1,
                    total=price,
                    currency='RUB',
                    source=source,
                    product_ids=[product_id]
                )

                # Отслеживаем открытие внешнего checkout
                product_url = getattr(product, 'link', '')
                if product_url:
                    affiliate_manager.track_external_checkout_opened(
                        partner=source.title(),
                        url=product_url,
                        items_count=1
                    )

            except Exception as e:
                print(f"⚠️ Affiliate tracking error: {e}")

            # Формируем сообщение об успехе
            variant_text = f" ({getattr(variant, 'name', '')})" if variant else ""
            item_name = f"{getattr(product, 'brand', '')} {getattr(product, 'name', '')}".strip()

            message = MSG_VARIANT_ADDED.format(
                brand=getattr(product, 'brand', ''),
                name=getattr(product, 'name', ''),
                variant=getattr(variant, 'name', 'стандарт') if variant else 'стандарт'
            )

            await cb.answer(message, show_alert=True)

        except CartServiceError as e:
            await cb.answer(f"⚠️ Ошибка добавления: {str(e)}")

    except Exception as e:
        print(f"❌ Error in add_makeup_to_cart: {e}")
        await cb.answer("⚠️ Ошибка добавления в корзину")


@router.callback_query(F.data.startswith("m:all:"))
async def show_all_makeup_variants(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать все варианты продукта"""
    try:
        product_id = cb.data.split(":")[2]
        user_id = cb.from_user.id if cb.from_user else 0

        # Получаем продукт из каталога
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()

        product = None
        for p in catalog or []:
            if getattr(p, 'id', str(id(p))) == product_id:
                product = p
                break

        if not product or not hasattr(product, 'variants') or not product.variants:
            await cb.answer("⚠️ Варианты не найдены")
            return

        # Формируем сообщение со всеми вариантами
        brand = getattr(product, 'brand', 'Бренд')
        name = getattr(product, 'name', 'Название')

        text = f"💄 **{brand} {name}**\n\n"
        text += f"🎨 **Все доступные оттенки ({len(product.variants)}):**\n\n"

        # Создаем кнопки для всех вариантов
        buttons = []
        for i, variant in enumerate(product.variants, 1):
            variant_name = getattr(variant, 'name', f'Вариант {i}')
            undertone = getattr(variant, 'undertone', '')

            button_text = f"{i}. {variant_name}"
            if undertone:
                button_text += f" ({undertone})"
            if len(button_text) > 35:
                button_text = button_text[:32] + "..."

            buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"m:add:{product_id}:{getattr(variant, 'id', str(id(variant)))}"
                )
            ])

        # Кнопка "Назад"
        buttons.append([
            InlineKeyboardButton(text="◀️ Назад к выбору", callback_data=f"m:opt:{product_id}")
        ])

        await cb.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in show_all_makeup_variants: {e}")
        await cb.answer("⚠️ Ошибка загрузки вариантов")


@router.callback_query(F.data == "m:back:results")
async def back_to_results(cb: CallbackQuery, state: FSMContext) -> None:
    """Вернуться к результатам теста"""
    try:
        # Восстанавливаем состояние результата
        await state.set_state("DetailedPaletteFlow:RESULT")

        # Получаем сохраненные данные
        data = await state.get_data()
        season = data.get('season', 'unknown')
        tldr_report = data.get('tldr_report', 'Нет данных')

        season_names = {
            "spring": "🌸 Яркая Весна",
            "summer": "🌊 Мягкое Лето",
            "autumn": "🍂 Глубокая Осень",
            "winter": "❄️ Холодная Зима"
        }

        await cb.message.edit_text(
            f"🎉 **РЕЗУЛЬТАТ ТЕСТА**\n\n"
            f"**Ваш цветотип:** {season_names.get(season, season)}\n\n"
            f"📊 **Краткий анализ:**\n{tldr_report}\n\n"
            f"Что вы хотите увидеть?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ℹ️ Полное описание цветотипа", callback_data="result:description")],
                [InlineKeyboardButton(text="🛍️ Что купить", callback_data="result:products")],
                [InlineKeyboardButton(text="💄 Подобрать макияж", callback_data="makeup_picker:start")],
                [InlineKeyboardButton(text="📄 Получить отчёт", callback_data="report:latest")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
            ])
        )

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in back_to_results: {e}")
        await cb.answer("⚠️ Ошибка возврата")
