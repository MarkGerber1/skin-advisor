from __future__ import annotations

import os
from typing import Dict, Optional, Tuple

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.cart_store import get_cart_store
from bot.utils.security import sanitize_message
from i18n.ru import (
    CART_EMPTY,
    CART_ITEM_LINE,
    CART_SUBTOTAL_LABEL,
    CART_TITLE,
    MSG_CART_EMPTY_AFTER_CLEAR,
    MSG_CART_ITEM_ADDED,
    MSG_CART_ITEM_REMOVED,
    MSG_CART_UPDATED,
    MSG_INVALID_VARIANT,
    MSG_UNKNOWN_PRODUCT,
    MSG_CART_READY_FOR_CHECKOUT,
    BTN_CART_DECREASE,
    BTN_CART_DELETE,
    BTN_CART_INCREASE,
    BTN_CART_CLEAR,
    BTN_CART_CONTINUE,
    BTN_CART_CHECKOUT,
)

try:
    from engine.analytics import (
        cart_cleared,
        cart_item_added,
        cart_item_removed,
        cart_opened,
        cart_qty_changed,
        checkout_started,
    )

    def _log_event(func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - diagnostics only
            print(f"analytics error: {exc}")

except ImportError:  # pragma: no cover - analytics optional

    def _log_event(*args, **kwargs):  # type: ignore
        return None


from engine.selector import SelectorV2
from engine.catalog_store import CatalogStore

router = Router()
store = get_cart_store()
_selector = SelectorV2()
_catalog_store: Optional[CatalogStore] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _catalog() -> Optional[CatalogStore]:
    global _catalog_store
    if _catalog_store is None:
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        try:
            _catalog_store = CatalogStore.instance(catalog_path)
        except Exception as exc:  # pragma: no cover - diagnostics only
            print(f"Catalog load error: {exc}")
            _catalog_store = None
    return _catalog_store


def _money(value: Optional[float], currency: str) -> str:
    if value is None:
        return "—"
    amount = f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"
    amount = amount.replace(",", " ")
    symbol = "₽" if currency.upper() in {"RUB", "RUR"} else currency.upper()
    return f"{amount} {symbol}"


def _encode(product_id: str, variant_id: Optional[str]) -> str:
    variant = variant_id or "default"
    return f"{product_id}:{variant}"


def _decode(key: str) -> Tuple[str, Optional[str]]:
    parts = key.split(":", 1)
    product_id = parts[0]
    variant_id = parts[1] if len(parts) > 1 and parts[1] != "default" else None
    return product_id, variant_id


def _compose_cart_view(user_id: int) -> Tuple[str, InlineKeyboardMarkup]:
    items = store.get_cart(user_id)
    total_qty, total_price, currency = store.get_cart_total(user_id)

    if not items:
        empty_text = sanitize_message(CART_EMPTY)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=BTN_CART_CONTINUE, callback_data="cart:back")]
            ]
        )
        return empty_text, keyboard

    lines = [CART_TITLE, ""]
    keyboard_rows = []

    for index, item in enumerate(items, start=1):
        unit_price = _money(item.price, item.currency)
        subtotal = _money(item.subtotal(), item.currency)
        variant_hint = f" ({item.variant_name})" if item.variant_name else ""
        lines.append(
            CART_ITEM_LINE.format(
                index=index,
                name=item.name or item.product_id,
                variant=variant_hint,
                price=unit_price,
                qty=item.quantity,
                total=subtotal,
            )
        )

        key = _encode(item.product_id, item.variant_id)
        keyboard_rows.append(
            [
                InlineKeyboardButton(text=BTN_CART_DECREASE, callback_data=f"cart:dec:{key}"),
                InlineKeyboardButton(text=str(item.quantity), callback_data="noop"),
                InlineKeyboardButton(text=BTN_CART_INCREASE, callback_data=f"cart:inc:{key}"),
                InlineKeyboardButton(text=BTN_CART_DELETE, callback_data=f"cart:rm:{key}"),
            ]
        )

    lines.append("")
    lines.append(
        CART_SUBTOTAL_LABEL.format(
            qty=total_qty,
            total=_money(total_price, currency),
        )
    )

    keyboard_rows.append([InlineKeyboardButton(text=BTN_CART_CLEAR, callback_data="cart:clr")])
    keyboard_rows.append([InlineKeyboardButton(text=BTN_CART_CONTINUE, callback_data="cart:back")])
    keyboard_rows.append(
        [InlineKeyboardButton(text=BTN_CART_CHECKOUT, callback_data="cart:checkout")]
    )

    text = sanitize_message("\n".join(lines))
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    return text, markup


def _resolve_product(product_id: str) -> Optional[Dict]:
    try:
        products = _selector.select_products(product_id=product_id)
        if products:
            return products[0]
    except TypeError:
        pass
    except Exception as exc:  # pragma: no cover - diagnostics only
        print(f"selector lookup failed for {product_id}: {exc}")

    catalog = _catalog()
    if not catalog:
        return None

    for product in catalog.get():
        pid = getattr(product, "key", getattr(product, "id", ""))
        if str(pid) == product_id:
            return product.dict() if hasattr(product, "dict") else product
    return None


def _validate_variant(product: Dict, variant_id: Optional[str]) -> bool:
    if not variant_id:
        return True
    variants = product.get("variants") or []
    return any(str(v.get("id")) == variant_id for v in variants)


def _variant_name(product: Dict, variant_id: Optional[str]) -> Optional[str]:
    if not variant_id:
        return None
    for variant in product.get("variants", []):
        if str(variant.get("id")) == variant_id:
            return variant.get("name")
    return None


def _cart_answer(cb: CallbackQuery, text: str) -> None:
    try:
        cb.answer(text)
    except TelegramBadRequest:
        pass


async def _show_cart(target: CallbackQuery | Message) -> None:
    if isinstance(target, CallbackQuery):
        user_id = target.from_user.id
    else:
        user_id = target.from_user.id

    text, markup = _compose_cart_view(user_id)

    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest:
            await target.message.answer(text, reply_markup=markup)
        _log_event(cart_opened, user_id)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)
        _log_event(cart_opened, user_id)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "cart:open")
async def cart_open(cb: CallbackQuery) -> None:
    await _show_cart(cb)


@router.callback_query(F.data.startswith("cart:add:"))
async def cart_add(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    _, payload = cb.data.split("cart:add:", 1)
    product_id, variant_id = _decode(payload)

    product = _resolve_product(product_id)
    if not product:
        _cart_answer(cb, MSG_UNKNOWN_PRODUCT)
        return

    if variant_id and not _validate_variant(product, variant_id):
        _cart_answer(cb, MSG_INVALID_VARIANT)
        return

    item = store.add_item(
        user_id,
        product_id,
        variant_id=variant_id,
        name=product.get("name", product_id),
        brand=product.get("brand"),
        variant_name=_variant_name(product, variant_id),
        price=product.get("price"),
        currency=product.get("price_currency", product.get("currency", "RUB")),
        ref_link=product.get("ref_link") or product.get("link"),
        image_url=product.get("image_url"),
        source="recommendations",
    )

    _log_event(
        cart_item_added,
        user_id=user_id,
        product_id=item.product_id,
        variant_id=item.variant_id or "",
        quantity=item.quantity,
        price=item.price,
    )
    _cart_answer(cb, MSG_CART_ITEM_ADDED)
    await _show_cart(cb)


@router.callback_query(F.data.startswith("cart:inc:"))
async def cart_increment(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    _, payload = cb.data.split("cart:inc:", 1)
    product_id, variant_id = _decode(payload)

    success, new_qty = store.inc_quantity(user_id, product_id, variant_id)
    if not success:
        _cart_answer(cb, MSG_UNKNOWN_PRODUCT)
        return

    _log_event(
        cart_qty_changed,
        user_id=user_id,
        product_id=product_id,
        variant_id=variant_id or "",
        quantity=new_qty,
        action="increment",
    )
    await _show_cart(cb)


@router.callback_query(F.data.startswith("cart:dec:"))
async def cart_decrement(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    _, payload = cb.data.split("cart:dec:", 1)
    product_id, variant_id = _decode(payload)

    success, new_qty = store.dec_quantity(user_id, product_id, variant_id)
    if not success:
        _cart_answer(cb, MSG_UNKNOWN_PRODUCT)
        return

    action = "decrement" if new_qty > 0 else "remove"
    _log_event(
        cart_qty_changed,
        user_id=user_id,
        product_id=product_id,
        variant_id=variant_id or "",
        quantity=new_qty,
        action=action,
    )
    await _show_cart(cb)


@router.callback_query(F.data.startswith("cart:rm:"))
async def cart_remove(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    _, payload = cb.data.split("cart:rm:", 1)
    product_id, variant_id = _decode(payload)

    if not store.remove_item(user_id, product_id, variant_id):
        _cart_answer(cb, MSG_UNKNOWN_PRODUCT)
        return

    _log_event(
        cart_item_removed,
        user_id=user_id,
        product_id=product_id,
        variant_id=variant_id or "",
    )
    _cart_answer(cb, MSG_CART_ITEM_REMOVED)
    await _show_cart(cb)


@router.callback_query(F.data == "cart:clr")
async def cart_clear(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    removed = store.clear_cart(user_id)
    _log_event(cart_cleared, user_id=user_id, items_removed=removed)
    _cart_answer(cb, MSG_CART_EMPTY_AFTER_CLEAR)
    await _show_cart(cb)


@router.callback_query(F.data == "cart:back")
async def cart_back_to_recommendations(cb: CallbackQuery) -> None:
    try:
        from bot.handlers.recommendations import show_main_recommendations

        await show_main_recommendations(cb)
    except Exception:
        await cb.message.answer(MSG_CART_UPDATED)
        await cb.answer()


@router.callback_query(F.data == "cart:checkout")
async def cart_checkout(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    cart = store.get_cart(user_id)
    if not cart:
        _cart_answer(cb, MSG_CART_EMPTY_AFTER_CLEAR)
        await _show_cart(cb)
        return

    _log_event(checkout_started, user_id=user_id)
    await cb.message.edit_text(
        sanitize_message(MSG_CART_READY_FOR_CHECKOUT),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=BTN_CART_CONTINUE, callback_data="cart:back")],
                [InlineKeyboardButton(text=BTN_CART_CHECKOUT, callback_data="cart:open")],
            ]
        ),
    )
    await cb.answer()


# DEPRECATED: This functionality moved to cart_v2
# @router.message(F.text == "Корзина")
# async def cart_message_entry(message: Message) -> None:
#     await _show_cart(message)


async def show_cart(message: Message, state=None) -> None:
    """Backward compatible entrypoint - redirects to cart_v2."""
    try:
        from bot.handlers.cart_v2 import show_cart as show_cart_v2

        await show_cart_v2(message, state)
    except ImportError:
        # Fallback to old implementation if cart_v2 not available
        await _show_cart(message)
