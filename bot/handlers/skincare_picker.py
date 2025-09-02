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

from engine.catalog_store import CatalogStore
from engine.models import Product
from engine.selector import SelectorV2
from i18n.ru import *
from services.cart_service import get_cart_service, CartServiceError

# Analytics import with fallback
try:
    from engine.analytics import get_analytics_tracker
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    def get_analytics_tracker():
        return None

router = Router()


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

# Обратный маппинг для поиска товаров по категориям
CATEGORY_TO_ENGINE = {
    CAT_CLEANSE: "cleanser",
    CAT_TONE: "toner",
    CAT_SERUM: "serum",
    CAT_MOIST: "moisturizer",
    CAT_EYE: "eye_cream",
    CAT_SPF: "sunscreen",
    CAT_MASK: "mask"
}


def _format_price(product: Dict) -> str:
    """Форматирование цены с валютой"""
    price = product.get("price", 0)
    currency = product.get("price_currency", "RUB")

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
        # Получаем сохраненный профиль пользователя
        from bot.handlers.user_profile_store import get_user_profile_store
        profile_store = get_user_profile_store()
        user_profile = profile_store.load_profile(user_id)

        if not user_profile:
            return [], 0

        # Получаем каталог
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()

        # Используем SelectorV2 для получения рекомендаций
        selector = SelectorV2()
        result = selector.select_products_v2(
            profile=user_profile,
            catalog=catalog,
            partner_code="S1"
        )

        # Получаем товары из нужной категории
        engine_category = CATEGORY_TO_ENGINE.get(category_slug, category_slug)
        skincare_data = result.get("skincare", {})
        category_products = skincare_data.get(engine_category, [])

        if not category_products:
            return [], 0

        # Приоритизация источников и разрешение
        resolved_products = []
        for product in category_products:
            resolved = _resolve_product_source(product)
            if resolved:
                resolved_products.append(resolved)

        # Пагинация (8 товаров на страницу)
        per_page = 8
        total_pages = (len(resolved_products) + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        page_products = resolved_products[start_idx:end_idx]

        return page_products, total_pages

    except Exception as e:
        print(f"❌ Error getting products for category {category_slug}: {e}")
        return [], 0


@router.callback_query(F.data == "skincare_result:products")
async def start_skincare_picker(cb: CallbackQuery, state: FSMContext) -> None:
    """Запуск подбора ухода после теста"""
    try:
        # Аналитика
        if ANALYTICS_AVAILABLE:
            analytics = get_analytics_tracker()
            analytics.track_event("recommendations_viewed", cb.from_user.id, {
                "branch": "skincare",
                "source": "test_completion"
            })

        # Получаем доступные категории из результатов теста
        data = await state.get_data()
        skin_analysis = data.get("skin_analysis", {})
        skin_type = skin_analysis.get("type", "normal")
        concerns = skin_analysis.get("concerns", [])

        # Определяем релевантные категории на основе типа кожи и проблем
        available_categories = []

        # Всегда показываем основные категории
        available_categories.extend([
            (CAT_CLEANSE, BTN_CLEANSE),
            (CAT_TONE, BTN_TONE),
            (CAT_SERUM, BTN_SERUM),
            (CAT_MOIST, BTN_MOIST)
        ])

        # Добавляем специфические категории
        if any(concern in ["aging", "dark_circles", "puffiness"] for concern in concerns):
            available_categories.append((CAT_EYE, BTN_EYE))

        if any(concern in ["pigmentation", "sun_damage"] for concern in concerns):
            available_categories.append((CAT_SPF, BTN_SPF))

        # Маски всегда доступны
        available_categories.append((CAT_MASK, BTN_REMOVER))

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
        if ANALYTICS_AVAILABLE:
            analytics = get_analytics_tracker()
            analytics.track_event("category_opened", user_id, {
                "name": category_slug,
                "page": page
            })

        # Получаем товары категории
        products, total_pages = _get_products_by_category(user_id, category_slug, page)

        if not products:
            # Нет товаров в категории
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_BACK, callback_data="c:back:categories")],
                [InlineKeyboardButton(text=BTN_BACK_CAT, callback_data="skincare_result:products")]
            ])

            await cb.message.edit_text(
                f"😔 **{CATEGORY_MAPPING.get(category_slug, category_slug)}**\n\n"
                f"К сожалению, подходящие продукты в этой категории сейчас недоступны.\n\n"
                f"Выберите другую категорию или попробуйте позже.",
                reply_markup=kb
            )
            await cb.answer()
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
        if ANALYTICS_AVAILABLE:
            analytics = get_analytics_tracker()
            analytics.track_event("product_opened", user_id, {
                "pid": product_id,
                "source": "category_view"
            })

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
            price_text = _format_price({"price": variant["price"], "price_currency": "RUB"})

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
        if not hasattr(cb.bot, 'cart_service_available'):
            await cb.answer(MSG_ADD_FAILED)
            return

        try:
            cart_service = get_cart_service()

            # Добавляем товар в корзину
            cart_item = await cart_service.add_item(
                user_id=user_id,
                product_id=product_id,
                variant_id=variant_id,
                qty=1
            )

            # Аналитика
            if ANALYTICS_AVAILABLE:
                analytics = get_analytics_tracker()
                analytics.track_event("product_added_to_cart", user_id, {
                    "pid": product_id,
                    "vid": variant_id or "default",
                    "source": cart_item.ref_link or "unknown",
                    "price": cart_item.price,
                    "category": cart_item.category
                })

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
            if ANALYTICS_AVAILABLE:
                analytics = get_analytics_tracker()
                analytics.track_event("error_shown", user_id, {
                    "code": e.code.value if hasattr(e, 'code') else "unknown",
                    "place": "cart_add",
                    "error_message": str(e)
                })

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
            price_text = _format_price({"price": alt["price"], "price_currency": "RUB"})
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
        if ANALYTICS_AVAILABLE:
            analytics = get_analytics_tracker()
            analytics.track_event("alternatives_shown", user_id, {
                "pid": product_id,
                "base_category": "unknown",  # TODO: определить категорию
                "alternatives_count": len(alternatives)
            })

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
