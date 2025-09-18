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

# Import SelectorV2 for recommendations
try:
    from engine.selector import SelectorV2
    selector_available = True
except ImportError:
    selector_available = False
    logger.warning("SelectorV2 not available - recommendations will use fallback")

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

            # Try to get real product data from selector
            product_data = None
            if selector_available:
                try:
                    selector = SelectorV2()
                    all_products = selector.select_products(user_id, category="all", limit=100)
                    for prod in all_products:
                        if str(prod.get("id", "")) == product_id:
                            product_data = prod
                            break
                except Exception as e:
                    logger.warning(f"Could not get product data for {product_id}: {e}")

            # Create cart item with real or fallback data
            if product_data:
                item = CartItem(
                    product_id=product_id,
                    variant_id=variant_id,
                    name=product_data.get("name", f"Продукт {product_id}"),
                    price=int(product_data.get("price", 0) * 100),  # Convert to cents
                    currency="RUB",
                    source="recommendations",
                    link="",  # Will be filled by affiliate system
                )
            else:
                # Fallback mock data
                item = CartItem(
                    product_id=product_id,
                    variant_id=variant_id,
                    name=f"Продукт {product_id}",
                    price=1990,  # 19.90 RUB in cents
                    currency="RUB",
                    source="recommendations",
                    link="",
                )

            # Add to cart
            cart = await cart_store.add(user_id, item)

            # Analytics
            try:
                from engine.analytics import cart_item_added
                cart_item_added(
                    user_id=user_id,
                    product_id=product_id,
                    variant_id=variant_id or "",
                    source="recommendations",
                    price=item.price,
                )
            except Exception as e:
                logger.warning(f"Analytics error: {e}")

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
    """Show recommendations after completing a test - CART V2 INTEGRATION"""
    try:
        text = "🎉 **Тест завершён!**\n\n"
        text += "Вот персональные рекомендации для вас:\n\n"

        # Get real recommendations using SelectorV2
        if selector_available:
            try:
                selector = SelectorV2()
                recommendations = selector.select_products(user_id, category="all", limit=6)
            except Exception as e:
                logger.error(f"Failed to get recommendations from SelectorV2: {e}")
                recommendations = []
        else:
            logger.warning("SelectorV2 not available, using empty recommendations")
            recommendations = []

            if recommendations:
                keyboard = InlineKeyboardBuilder()

                for i, product in enumerate(recommendations[:3]):  # Show first 3 products
                    product_name = product.get("name", f"Товар {i+1}")
                    product_id = product.get("id", f"unknown-{i}")
                    price = product.get("price", 0)

                    # Product info
                    text += f"🧴 **{product_name}**\n"
                    if price:
                        text += f"💰 {price} ₽\n"
                    text += "\n"

                    # Add to cart button
                    keyboard.row(InlineKeyboardButton(
                        text=f"Добавить ▸ {product_name[:20]}...",
                        callback_data=f"rec:add:{product_id}:default"
                    ))

                # More recommendations button
                keyboard.row(InlineKeyboardButton(
                    text="🛍️ Больше рекомендаций",
                    callback_data=f"rec:more:{test_type}:1"
                ))

                # Cart button
                keyboard.row(InlineKeyboardButton(
                    text="🛒 Корзина",
                    callback_data="cart:open"
                ))

                await safe_send_message(
                    bot, user_id,
                    text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
            else:
                # Fallback if no recommendations
                text += "⚠️ Не удалось сгенерировать рекомендации.\nПопробуйте пройти тест заново."

                keyboard = InlineKeyboardBuilder()
                keyboard.row(InlineKeyboardButton(
                    text="🔄 Пройти тест заново",
                    callback_data=f"start:{test_type}"
                ))

                await safe_send_message(
                    bot, user_id,
                    text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            # Fallback message
            text += "⚠️ Ошибка при генерации рекомендаций.\n\n"
            text += "Используйте меню для выбора средств:"

            keyboard = InlineKeyboardBuilder()
            keyboard.row(InlineKeyboardButton(
                text="🛍️ Каталог товаров",
                callback_data="rec:more:all:1"
            ))
            keyboard.row(InlineKeyboardButton(
                text="🛒 Корзина",
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
