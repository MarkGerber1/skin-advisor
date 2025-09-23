"""
🛒 Cart v2 Handler

Complete cart flow: recommendations → cart → checkout
Unified cart:* callbacks with proper UX and analytics
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from services.cart_store import CartStore, CartItem
from bot.utils.security import safe_edit_message_text
from engine.analytics import (
    cart_item_added,
    cart_opened,
    cart_qty_changed,
    cart_item_removed,
    cart_cleared,
    checkout_started,
)
from engine.catalog_store import CatalogStore
from i18n.ru import *

logger = logging.getLogger(__name__)
router = Router()

# Global instances
cart_store = CartStore()

# Catalog instance for product lookup
_catalog_store = None


def get_catalog_store():
    """Get catalog store instance"""
    global _catalog_store
    if _catalog_store is None:
        _catalog_store = CatalogStore.instance("assets/fixed_catalog.yaml")
    return _catalog_store


def find_product_by_id(product_id: str):
    """Find product by ID in catalog"""
    catalog = get_catalog_store().get()
    for product in catalog:
        if product.key == product_id:
            return product
    return None


def find_variant_by_id(product, variant_id: str):
    """Find variant by ID in product"""
    if not hasattr(product, "variants") or not product.variants:
        return None
    for variant in product.variants:
        if variant.id == variant_id:
            return variant
    return None


def format_price(price: float, currency: str = "RUB") -> str:
    """Format price with spaces for thousands"""
    if currency == "RUB":
        rubles = int(price)
        return f"{rubles:,} ₽".replace(",", " ")
    return f"{price:.2f} {currency}"


def format_cart_item(item: CartItem) -> str:
    """Format cart item for display"""
    price_str = format_price(item.price or 0, item.currency)
    total = (item.price or 0) * item.qty
    total_str = format_price(total, item.currency)

    variant_text = ""
    if item.variant_name:
        variant_text = f" • {item.variant_name}"
    elif item.variant_id:
        variant_text = f" • Вариант {item.variant_id}"

    return f"{item.name}{variant_text}\n{price_str} × {item.qty} = {total_str}"


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
    lines.append(f"Итого: {total_qty} шт × {format_price(total_price, currency)}")
    return "\n".join(lines)


def build_cart_keyboard(cart_items: list[CartItem]) -> InlineKeyboardMarkup:
    """Build cart keyboard with controls"""
    keyboard = InlineKeyboardBuilder()

    # Item controls
    for item in cart_items:
        keyboard.row(
            InlineKeyboardButton(
                text="➖", callback_data=f"cart:dec:{item.product_id}:{item.variant_id or 'none'}"
            ),
            InlineKeyboardButton(text=f" {item.qty} ", callback_data="noop"),
            InlineKeyboardButton(
                text="➕", callback_data=f"cart:inc:{item.product_id}:{item.variant_id or 'none'}"
            ),
            InlineKeyboardButton(
                text="🗑", callback_data=f"cart:rm:{item.product_id}:{item.variant_id or 'none'}"
            ),
        )

    # Cart actions
    if cart_items:
        keyboard.row(
            InlineKeyboardButton(text="🧹 Очистить", callback_data="cart:clr"),
            InlineKeyboardButton(text="🔎 Продолжить подбор", callback_data="cart:back_reco"),
            InlineKeyboardButton(text="🧾 Оформление", callback_data="cart:checkout"),
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text="🔎 Продолжить подбор", callback_data="cart:back_reco")
        )

    return keyboard.as_markup()


@router.callback_query(F.data == "cart:open")
async def handle_cart_open(cb: CallbackQuery):
    """Open cart view"""
    user_id = cb.from_user.id

    try:
        cart_items = cart_store.get_cart(user_id)

        cart_opened(user_id)

        text = render_cart(cart_items)

        keyboard = build_cart_keyboard(cart_items)

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard
        )
        await cb.answer()

    except Exception as e:
        logger.error(f"Error opening cart: {e}")
        await cb.answer("❌ Ошибка открытия корзины", show_alert=True)


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

        # 🔍 Найти реальный товар в каталоге
        product = find_product_by_id(product_id)
        if not product:
            await cb.answer("❌ Товар не найден", show_alert=True)
            return

        # 🔍 Проверить вариант товара (если указан)
        if variant_id and variant_id != "default":
            variant = find_variant_by_id(product, variant_id)
            if not variant:
                await cb.answer("❌ Вариант товара недоступен", show_alert=True)
                return
            # Используем данные варианта
            name = f"{product.title} - {variant.name}"
            price = variant.price or product.price or 0
        else:
            # Используем базовые данные товара
            name = product.title
            price = product.price or 0

        # ✅ Добавить товар с реальными данными
        item, currency_conflict = cart_store.add_item(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id,
            name=name,
            price=float(price),
            currency="RUB",
            source=product.source or "goldapple",
            ref_link=product.buy_url or f"https://goldapple.ru/products/{product_id}",
            image_url=product.image_url,
        )

        if currency_conflict:
            await cb.answer("⚠️ В корзине уже есть товары в другой валюте", show_alert=True)
            return

        cart_item_added(
            user_id, product_id, variant_id or "", item.price, item.currency, item.source or ""
        )
        await cb.answer(MSG_CART_ITEM_ADDED)

    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        await cb.answer("❌ Ошибка добавления", show_alert=True)


@router.callback_query(F.data.startswith("cart:inc:"))
async def handle_cart_inc(cb: CallbackQuery):
    """Increase item quantity"""
    try:
        parts = cb.data.split(":")
        if len(parts) < 4:
            await cb.answer("❌ Неверный формат")
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
            await cb.answer("❌ Товар не найден")
            return

        old_qty = item.qty
        cart_store.update_quantity(user_id, product_id, variant_id, item.qty + 1)

        cart_qty_changed(user_id, f"{product_id}:{variant_id}", old_qty, item.qty + 1)
        await cb.answer(f"➕ Количество: {item.qty + 1}")

        # Update cart view
        cart_items = cart_store.get_cart(user_id)
        text = render_cart(cart_items)
        keyboard = build_cart_keyboard(cart_items)

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error increasing quantity: {e}")
        await cb.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("cart:dec:"))
async def handle_cart_dec(cb: CallbackQuery):
    """Decrease item quantity"""
    try:
        parts = cb.data.split(":")
        if len(parts) < 4:
            await cb.answer("❌ Неверный формат")
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
            await cb.answer("❌ Товар не найден")
            return

        if item.qty <= 1:
            # Remove item if qty == 1
            cart_store.remove_item(user_id, product_id, variant_id)
            cart_item_removed(user_id, f"{product_id}:{variant_id}")
            await cb.answer("🗑 Товар удалён")
        else:
            old_qty = item.qty
            cart_store.update_quantity(user_id, product_id, variant_id, item.qty - 1)
            cart_qty_changed(user_id, f"{product_id}:{variant_id}", old_qty, item.qty - 1)
            await cb.answer(f"➖ Количество: {item.qty - 1}")

        # Update cart view
        cart_items = cart_store.get_cart(user_id)
        text = render_cart(cart_items)
        keyboard = build_cart_keyboard(cart_items)

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error decreasing quantity: {e}")
        await cb.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("cart:rm:"))
async def handle_cart_rm(cb: CallbackQuery):
    """Remove item from cart"""
    try:
        parts = cb.data.split(":")
        if len(parts) < 4:
            await cb.answer("❌ Неверный формат")
            return

        product_id = parts[2]
        variant_id = parts[3] if parts[3] != "none" else None
        user_id = cb.from_user.id

        if cart_store.remove_item(user_id, product_id, variant_id):
            cart_item_removed(user_id, f"{product_id}:{variant_id}")
            await cb.answer("🗑 Товар удалён")
        else:
            await cb.answer("❌ Товар не найден")
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
        await cb.answer("❌ Ошибка удаления", show_alert=True)


@router.callback_query(F.data == "cart:clr")
async def handle_cart_clr(cb: CallbackQuery):
    """Clear entire cart"""
    try:
        user_id = cb.from_user.id
        removed_count = cart_store.clear_cart(user_id)
        cart_cleared(user_id, removed_count)

        await cb.answer(f"🧹 Корзина очищена ({removed_count} товаров)")

        # Update cart view
        cart_items = cart_store.get_cart(user_id)
        text = render_cart(cart_items)
        keyboard = build_cart_keyboard(cart_items)

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        await cb.answer("❌ Ошибка очистки", show_alert=True)


@router.callback_query(F.data == "cart:checkout")
async def handle_cart_checkout(cb: CallbackQuery):
    """Show checkout screen"""
    try:
        user_id = cb.from_user.id
        cart_items = cart_store.get_cart(user_id)

        if not cart_items:
            await cb.answer("Корзина пуста")
            return

        checkout_started(user_id)

        # Generate checkout links with affiliate tags
        checkout_lines = [CHECKOUT_TITLE, "", CHECKOUT_LINKS_READY]

        for item in cart_items:
            if item.ref_link:
                # Add affiliate tag if needed
                affiliate_link = item.ref_link  # TODO: Add affiliate logic
                checkout_lines.append(f"• {item.name} - {affiliate_link}")

        checkout_lines.append("")
        checkout_lines.append(MSG_CART_READY_FOR_CHECKOUT)

        text = "\n".join(checkout_lines)
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="⬅️ Назад в корзину", callback_data="cart:open"))

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard.as_markup()
        )

    except Exception as e:
        logger.error(f"Error in checkout: {e}")
        await cb.answer("❌ Ошибка оформления", show_alert=True)


@router.callback_query(F.data == "cart:back_reco")
async def handle_cart_back_reco(cb: CallbackQuery):
    """Return to recommendations"""
    try:
        # TODO: Implement proper return to recommendations
        # For now, just show a placeholder
        text = "🔎 Возврат к рекомендациям\n\nВыберите действие:"
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back:main"))

        await safe_edit_message_text(
            cb.message.chat.id, cb.message.message_id, text, reply_markup=keyboard.as_markup()
        )
        await cb.answer("Возвращаемся к рекомендациям")

    except Exception as e:
        logger.error(f"Error returning to recommendations: {e}")
        await cb.answer("❌ Ошибка", show_alert=True)


async def show_cart(message: Message, state=None) -> None:
    """Backward compatible entrypoint for other modules - show cart via message."""
    user_id = message.from_user.id

    try:
        cart_items = cart_store.get_cart(user_id)

        cart_opened(user_id)

        text = render_cart(cart_items)

        keyboard = build_cart_keyboard(cart_items)

        await message.answer(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error showing cart: {e}")
        await message.answer("❌ Ошибка открытия корзины")


# Export router
__all__ = ["router", "show_cart"]
