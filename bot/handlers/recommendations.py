"""
🛍️ Recommendations Handler

Shows product recommendations with inline buttons for cart operations
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from engine.cart_store import CartStore, CartItem
from config.env import get_settings
from bot.utils.security import safe_send_message
from i18n.ru import *

logger = logging.getLogger(__name__)
router = Router()

# Global cart store instance
cart_store = CartStore()

@router.callback_query(F.data.startswith("rec:"))
async def handle_recommendations(cb: CallbackQuery, bot: Bot):
    """Handle recommendations callbacks"""
    try:
        data = cb.data
        user_id = cb.from_user.id
        settings = get_settings()

        if data.startswith("rec:add:"):
            # Add to cart: rec:add:<pid>:<vid>
            parts = data.split(":")
            if len(parts) < 4:
                await cb.answer("❌ Неверный формат данных")
                return

            product_id = parts[2]
            variant_id = parts[3] if len(parts) > 3 and parts[3] != "none" else None

            # Create cart item (mock data - should come from catalog)
            item = CartItem(
                product_id=product_id,
                variant_id=variant_id,
                name=f"Продукт {product_id}",
                price=1990,  # 19.90 RUB in cents
                currency="RUB",
                qty=1,
                source="goldapple",
                link=f"https://goldapple.ru/product/{product_id}",
                meta={"category": "skincare"}
            )

            # Add to cart
            cart = await cart_store.add(user_id, item)

            # Update cart badge in UI
            await cb.answer(MSG_ADDED, show_alert=False)

            # Optionally update message with cart count
            # This would require re-rendering the recommendations

        elif data.startswith("rec:open:"):
            # Open product details: rec:open:<pid>
            product_id = data.split(":")[2]
            # Mock product details
            text = f"📦 **Продукт {product_id}**\n\nПодробное описание товара..."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=BTN_ADD, callback_data=f"rec:add:{product_id}:none")],
                [InlineKeyboardButton(text=BTN_BACK, callback_data="rec:back")]
            ])
            await cb.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

        elif data.startswith("rec:more:"):
            # Load more recommendations: rec:more:<category>:<page>
            parts = data.split(":")
            category = parts[2] if len(parts) > 2 else "all"
            page = int(parts[3]) if len(parts) > 3 else 1

            # Generate next page of recommendations
            await show_recommendations_page(cb, category, page)

        elif data == "rec:back":
            # Back to main recommendations
            await show_main_recommendations(cb)

        await cb.answer()

    except Exception as e:
        logger.error(f"Error in recommendations handler: {e}")
        await cb.answer("❌ Произошла ошибка", show_alert=True)

async def show_recommendations_page(cb: CallbackQuery, category: str = "skincare", page: int = 1):
    """Show paginated recommendations"""
    items_per_page = 3
    start_idx = (page - 1) * items_per_page

    # Mock recommendations data
    mock_products = [
        {"id": "cleanser-001", "name": "Очищающее средство CeraVe", "price": 1590, "category": "cleanser"},
        {"id": "toner-001", "name": "Тоник La Roche-Posay", "price": 1890, "category": "toner"},
        {"id": "serum-001", "name": "Сыворотка The Ordinary", "price": 2190, "category": "serum"},
        {"id": "moisturizer-001", "name": "Увлажняющий крем Neutrogena", "price": 1290, "category": "moisturizer"},
        {"id": "sunscreen-001", "name": "SPF La Prairie", "price": 2990, "category": "sunscreen"},
    ]

    # Filter by category
    if category != "all":
        filtered = [p for p in mock_products if p["category"] == category]
    else:
        filtered = mock_products

    # Paginate
    total_pages = (len(filtered) + items_per_page - 1) // items_per_page
    page_items = filtered[start_idx:start_idx + items_per_page]

    text = f"💄 **Рекомендации** ({category})\nСтраница {page}/{total_pages}\n\n"

    keyboard = InlineKeyboardBuilder()

    for product in page_items:
        price_rub = product["price"] // 100  # Convert cents to rubles
        text += f"🧴 **{product['name']}**\n"
        text += f"— цена: {price_rub} ₽\n"
        text += f"— магазин: Gold Apple\n\n"

        # Buttons for each product
        keyboard.row(
            InlineKeyboardButton(
                text=BTN_ADD,
                callback_data=f"rec:add:{product['id']}:none"
            ),
            InlineKeyboardButton(
                text=BTN_DETAILS,
                callback_data=f"rec:open:{product['id']}"
            )
        )

    # Navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text=BTN_PREV,
            callback_data=f"rec:more:{category}:{page-1}"
        ))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text=BTN_NEXT,
            callback_data=f"rec:more:{category}:{page+1}"
        ))

    if nav_buttons:
        keyboard.row(*nav_buttons)

    # Back button
    keyboard.row(InlineKeyboardButton(text=BTN_BACK, callback_data="rec:back"))

    await cb.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

async def show_main_recommendations(cb: CallbackQuery):
    """Show main recommendations screen with categories"""
    text = "💄 **Рекомендованные средства**\n\n"
    text += "Выберите категорию для просмотра рекомендаций:"

    keyboard = InlineKeyboardBuilder()

    categories = [
        ("Очищение", "cleanser"),
        ("Тоник", "toner"),
        ("Сыворотки", "serum"),
        ("Увлажнение", "moisturizer"),
        ("Солнцезащита", "sunscreen"),
    ]

    for cat_name, cat_id in categories:
        keyboard.row(InlineKeyboardButton(
            text=f"🧴 {cat_name}",
            callback_data=f"rec:more:{cat_id}:1"
        ))

    # Show all
    keyboard.row(InlineKeyboardButton(
        text="📋 Все рекомендации",
        callback_data="rec:more:all:1"
    ))

    await cb.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

async def show_recommendations_after_test(bot: Bot, user_id: int, test_type: str = "skincare"):
    """Show recommendations after completing a test"""
    try:
        text = "🎉 **Тест завершён!**\n\n"
        text += "Рекомендую ознакомиться с подобранными средствами:\n\n"

        # Quick recommendations preview
        keyboard = InlineKeyboardBuilder()

        if test_type == "skincare":
            categories = ["cleanser", "toner", "serum"]
        else:  # makeup
            categories = ["foundation", "concealer", "mascara"]

        for category in categories:
            keyboard.row(InlineKeyboardButton(
                text=f"🛍️ {category.title()} средства",
                callback_data=f"rec:more:{category}:1"
            ))

        keyboard.row(InlineKeyboardButton(
            text="🛒 Перейти в корзину",
            callback_data="cart:open"
        ))

        await safe_send_message(
            bot, user_id,
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error showing recommendations after test: {e}")

# Export functions for use in other handlers
__all__ = ["router", "show_recommendations_after_test"]
