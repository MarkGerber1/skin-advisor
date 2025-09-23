"""
пїЅпїЅ Cart v2 Handler

Complete cart flow: recommendations в†’ cart в†’ checkout
Unified cart:* callbacks with proper UX and analytics
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup

from services.cart_store import CartStore, CartItem
from bot.utils.security import safe_edit_message_text
from engine.analytics import get_analytics_tracker
from i18n.ru import *

logger = logging.getLogger(__name__)
router = Router()

# Global instances
cart_store = CartStore()
analytics = get_analytics_tracker()


def format_price(price: float, currency: str = "RUB") -> str:
    """Format price with spaces for thousands"""
    if currency == "RUB":
        rubles = int(price)
        return f"{rubles:,} в‚Ѕ".replace(",", " ")
    return f"{price:.2f} {currency}"


def format_cart_item(item: CartItem) -> str:
    """Format cart item for display"""
    price_str = format_price(item.price or 0, item.currency)
    total = (item.price or 0) * item.qty
    total_str = format_price(total, item.currency)

    variant_text = ""
    if item.variant_name:
        variant_text = f" вЂў {item.variant_name}"
    elif item.variant_id:
        variant_text = f" вЂў Р’Р°СЂРёР°РЅС‚ {item.variant_id}"

    return f"{item.name}{variant_text}\n{price_str} Г— {item.qty} = {total_str}"


def render_cart(cart_items: list[CartItem]) -> str:
    """Render full cart view"""
    if not cart_items:
        return CART_EMPTY

    # Calculate totals
    total_qty = sum(item.qty for item in cart_items)
    total_price = sum((item.price or 0) * item.qty for item in cart_items)
    currency = next((item.currency for item in cart_items if item.currency), "RUB")

    lines = [CART_TITLE]
    for item in cart_items:
        lines.append("")
        lines.append(format_cart_item(item))

    lines.append("")
    lines.append(f"РС‚РѕРіРѕ: {total_qty} С€С‚ Г— {format_price(total_price, currency)}")
    return "\n".join(lines)


def build_cart_keyboard(cart_items: list[CartItem]) -> InlineKeyboardMarkup:
    """Build cart keyboard with controls"""
    keyboard = InlineKeyboardBuilder()

    # Item controls
    for item in cart_items:
        keyboard.row(
            InlineKeyboardButton(
                text="вћ–", callback_data=f"cart:dec:{item.product_id}:{item.variant_id or 'none'}"
            ),
            InlineKeyboardButton(text=f" {item.qty} ", callback_data="noop"),
            InlineKeyboardButton(
                text="вћ•", callback_data=f"cart:inc:{item.product_id}:{item.variant_id or 'none'}"
            ),
            InlineKeyboardButton(
                text="н·‘", callback_data=f"cart:rm:{item.product_id}:{item.variant_id or 'none'}"
            ),
        )

    # Cart actions
    if cart_items:
        keyboard.row(
            InlineKeyboardButton(text="н·№ РћС‡РёСЃС‚РёС‚СЊ", callback_data="cart:clr"),
            InlineKeyboardButton(
                text="нґЌ РџСЂРѕРґРѕР»Р¶РёС‚СЊ РїРѕРґР±РѕСЂ", callback_data="cart:back_reco"
            ),
            InlineKeyboardButton(text="н·ѕ РћС„РѕСЂРјР»РµРЅРёРµ", callback_data="cart:checkout"),
        )
    else:
        keyboard.row(
            InlineKeyboardButton(
                text="нґЌ РџСЂРѕРґРѕР»Р¶РёС‚СЊ РїРѕРґР±РѕСЂ", callback_data="cart:back_reco"
            )
        )

    return keyboard.as_markup()


@router.callback_query(F.data == "cart:open")
async def handle_cart_open(cb: CallbackQuery):
    """Open cart view"""
    user_id = cb.from_user.id

    try:
        cart_items = cart_store.get_cart(user_id)
        analytics.cart_opened(user_id)

        text = render_cart(cart_items)
        keyboard = build_cart_keyboard(cart_items)

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard
        )
        await cb.answer()

    except Exception as e:
        logger.error(f"Error opening cart: {e}")
        await cb.answer("вќЊ РћС€РёР±РєР° РѕС‚РєСЂС‹С‚РёСЏ РєРѕСЂР·РёРЅС‹", show_alert=True)


@router.callback_query(F.data.startswith("cart:add:"))
async def handle_cart_add(cb: CallbackQuery):
    """Add item to cart from recommendations"""
    try:
        # Format: cart:add:<pid>:<vid>
        parts = cb.data.split(":")
        if len(parts) < 4:
            await cb.answer("вќЊ РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚")
            return

        product_id = parts[2]
        variant_id = parts[3] if parts[3] != "none" else None
        user_id = cb.from_user.id

        # TODO: Validate variant_id belongs to product_id
        # For now, create mock item
        item, currency_conflict = cart_store.add_item(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id,
            name=f"РџСЂРѕРґСѓРєС‚ {product_id}",
            price=1990.0,  # 1990 RUB
            currency="RUB",
            source="goldapple",
            ref_link=f"https://goldapple.ru/products/{product_id}",
        )

        if currency_conflict:
            await cb.answer(
                "вљ пёЏ Р’Р°Р»СЋС‚РЅС‹Р№ РєРѕРЅС„Р»РёРєС‚ - С‚РѕРІР°СЂС‹ СЃ СЂР°Р·РЅРѕР№ РІР°Р»СЋС‚РѕР№",
                show_alert=True,
            )
            return

        analytics.cart_item_added(
            user_id, product_id, variant_id or "", item.price, item.currency, item.source or ""
        )
        await cb.answer(MSG_CART_ITEM_ADDED)

    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        await cb.answer("вќЊ РћС€РёР±РєР° РґРѕР±Р°РІР»РµРЅРёСЏ", show_alert=True)


@router.callback_query(F.data.startswith("cart:inc:"))
async def handle_cart_inc(cb: CallbackQuery):
    """Increase item quantity"""
    try:
        parts = cb.data.split(":")
        if len(parts) < 4:
            await cb.answer("вќЊ РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚")
            return

        product_id = parts[2]
        variant_id = parts[3] if parts[3] != "none" else None
        user_id = cb.from_user.id

        cart_items = cart_store.get_cart(user_id)
        item = next(
            (i for i in cart_items if i.product_id == product_id and i.variant_id == variant_id),
            None,
        )
        if not item:
            await cb.answer("вќЊ РўРѕРІР°СЂ РЅРµ РЅР°Р№РґРµРЅ")
            return

        old_qty = item.qty
        cart_store.update_quantity(user_id, product_id, variant_id, item.qty + 1)

        analytics.cart_qty_changed(user_id, f"{product_id}:{variant_id}", old_qty, item.qty + 1)
        await cb.answer(f"вћ• РљРѕР»РёС‡РµСЃС‚РІРѕ: {item.qty + 1}")

        # Update cart view
        cart_items = cart_store.get_cart(user_id)
        text = render_cart(cart_items)
        keyboard = build_cart_keyboard(cart_items)

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error increasing quantity: {e}")
        await cb.answer("вќЊ РћС€РёР±РєР°", show_alert=True)


@router.callback_query(F.data.startswith("cart:dec:"))
async def handle_cart_dec(cb: CallbackQuery):
    """Decrease item quantity"""
    try:
        parts = cb.data.split(":")
        if len(parts) < 4:
            await cb.answer("вќЊ РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚")
            return

        product_id = parts[2]
        variant_id = parts[3] if parts[3] != "none" else None
        user_id = cb.from_user.id

        cart_items = cart_store.get_cart(user_id)
        item = next(
            (i for i in cart_items if i.product_id == product_id and i.variant_id == variant_id),
            None,
        )
        if not item:
            await cb.answer("вќЊ РўРѕРІР°СЂ РЅРµ РЅР°Р№РґРµРЅ")
            return

        if item.qty <= 1:
            # Remove item if qty == 1
            cart_store.remove_item(user_id, product_id, variant_id)
            analytics.cart_item_removed(user_id, f"{product_id}:{variant_id}")
            await cb.answer("н·‘ РўРѕРІР°СЂ СѓРґР°Р»С‘РЅ")
        else:
            old_qty = item.qty
            cart_store.update_quantity(user_id, product_id, variant_id, item.qty - 1)
            analytics.cart_qty_changed(user_id, f"{product_id}:{variant_id}", old_qty, item.qty - 1)
            await cb.answer(f"вћ– РљРѕР»РёС‡РµСЃС‚РІРѕ: {item.qty - 1}")

        # Update cart view
        cart_items = cart_store.get_cart(user_id)
        text = render_cart(cart_items)
        keyboard = build_cart_keyboard(cart_items)

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error decreasing quantity: {e}")
        await cb.answer("вќЊ РћС€РёР±РєР°", show_alert=True)


@router.callback_query(F.data.startswith("cart:rm:"))
async def handle_cart_rm(cb: CallbackQuery):
    """Remove item from cart"""
    try:
        parts = cb.data.split(":")
        if len(parts) < 4:
            await cb.answer("вќЊ РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚")
            return

        product_id = parts[2]
        variant_id = parts[3] if parts[3] != "none" else None
        user_id = cb.from_user.id

        if cart_store.remove_item(user_id, product_id, variant_id):
            analytics.cart_item_removed(user_id, f"{product_id}:{variant_id}")
            await cb.answer("н·‘ РўРѕРІР°СЂ СѓРґР°Р»С‘РЅ")
        else:
            await cb.answer("вќЊ РўРѕРІР°СЂ РЅРµ РЅР°Р№РґРµРЅ")
            return

        # Update cart view
        cart_items = cart_store.get_cart(user_id)
        text = render_cart(cart_items)
        keyboard = build_cart_keyboard(cart_items)

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error removing item: {e}")
        await cb.answer("вќЊ РћС€РёР±РєР° СѓРґР°Р»РµРЅРёСЏ", show_alert=True)


@router.callback_query(F.data == "cart:clr")
async def handle_cart_clr(cb: CallbackQuery):
    """Clear entire cart"""
    try:
        user_id = cb.from_user.id
        removed_count = cart_store.clear_cart(user_id)
        analytics.cart_cleared(user_id)

        await cb.answer(f"н·№ РљРѕСЂР·РёРЅР° РѕС‡РёС‰РµРЅР° ({removed_count} С‚РѕРІР°СЂРѕРІ)")

        # Update cart view
        cart_items = cart_store.get_cart(user_id)
        text = render_cart(cart_items)
        keyboard = build_cart_keyboard(cart_items)

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        await cb.answer("вќЊ РћС€РёР±РєР° РѕС‡РёСЃС‚РєРё", show_alert=True)


@router.callback_query(F.data == "cart:checkout")
async def handle_cart_checkout(cb: CallbackQuery):
    """Show checkout screen"""
    try:
        user_id = cb.from_user.id
        cart_items = cart_store.get_cart(user_id)

        if not cart_items:
            await cb.answer("РљРѕСЂР·РёРЅР° РїСѓСЃС‚Р°")
            return

        analytics.checkout_started(user_id)

        # Generate checkout links with affiliate tags
        checkout_lines = [CHECKOUT_TITLE, "", CHECKOUT_LINKS_READY]

        for item in cart_items:
            if item.ref_link:
                # Add affiliate tag if needed
                affiliate_link = item.ref_link  # TODO: Add affiliate logic
                checkout_lines.append(f"вЂў {item.name} - {affiliate_link}")

        checkout_lines.append("")
        checkout_lines.append(MSG_CART_READY_FOR_CHECKOUT)

        text = "\n".join(checkout_lines)
        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            InlineKeyboardButton(text="нґ™ РќР°Р·Р°Рґ РІ РєРѕСЂР·РёРЅСѓ", callback_data="cart:open")
        )

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard.as_markup()
        )

    except Exception as e:
        logger.error(f"Error in checkout: {e}")
        await cb.answer("вќЊ РћС€РёР±РєР° РѕС„РѕСЂРјР»РµРЅРёСЏ", show_alert=True)


@router.callback_query(F.data == "cart:back_reco")
async def handle_cart_back_reco(cb: CallbackQuery):
    """Return to recommendations"""
    try:
        # TODO: Implement proper return to recommendations
        # For now, just show a placeholder
        text = (
            "нґЌ Р’РѕР·РІСЂР°С‚ Рє СЂРµРєРѕРјРµРЅРґР°С†РёСЏРј\n\nР’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
        )
        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            InlineKeyboardButton(text="нї  Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ", callback_data="back:main")
        )

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard.as_markup()
        )
        await cb.answer("Р’РѕР·РІСЂР°С‰Р°РµРјСЃСЏ Рє СЂРµРєРѕРјРµРЅРґР°С†РёСЏРј")

    except Exception as e:
        logger.error(f"Error returning to recommendations: {e}")
        await cb.answer("вќЊ РћС€РёР±РєР°", show_alert=True)


# Export router
__all__ = ["router"]
