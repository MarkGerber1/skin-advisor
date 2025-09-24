"""
Recommendations handler: shows products and routes cart callbacks.
"""

from __future__ import annotations

import logging
from typing import List

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils.security import safe_send_message
from config.env import get_settings
from engine.catalog_store import CatalogStore
from i18n.ru import (
    BTN_ADD,
    BTN_BACK,
    BTN_BACK_RECO,
    BTN_CART_CONTINUE,
    BTN_MORE,
    MSG_CART_UPDATED,
)

logger = logging.getLogger(__name__)
router = Router()

try:
    from engine.selector import SelectorV2

    _selector = SelectorV2()
    selector_available = True
except ImportError:  # pragma: no cover - optional dependency
    selector_available = False
    _selector = None
    logger.warning("SelectorV2 not available; recommendations will use static fallback")


def _product_button(product_id: str, label: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=label,
        callback_data=f"cart:add:{product_id}:default",
    )


async def _show_product_details(cb: CallbackQuery, product_id: str) -> None:
    text = f"Вы выбрали товар {product_id}. Добавить его в корзину?"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [_product_button(product_id, BTN_ADD)],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="rec:back")],
        ]
    )
    await cb.message.edit_text(text, reply_markup=keyboard)


def _get_catalog_products() -> List[dict]:
    """Получить товары из реального каталога как fallback (без персонализации)."""
    try:
        settings = get_settings()
        catalog_store = CatalogStore.instance(settings.catalog_path)
        catalog = catalog_store.get()
        return [
            {
                "id": p.key,
                "name": p.title,
                "price": p.price or 0,
                "category": p.category,
                "brand": p.brand,
                "image_url": p.image_url,
                "source": p.source,
            }
            for p in catalog[:200]
        ]
    except Exception as e:
        logger.error(f"Failed to load catalog products: {e}")
        # Ultimate fallback
        return [
            {"id": "cleanser-001", "name": "Очищающий гель", "price": 1590, "category": "cleanser"},
            {"id": "toner-001", "name": "Успокаивающий тоник", "price": 1890, "category": "toner"},
            {
                "id": "serum-001",
                "name": "Сыворотка с витамином С",
                "price": 2190,
                "category": "serum",
            },
            {
                "id": "moisturizer-001",
                "name": "Увлажняющий крем",
                "price": 1290,
                "category": "moisturizer",
            },
            {
                "id": "sunscreen-001",
                "name": "Солнцезащитный крем",
                "price": 2990,
                "category": "sunscreen",
            },
        ]


def _filter_products(category: str, page: int, per_page: int = 8) -> tuple[List[dict], int]:
    settings = get_settings()
    products_all: List[dict] = []

    if selector_available and _selector:
        try:
            products_all = _get_catalog_products()  # персонализацию после тестов делаем отдельно
        except Exception as exc:  # pragma: no cover
            logger.warning("Selector fetch failed: %s", exc)
            products_all = _get_catalog_products()
    else:
        products_all = _get_catalog_products()

    if category != "all":
        filtered = [p for p in products_all if p.get("category") == category]
    else:
        filtered = products_all

    total_pages = max(1, (len(filtered) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    return filtered[start:end], total_pages


@router.callback_query(F.data.startswith("rec:"))
async def handle_recommendations(cb: CallbackQuery, bot: Bot) -> None:
    try:
        data = cb.data
        # Legacy rec:add: callbacks - redirect to cart:add:
        if data.startswith("rec:add:"):
            parts = data.split(":")
            if len(parts) >= 3:
                product_id = parts[2]
                variant_id = parts[3] if len(parts) > 3 else "default"
                cb.data = f"cart:add:{product_id}:{variant_id}"
            await cb.answer(MSG_CART_UPDATED, show_alert=False)
            return

        if data.startswith("rec:open:"):
            product_id = data.split(":")[2]
            await _show_product_details(cb, product_id)
        elif data.startswith("rec:more:"):
            parts = data.split(":") + ["all", "1"]
            category = parts[2] or "all"
            page = int(parts[3]) if len(parts) > 3 and parts[3] else 1
            await show_recommendations_page(cb, category, page)
        elif data == "rec:back":
            await show_main_recommendations(cb)
        await cb.answer()
    except Exception as exc:  # pragma: no cover
        logger.exception("Error in recommendations handler: %s", exc)
        await cb.answer("Произошла ошибка. Попробуйте ещё раз", show_alert=True)


async def show_recommendations_page(
    cb: CallbackQuery, category: str = "all", page: int = 1
) -> None:
    page_items, total_pages = _filter_products(category, page)

    text_lines = [
        f"Рекомендации · {category}",
        f"Страница {page}/{total_pages}",
        "",
    ]
    keyboard = InlineKeyboardBuilder()

    for product in page_items:
        name = product.get("name", "Товар")
        product_id = product.get("id") or product.get("key") or "unknown"
        price = product.get("price")
        price_row = f"{price} ₽" if price else "—"
        text_lines.append(f"• {name} — {price_row}")
        keyboard.row(_product_button(product_id, BTN_ADD))

    # Pagination row ◀︎ 1/3 ▶︎
    if total_pages > 1:
        nav_row: List[InlineKeyboardButton] = []
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(text="◀︎", callback_data=f"rec:more:{category}:{page-1}")
            )
        nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(text="▶︎", callback_data=f"rec:more:{category}:{page+1}")
            )
        keyboard.row(*nav_row)

    keyboard.row(InlineKeyboardButton(text=BTN_BACK_RECO, callback_data="rec:back"))
    keyboard.row(InlineKeyboardButton(text=BTN_CART_CONTINUE, callback_data="cart:open"))

    await cb.message.edit_text("\n".join(text_lines), reply_markup=keyboard.as_markup())


async def show_main_recommendations(cb: CallbackQuery) -> None:
    text = "Выберите категорию, чтобы продолжить подбор."
    keyboard = InlineKeyboardBuilder()
    categories = [
        ("Очищение", "cleanser"),
        ("Тоники", "toner"),
        ("Сыворотки", "serum"),
        ("Кремы", "moisturizer"),
        ("Солнцезащита", "sunscreen"),
    ]
    for title, slug in categories:
        keyboard.row(InlineKeyboardButton(text=title, callback_data=f"rec:more:{slug}:1"))
    keyboard.row(InlineKeyboardButton(text=BTN_CART_CONTINUE, callback_data="cart:open"))
    await cb.message.edit_text(text, reply_markup=keyboard.as_markup())


async def show_recommendations_after_test(
    bot: Bot, user_id: int, test_type: str = "skincare"
) -> None:
    """Показ персональных рекомендаций после успешного теста.

    Использует SelectorV2.select_products_v2(profile, catalog, partner_code, redirect_base)
    и выводит товары ухода (skincare) с кнопками «В корзину».
    """
    settings = get_settings()

    try:
        # Профиль пользователя
        from bot.handlers.user_profile_store import get_user_profile_store

        profile_store = get_user_profile_store()
        profile = profile_store.load_profile(user_id)

        # Каталог
        catalog = CatalogStore.instance(settings.catalog_path).get()

        # Селектор
        if selector_available and _selector and profile:
            result = _selector.select_products_v2(
                profile=profile,
                catalog=catalog,
                partner_code=settings.partner_code,
                redirect_base=settings.redirect_base,
            )
            skincare = result.get("skincare", {})
            # Берём первые 3 позиции из всех категорий ухода
            products: List[dict] = []
            for items in skincare.values():
                products.extend(items or [])
            products = products[:3]
        else:
            products = _get_catalog_products()[:3]

        text = (
            "Результаты подбора готовы. Вот несколько идей:"
            if settings
            else "Вот что мы нашли для вас:"
        )
        keyboard = InlineKeyboardBuilder()

        for product in products:
            name = product.get("name", "Товар")
            product_id = product.get("id", "unknown")
            keyboard.row(_product_button(product_id, f"Добавить {name[:18]}"))

        keyboard.row(InlineKeyboardButton(text=BTN_MORE, callback_data="rec:more:all:1"))
        keyboard.row(InlineKeyboardButton(text=BTN_CART_CONTINUE, callback_data="cart:open"))
        keyboard.row(InlineKeyboardButton(text="🛒 Открыть корзину", callback_data="cart:open"))

        await safe_send_message(bot, user_id, text, reply_markup=keyboard.as_markup())

    except Exception as e:
        logger.exception("Failed to show recommendations after test: %s", e)
        await safe_send_message(
            bot, user_id, "⚠️ Не удалось загрузить рекомендации. Попробуйте позже."
        )
