"""
🛒 Cart v2 Handler

New cart implementation with proper UX flow:
recommendations → cart → checkout
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from engine.cart_store import CartStore, Cart, CartItem
from config.env import get_settings
from bot.utils.security import safe_send_message, safe_edit_message_text, sanitize_message
from engine.analytics import get_analytics_tracker
from i18n.ru import *

logger = logging.getLogger(__name__)
router = Router()

# Global instances
cart_store = CartStore()
analytics = get_analytics_tracker()

def format_price(amount_cents: int, currency: str = "RUB") -> str:
    """Format price for display"""
    amount_rub = amount_cents // 100
    return f"{amount_rub} {currency}"

def format_cart_item(item: CartItem) -> str:
    """Format cart item for display"""
    price_str = format_price(item.price, item.currency)
    total_str = format_price(item.price * item.qty, item.currency)
    return CART_ITEM_FMT.format(
        name=item.name,
        price=price_str,
        qty=item.qty,
        total=total_str
    )

def build_cart_keyboard(cart: Cart, user_id: int) -> InlineKeyboardMarkup:
    """Build cart keyboard with item controls"""
    keyboard = InlineKeyboardBuilder()

    # Item controls
    for key, item in cart.items.items():
        # Quantity controls for each item
        keyboard.row(
            InlineKeyboardButton(text=BTN_DEC, callback_data=f"cart:dec:{key}"),
            InlineKeyboardButton(text=str(item.qty), callback_data=f"cart:info:{key}"),
            InlineKeyboardButton(text=BTN_INC, callback_data=f"cart:inc:{key}"),
            InlineKeyboardButton(text=BTN_DEL, callback_data=f"cart:del:{key}")
        )

    # Cart actions
    keyboard.row(
        InlineKeyboardButton(text=BTN_BACK_RECO, callback_data="cart:back_reco"),
        InlineKeyboardButton(text=BTN_CHECKOUT, callback_data="cart:checkout")
    )

    keyboard.row(InlineKeyboardButton(text=BTN_CLEAR, callback_data="cart:clear"))

    return keyboard.as_markup()

async def render_cart(cart: Cart) -> str:
    """Render cart content as text"""
    if not cart.items:
        return CART_EMPTY

    text = f"{CART_TITLE}\n\n"

    # Items
    for i, (key, item) in enumerate(cart.items.items(), 1):
        text += f"{i}) {format_cart_item(item)}\n"

    # Total
    total_str = format_price(cart.subtotal, cart.currency)
    text += f"\n{CART_TOTAL.format(total=total_str)}"

    # Currency warning
    if cart.needs_review:
        text += "\n⚠️ Разные валюты в корзине"

    return text

@router.callback_query(F.data == "cart:open")
async def handle_cart_open(cb: CallbackQuery):
    """Open cart screen"""
    try:
        user_id = cb.from_user.id
        cart = await cart_store.get(user_id)

        text = await render_cart(cart)
        keyboard = build_cart_keyboard(cart, user_id)

        await safe_edit_message_text(
            cb.message.chat.id,
            cb.message.message_id,
            text,
            reply_markup=keyboard
        )

        analytics.cart_opened(user_id)
        await cb.answer()

    except Exception as e:
        logger.error(f"Error opening cart: {e}")
        await cb.answer("❌ Ошибка открытия корзины", show_alert=True)

@router.callback_query(F.data.startswith("cart:inc:"))
async def handle_cart_inc(cb: CallbackQuery):
    """Increase item quantity"""
    try:
        key = cb.data.replace("cart:inc:", "")
        user_id = cb.from_user.id

        cart = await cart_store.set_qty(user_id, key, 99)  # Max qty check in set_qty
        text = await render_cart(cart)
        keyboard = build_cart_keyboard(cart, user_id)

        await safe_edit_message_text(
            cb.message.chat.id,
            cb.message.message_id,
            text,
            reply_markup=keyboard
        )

        analytics.cart_qty_changed(user_id, key, cart.items.get(key, CartItem("", "")).qty)
        await cb.answer("➕ Количество увеличено")

    except Exception as e:
        logger.error(f"Error increasing quantity: {e}")
        await cb.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("cart:dec:"))
async def handle_cart_dec(cb: CallbackQuery):
    """Decrease item quantity"""
    try:
        key = cb.data.replace("cart:dec:", "")
        user_id = cb.from_user.id

        # Get current quantity
        cart = await cart_store.get(user_id)
        current_qty = cart.items.get(key, CartItem("", "")).qty

        if current_qty <= 1:
            # Remove item instead of setting to 0
            cart = await cart_store.remove(user_id, key)
        else:
            cart = await cart_store.set_qty(user_id, key, current_qty - 1)

        text = await render_cart(cart)
        keyboard = build_cart_keyboard(cart, user_id)

        await safe_edit_message_text(
            cb.message.chat.id,
            cb.message.message_id,
            text,
            reply_markup=keyboard
        )

        new_qty = cart.items.get(key, CartItem("", "")).qty
        analytics.cart_qty_changed(user_id, key, new_qty)
        if new_qty == 0:
            analytics.cart_item_removed(user_id, key)

        await cb.answer("➖ Количество уменьшено")

    except Exception as e:
        logger.error(f"Error decreasing quantity: {e}")
        await cb.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("cart:del:"))
async def handle_cart_del(cb: CallbackQuery):
    """Remove item from cart"""
    try:
        key = cb.data.replace("cart:del:", "")
        user_id = cb.from_user.id

        cart = await cart_store.remove(user_id, key)

        text = await render_cart(cart)
        keyboard = build_cart_keyboard(cart, user_id)

        await safe_edit_message_text(
            cb.message.chat.id,
            cb.message.message_id,
            text,
            reply_markup=keyboard
        )

        analytics.cart_item_removed(user_id, key)
        await cb.answer("🗑️ Товар удалён")

    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        await cb.answer("❌ Ошибка удаления", show_alert=True)

@router.callback_query(F.data == "cart:clear")
async def handle_cart_clear(cb: CallbackQuery):
    """Clear entire cart"""
    try:
        user_id = cb.from_user.id
        await cart_store.clear(user_id)

        text = CART_EMPTY
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BACK_RECO, callback_data="cart:back_reco")]
        ])

        await safe_edit_message_text(
            cb.message.chat.id,
            cb.message.message_id,
            text,
            reply_markup=keyboard
        )

        analytics.cart_cleared(user_id)
        await cb.answer("🗑️ Корзина очищена")

    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        await cb.answer("❌ Ошибка очистки", show_alert=True)

@router.callback_query(F.data == "cart:checkout")
async def handle_cart_checkout(cb: CallbackQuery):
    """Start checkout process"""
    try:
        user_id = cb.from_user.id
        cart = await cart_store.get(user_id)

        if not cart.items:
            await cb.answer("Корзина пуста", show_alert=True)
            return

        # Simple checkout - just show links
        text = f"{CHECKOUT_TITLE}\n\n"

        links = []
        for item in cart.items.values():
            links.append(f"• {item.name}: {item.link}")

        text += f"{CHECKOUT_LINKS_READY}\n\n" + "\n".join(links)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в корзину", callback_data="cart:open")]
        ])

        await safe_edit_message_text(
            cb.message.chat.id,
            cb.message.message_id,
            text,
            reply_markup=keyboard
        )

        analytics.checkout_started(user_id, len(cart.items), cart.subtotal / 100)
        analytics.checkout_links_generated(user_id, len(links))

        await cb.answer("✅ Ссылки готовы")

    except Exception as e:
        logger.error(f"Error in checkout: {e}")
        await cb.answer("❌ Ошибка оформления", show_alert=True)

@router.callback_query(F.data == "cart:back_reco")
async def handle_cart_back_reco(cb: CallbackQuery):
    """Go back to recommendations"""
    try:
        # This should trigger showing recommendations again
        # For now, just show a placeholder
        text = "💄 Возврат к рекомендациям\n\nВыберите категорию для просмотра средств:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧴 Очищение", callback_data="rec:more:cleanser:1")],
            [InlineKeyboardButton(text="💧 Тоник", callback_data="rec:more:toner:1")],
            [InlineKeyboardButton(text="✨ Сыворотки", callback_data="rec:more:serum:1")],
            [InlineKeyboardButton(text="⬅️ Назад в корзину", callback_data="cart:open")]
        ])

        await safe_edit_message_text(
            cb.message.chat.id,
            cb.message.message_id,
            text,
            reply_markup=keyboard
        )

        await cb.answer("💄 Рекомендации")

    except Exception as e:
        logger.error(f"Error going back to recommendations: {e}")
        await cb.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("cart:add:"))
async def handle_cart_add(cb: CallbackQuery):
    """Add item to cart from recommendations"""
    try:
        # Format: cart:add:<pid>:<vid>
        parts = cb.data.split(":")
        if len(parts) < 4:
            await cb.answer("❌ Неверный формат")
            return

        product_id = parts[2]
        variant_id = parts[3] if parts[3] != "none" else None
        user_id = cb.from_user.id

        # Create cart item (mock data - should come from real catalog)
        item = CartItem(
            product_id=product_id,
            variant_id=variant_id,
            name=f"Продукт {product_id}",
            price=1990,  # 19.90 RUB
            currency="RUB",
            qty=1,
            source="goldapple",
            link=f"https://goldapple.ru/products/{product_id}",
            meta={"category": "skincare"}
        )

        # Validate item exists and is available
        # TODO: Check against real catalog

        # Add to cart
        cart = await cart_store.add(user_id, item)

        analytics.cart_item_added(user_id, product_id, variant_id or "", "goldapple", item.price / 100)

        await cb.answer(MSG_ADDED, show_alert=False)

    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        await cb.answer("❌ Ошибка добавления", show_alert=True)

# Export router
__all__ = ["router"]
