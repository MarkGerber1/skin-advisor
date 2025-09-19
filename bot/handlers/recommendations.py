"""Recommendations handler: карточки с Add/More/View Cart."""

import logging
from urllib.parse import quote_plus
from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.env import get_settings
from bot.utils.security import safe_send_message
from i18n.ru import BTN_ADD, BTN_BACK_RECO, BTN_DETAILS, BTN_MORE, BTN_VIEW_CART, MSG_UNAVAILABLE

try:
    from engine.selector import SelectorV2
    selector_available = True
except ImportError:  # pragma: no cover
    selector_available = False

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("rec:"))
async def handle_recommendations(cb: CallbackQuery, bot: Bot) -> None:
    try:
        data = cb.data
        user_id = cb.from_user.id
        if data.startswith("rec:open:")):
            await _show_product_details(cb)
        elif data.startswith("rec:more:")):
            parts = data.split(":")
            category = parts[2] if len(parts) > 2 else "all"
            page = int(parts[3]) if len(parts) > 3 else 1
            await _show_page(cb, category, page)
        elif data == "rec:back":
            await show_main_recommendations(cb)
        await cb.answer()
    except Exception as exc:
        logger.error("Error in recommendations handler: %s", exc)
        await cb.answer(MSG_UNAVAILABLE, show_alert=True)


def _build_product_keyboard(product_id: str) -> InlineKeyboardMarkup:
    key = quote_plus(product_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_ADD, callback_data=f"cart:add:{key}:")],
            [InlineKeyboardButton(text=BTN_DETAILS, callback_data=f"rec:open:{product_id}")],
            [InlineKeyboardButton(text=BTN_VIEW_CART, callback_data="cart:open")],
        ]
    )


async def _show_product_details(cb: CallbackQuery) -> None:
    product_id = cb.data.split(":")[2]
    text = (
        "🔍 **Подробности**\n\n"
        f"Товар: `{product_id}`\n"
        "Скоро здесь будут реальные описания и фото."
    )
    markup = _build_product_keyboard(product_id)
    await cb.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")


async def _show_page(cb: CallbackQuery, category: str, page: int) -> None:
    products = _mock_products(category)
    items_per_page = 3
    start = (page - 1) * items_per_page
    page_items = products[start : start + items_per_page]
    total_pages = max(1, (len(products) + items_per_page - 1) // items_per_page)

    text = (
        f"🔎 **Рекомендации** ({category})\n"
        f"Страница {page}/{total_pages}\n\n"
    )
    keyboard = InlineKeyboardBuilder()
    for product in page_items:
        pid = product["id"]
        price = product["price"]
        text += f"• {product['name']} — {price} ₽\n"
        keyboard.row(
            InlineKeyboardButton(text=BTN_ADD, callback_data=f"cart:add:{quote_plus(pid)}:"),
            InlineKeyboardButton(text=BTN_DETAILS, callback_data=f"rec:open:{pid}"),
        )

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"rec:more:{category}:{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"rec:more:{category}:{page+1}"))
    if nav_row:
        keyboard.row(*nav_row)
    keyboard.row(InlineKeyboardButton(text=BTN_BACK_RECO, callback_data="rec:back"))
    keyboard.row(InlineKeyboardButton(text=BTN_VIEW_CART, callback_data="cart:open"))

    await cb.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")


async def show_main_recommendations(cb: CallbackQuery) -> None:
    categories = [
        ("Умывание", "cleanser"),
        ("Тонизация", "toner"),
        ("Базовый уход", "serum"),
        ("Увлажнение", "moisturizer"),
        ("SPF-защита", "sunscreen"),
    ]
    text = "✨ **Рекомендации по категориям**\n\nВыберите направление, чтобы посмотреть товары."
    keyboard = InlineKeyboardBuilder()
    for name, slug in categories:
        keyboard.row(InlineKeyboardButton(text=f"{name}", callback_data=f"rec:more:{slug}:1"))
    keyboard.row(InlineKeyboardButton(text=BTN_VIEW_CART, callback_data="cart:open"))
    await cb.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")


async def show_recommendations_after_test(bot: Bot, user_id: int, test_type: str = "skincare") -> None:
    picks = _mock_products(test_type)[:3]
    text_lines = ["🎉 **Тест завершён!**", "", "Товары, которые подойдут вам:"]
    keyboard = InlineKeyboardBuilder()
    for product in picks:
        text_lines.append(f"• {product['name']} — {product['price']} ₽")
        keyboard.row(
            InlineKeyboardButton(text=BTN_ADD, callback_data=f"cart:add:{quote_plus(product['id'])}:"),
            InlineKeyboardButton(text=BTN_DETAILS, callback_data=f"rec:open:{product['id']}")
        )
    keyboard.row(InlineKeyboardButton(text=BTN_VIEW_CART, callback_data="cart:open"))
    keyboard.row(InlineKeyboardButton(text=BTN_MORE, callback_data=f"rec:more:{test_type}:1"))

    await safe_send_message(
        bot,
        user_id,
        "\n".join(text_lines),
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown",
    )


def _mock_products(category: str) -> List[Dict[str, Any]]:
    return [
        {"id": "cleanser-001", "name": "Гель для умывания CeraVe", "price": 1590},
        {"id": "toner-001", "name": "Тоник La Roche-Posay", "price": 1890},
        {"id": "serum-001", "name": "Сыворотка The Ordinary", "price": 2190},
        {"id": "moisturizer-001", "name": "Крем Neutrogena Hydro Boost", "price": 1290},
        {"id": "sunscreen-001", "name": "SPF-флюид La Prairie", "price": 2990},
    ]


__all__ = ["router", "show_recommendations_after_test", "show_main_recommendations"]
