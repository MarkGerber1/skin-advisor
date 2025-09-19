# -*- coding: utf-8 -*-
"""Cart handlers: единый UX, undo, быстрые рекомендации и checkout."""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.cart_store import CartItem, get_cart_store
from engine.selector import SelectorV2
from engine.business_metrics import get_metrics_tracker
from bot.utils.security import sanitize_message
from bot.ui.keyboards import main_menu
from i18n.ru import (
    BTN_ADD,
    BTN_BACK_RECO,
    BTN_CHECKOUT,
    BTN_CLEAR,
    BTN_DEC,
    BTN_DEL,
    BTN_DETAILS,
    BTN_INC,
    BTN_MORE,
    BTN_UNDO,
    BTN_VIEW_CART,
    CART_EMPTY,
    CART_TITLE,
    CART_TOTAL,
    CHECKOUT_LINKS_READY,
    CHECKOUT_NO_LINK,
    CHECKOUT_TITLE,
    MSG_ADDED,
    MSG_BAD_VARIANT,
    MSG_CART_UPDATED,
    MSG_REMOVED,
    MSG_UNAVAILABLE,
    MSG_UNDO_EXPIRED,
    MSG_UNDO_SUCCESS,
)

try:
    from engine.analytics import (
        cart_cleared,
        cart_item_added,
        cart_item_removed,
        cart_opened,
        cart_qty_changed,
        checkout_links_generated,
        checkout_started,
    )
    ANALYTICS_AVAILABLE = True
except ImportError:  # pragma: no cover
    ANALYTICS_AVAILABLE = False

    def cart_cleared(*args, **kwargs):
        return None

    def cart_item_added(*args, **kwargs):
        return None

    def cart_item_removed(*args, **kwargs):
        return None

    def cart_opened(*args, **kwargs):
        return None

    def cart_qty_changed(*args, **kwargs):
        return None

    def checkout_links_generated(*args, **kwargs):
        return None

    def checkout_started(*args, **kwargs):
        return None

logger = logging.getLogger(__name__)
router = Router()
store = get_cart_store()
selector = SelectorV2()
metrics = get_metrics_tracker()

NARROW_NBSP = "\u202f"
UNDO_TTL_SECONDS = 5
SOURCE_PRIORITY = {
    "goldapple": 0,
    "gold_apple": 0,
    "gold-apple": 0,
    "official": 1,
    "official_ru": 1,
    "brand": 1,
    "ru_marketplace": 2,
    "marketplace": 2,
    "wildberries": 2,
    "ozon": 2,
    "intl": 3,
    "international": 3,
}
CURRENCY_SYMBOLS = {
    "RUB": "₽",
    "RUR": "₽",
    "USD": "$",
    "EUR": "€",
}

_last_operations: Dict[str, float] = {}
_undo_buffer: Dict[str, Tuple[int, CartItem]] = {}


def _format_price(value: Optional[float], currency: Optional[str]) -> str:
    if value is None:
        return "—"
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError):
        dec = Decimal(0)
    if dec == dec.quantize(Decimal("1")):
        amount = f"{int(dec):,}".replace(",", NARROW_NBSP)
    else:
        amount = f"{dec:.2f}".replace(",", NARROW_NBSP)
    symbol = CURRENCY_SYMBOLS.get((currency or "RUB").upper(), (currency or "").upper())
    return f"{amount}{NARROW_NBSP}{symbol}".strip()


def _encode_key(product_id: str, variant_id: Optional[str]) -> str:
    from urllib.parse import quote_plus

    pid = quote_plus(product_id or "")
    vid = quote_plus(variant_id or "") if variant_id else ""
    return f"{pid}:{vid}"


def _decode_key(key: str) -> Tuple[str, Optional[str]]:
    from urllib.parse import unquote_plus

    if ":" in key:
        pid, vid = key.split(":", 1)
    else:
        pid, vid = key, ""
    return unquote_plus(pid), unquote_plus(vid) or None


def _normalize_source(source: Optional[str]) -> str:
    if not source:
        return "unknown"
    return source.replace(" ", "_").lower()


def _debounce(user_id: int, token: str, ttl: float = 1.5) -> bool:
    loop = asyncio.get_running_loop()
    now = loop.time()
    key = f"{user_id}:{token}"
    last = _last_operations.get(key)
    if last and now - last < ttl:
        return False
    _last_operations[key] = now
    return True


async def _load_recommendations(user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    try:
        from engine.models import UserProfile
        from engine.catalog_store import CatalogStore
        from bot.handlers.user_profile_store import get_user_profile_store
        from bot.handlers.fsm_coordinator import get_fsm_coordinator

        profile_store = get_user_profile_store()
        profile = profile_store.load_profile(user_id)

        if not profile:
            coordinator = get_fsm_coordinator()
            session = await coordinator.get_session(user_id)
            data = session.flow_data if session else {}
            profile = UserProfile(
                user_id=user_id,
                skin_type=data.get("skin_type", "normal"),
                concerns=data.get("concerns", []),
                season=data.get("season", "spring"),
                undertone=data.get("undertone", "neutral"),
                contrast=data.get("contrast", "medium"),
            )

        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()
        result = selector.select_products_v2(profile, catalog, partner_code="S1") or {}

        buckets: List[List[Dict[str, Any]]] = []
        for group in (result.get("skincare"), result.get("makeup")):
            if isinstance(group, dict):
                buckets.extend(list(group.values()))

        flat: Dict[str, Dict[str, Any]] = {}
        for bucket in buckets:
            if isinstance(bucket, list):
                for product in bucket:
                    if not isinstance(product, dict):
                        continue
                    pid = str(product.get("id")) if product.get("id") else None
                    if pid and pid not in flat:
                        flat[pid] = product

        ordered = sorted(
            flat.values(),
            key=lambda prod: (
                SOURCE_PRIORITY.get(_normalize_source(prod.get("source")), 10),
                float(prod.get("price") or prod.get("price_value") or 0),
            ),
        )
        if limit is not None:
            ordered = ordered[:limit]
        return ordered
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to load recommendations: %s", exc)
        return []


@dataclass
class CartView:
    text: str
    markup: InlineKeyboardMarkup
    total_qty: int
    total_price: float
    currency: str
    currency_warning: bool


async def _compose_cart_view(user_id: int) -> CartView:
    items = store.get_cart(user_id)
    if not items:
        return await _render_empty_cart(user_id)

    total_qty, total_price, currency = store.get_cart_total(user_id)
    currencies = {item.currency or currency for item in items if item.price}
    currency_warning = len(currencies) > 1

    lines: List[str] = [f"{CART_TITLE} ({total_qty})", ""]
    keyboard_rows: List[List[InlineKeyboardButton]] = []

    for index, item in enumerate(items, start=1):
        title_parts = [item.brand or "", item.name or item.product_id]
        title = " ".join(part for part in title_parts if part).strip() or item.product_id
        lines.append(f"{index}) {title}")

        if item.variant_name:
            lines.append(f"   Вариант: {item.variant_name}")

        price_text = _format_price(item.price, item.currency)
        line_total = _format_price((item.price or 0) * item.qty, item.currency)
        lines.append(f"   {price_text} × {item.qty} = {line_total}")

        if item.in_stock is False:
            lines.append("   · Нет в наличии")

        source_label = item.meta.get("source_label") if isinstance(item.meta, dict) else None
        if source_label:
            lines.append(f"   · Источник: {source_label}")

        lines.append("")

        key = _encode_key(item.product_id, item.variant_id)
        keyboard_rows.append(
            [
                InlineKeyboardButton(text=BTN_DEC, callback_data=f"cart:dec:{key}"),
                InlineKeyboardButton(text=str(item.qty), callback_data=f"cart:qty:{key}"),
                InlineKeyboardButton(text=BTN_INC, callback_data=f"cart:inc:{key}"),
                InlineKeyboardButton(text=BTN_DEL, callback_data=f"cart:del:{key}"),
            ]
        )

    lines.append(CART_TOTAL.format(total=_format_price(total_price, currency)))
    if currency_warning:
        lines.append("⚠ В корзине товары с разной валютой")

    keyboard_rows.append(
        [
            InlineKeyboardButton(text=BTN_BACK_RECO, callback_data="cart:back_reco"),
            InlineKeyboardButton(text=BTN_CHECKOUT, callback_data="cart:checkout"),
        ]
    )
    keyboard_rows.append([InlineKeyboardButton(text=BTN_CLEAR, callback_data="cart:clear")])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    text = sanitize_message("\n".join(lines).strip())
    return CartView(text=text, markup=markup, total_qty=total_qty, total_price=total_price, currency=currency, currency_warning=currency_warning)


async def _render_empty_cart(user_id: int) -> CartView:
    picks = await _load_recommendations(user_id, limit=3)
    lines = [CART_EMPTY, ""]
    buttons: List[List[InlineKeyboardButton]] = []

    if picks:
        lines.append("Предложения для вас:")
        for product in picks:
            title = " ".join(filter(None, [product.get("brand"), product.get("name")])).strip() or str(product.get("id"))
            price_text = _format_price(product.get("price"), product.get("currency"))
            lines.append(f"• {title} — {price_text}")
            buttons.append([
                InlineKeyboardButton(
                    text=f"{BTN_ADD} {title[:24]}",
                    callback_data=f"cart:add:{_encode_key(str(product.get('id')), None)}",
                )
            ])
        lines.append("")

    buttons.append([InlineKeyboardButton(text=BTN_BACK_RECO, callback_data="cart:back_reco")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = sanitize_message("\n".join(lines).strip())
    return CartView(text=text, markup=markup, total_qty=0, total_price=0.0, currency="RUB", currency_warning=False)


async def show_cart(message: Message, state: Optional[FSMContext] = None) -> None:
    user_id = int(message.from_user.id) if message.from_user else 0
    if user_id == 0:
        await message.answer("Не удалось определить пользователя")
        return
    view = await _compose_cart_view(user_id)
    await message.answer(view.text, reply_markup=view.markup)
    await message.answer(MSG_CART_UPDATED, reply_markup=main_menu(cart_count=view.total_qty))


@router.callback_query(F.data == "cart:open")
async def handle_cart_open(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    view = await _compose_cart_view(user_id)
    await _edit_or_send(cb, view)
    await _answer(cb, MSG_CART_UPDATED)


@router.callback_query(F.data.startswith("cart:add:"))
async def handle_cart_add(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    payload = cb.data.split(":", 2)[2]
    product_id, variant_id = _decode_key(payload)

    product, alternatives = await _resolve_product(user_id, product_id)
    if not product:
        await _send_alternatives(cb, alternatives)
        return

    if variant_id and not _variant_exists(product, variant_id):
        await _answer(cb, MSG_BAD_VARIANT, alert=True)
        await _send_alternatives(cb, alternatives)
        return

    if not product.get("price") or not product.get("currency") or product.get("in_stock") is False:
        await _answer(cb, MSG_UNAVAILABLE, alert=True)
        await _send_alternatives(cb, alternatives)
        return

    cart_item = _build_cart_item(product, variant_id)
    stored = store.add_item(
        user_id=user_id,
        product_id=cart_item.product_id,
        variant_id=cart_item.variant_id,
        quantity=cart_item.qty,
        brand=cart_item.brand,
        name=cart_item.name,
        price=cart_item.price,
        currency=cart_item.currency,
        price_currency=cart_item.price_currency,
        ref_link=cart_item.ref_link,
        category=cart_item.category,
        variant_name=cart_item.variant_name,
        in_stock=cart_item.in_stock,
        image_url=cart_item.image_url,
        source=cart_item.source,
        meta=cart_item.meta,
    )

    price_cents = int(round((cart_item.price or 0) * 100))
    _track_metrics(
        "cart_add_success",
        user_id,
        {"product_id": cart_item.product_id, "variant_id": cart_item.variant_id, "price": cart_item.price},
    )
    _emit_analytics_added(user_id, cart_item.product_id, cart_item.variant_id, cart_item.source, price_cents)

    view = await _compose_cart_view(user_id)
    await _edit_or_send(cb, view)
    display_name = " ".join(filter(None, [stored.brand, stored.name])) or stored.product_id
    await _answer(cb, f"{MSG_ADDED}: {display_name}")


@router.callback_query(F.data.startswith("cart:inc:"))
async def handle_cart_inc(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    key = cb.data.split(":", 2)[2]
    if not _debounce(user_id, f"inc:{key}"):
        await _answer(cb, MSG_CART_UPDATED)
        return
    product_id, variant_id = _decode_key(key)
    success, new_qty = store.inc_quantity(user_id, product_id, variant_id, max_qty=99)
    if not success:
        await _answer(cb, MSG_UNAVAILABLE, alert=True)
        return
    view = await _compose_cart_view(user_id)
    await _edit_or_send(cb, view)
    cart_qty_changed(user_id, key, new_qty)
    await _answer(cb, MSG_CART_UPDATED)


@router.callback_query(F.data.startswith("cart:dec:"))
async def handle_cart_dec(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    key = cb.data.split(":", 2)[2]
    if not _debounce(user_id, f"dec:{key}"):
        await _answer(cb, MSG_CART_UPDATED)
        return
    product_id, variant_id = _decode_key(key)
    success, new_qty, removed = store.dec_quantity(user_id, product_id, variant_id)
    if not success:
        await _answer(cb, MSG_UNAVAILABLE, alert=True)
        return
    view = await _compose_cart_view(user_id)
    await _edit_or_send(cb, view)
    if removed:
        undo_key = _remember_removed(user_id, removed)
        await _send_undo_prompt(cb, removed, undo_key)
        cart_item_removed(user_id, key)
    else:
        cart_qty_changed(user_id, key, new_qty)
    await _answer(cb, MSG_CART_UPDATED)


@router.callback_query(F.data.startswith("cart:del:"))
async def handle_cart_delete(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    key = cb.data.split(":", 2)[2]
    product_id, variant_id = _decode_key(key)
    removed = store.remove_item(user_id, product_id, variant_id)
    if not removed:
        await _answer(cb, MSG_UNAVAILABLE, alert=True)
        return
    view = await _compose_cart_view(user_id)
    await _edit_or_send(cb, view)
    undo_key = _remember_removed(user_id, removed)
    await _send_undo_prompt(cb, removed, undo_key)
    cart_item_removed(user_id, key)
    await _answer(cb, MSG_CART_UPDATED)


@router.callback_query(F.data.startswith("cart:undo:"))
async def handle_cart_undo(cb: CallbackQuery) -> None:
    undo_key = cb.data.split(":", 2)[2]
    record = _undo_buffer.pop(undo_key, None)
    if not record:
        await _answer(cb, MSG_UNDO_EXPIRED, alert=True)
        return
    user_id, item = record
    restored = store.add_item(
        user_id=user_id,
        product_id=item.product_id,
        variant_id=item.variant_id,
        quantity=item.qty,
        brand=item.brand,
        name=item.name,
        price=item.price,
        currency=item.currency,
        price_currency=item.price_currency,
        ref_link=item.ref_link,
        category=item.category,
        variant_name=item.variant_name,
        in_stock=item.in_stock,
        image_url=item.image_url,
        source=item.source,
        meta=item.meta,
    )
    view = await _compose_cart_view(user_id)
    await _edit_or_send(cb, view)
    display_name = " ".join(filter(None, [restored.brand, restored.name])) or restored.product_id
    await _answer(cb, f"{MSG_UNDO_SUCCESS}: {display_name}")


@router.callback_query(F.data == "cart:clear")
async def handle_cart_clear(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    store.clear_cart(user_id)
    view = await _compose_cart_view(user_id)
    await _edit_or_send(cb, view)
    cart_cleared(user_id)
    await _answer(cb, MSG_CART_UPDATED)


@router.callback_query(F.data == "cart:checkout")
async def handle_cart_checkout(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    text, markup, links_count = await _build_checkout_view(user_id)
    await _safe_edit(cb, text, markup)
    total_qty, total_price, currency = store.get_cart_total(user_id)
    checkout_started(user_id, total_qty, total_price)
    checkout_links_generated(user_id, links_count)
    await _answer(cb, MSG_CART_UPDATED)


@router.callback_query(F.data == "cart:back_reco")
async def handle_cart_back_reco(cb: CallbackQuery) -> None:
    try:
        from bot.handlers.recommendations import show_main_recommendations

        await show_main_recommendations(cb)
    except Exception as exc:
        logger.warning("Failed to show recommendations: %s", exc)
        await _answer(cb, MSG_UNAVAILABLE, alert=True)


@router.callback_query(F.data.startswith("cart:qty:"))
async def handle_cart_qty_info(cb: CallbackQuery) -> None:
    user_id = cb.from_user.id
    key = cb.data.split(":", 2)[2]
    product_id, variant_id = _decode_key(key)
    for item in store.get_cart(user_id):
        if item.product_id == product_id and item.variant_id == variant_id:
            await _answer(cb, f"{MSG_CART_UPDATED} ({item.qty})")
            return
    await _answer(cb, MSG_UNAVAILABLE, alert=True)


async def _edit_or_send(cb: CallbackQuery, view: CartView) -> None:
    if not await _safe_edit(cb, view.text, view.markup):
        await cb.message.answer(view.text, reply_markup=view.markup)


async def _safe_edit(cb: CallbackQuery, text: str, markup: InlineKeyboardMarkup) -> bool:
    message = cb.message
    if not message:
        return False
    try:
        if message.text == text and message.reply_markup == markup:
            return True
        await message.edit_text(text, reply_markup=markup)
        return True
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return True
        logger.debug("Edit failed: %s", exc)
    except Exception as exc:  # pragma: no cover
        logger.debug("Edit failed: %s", exc)
    return False


async def _answer(cb: CallbackQuery, text: str, *, alert: bool = False) -> None:
    try:
        await cb.answer(sanitize_message(text), show_alert=alert)
    except Exception as exc:  # pragma: no cover
        logger.debug("Callback answer failed: %s", exc)


async def _resolve_product(user_id: int, product_id: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    products = await _load_recommendations(user_id)
    product = next((p for p in products if str(p.get("id")) == str(product_id)), None)
    alternatives = [p for p in products if str(p.get("id")) != str(product_id)]
    return product, alternatives[:5]


def _variant_exists(product: Dict[str, Any], variant_id: str) -> bool:
    for variant in product.get("variants") or []:
        if str(variant.get("id")) == str(variant_id):
            return True
    return False


def _build_cart_item(product: Dict[str, Any], variant_id: Optional[str]) -> CartItem:
    variants = product.get("variants") or []
    variant_name = None
    variant_ref = None
    in_stock = product.get("in_stock", True)
    price = product.get("price") or product.get("price_value")
    currency = product.get("currency") or product.get("price_currency") or "RUB"

    if variant_id and variants:
        for variant in variants:
            if str(variant.get("id")) == str(variant_id):
                variant_name = variant.get("name")
                variant_ref = variant.get("ref_link") or variant.get("link")
                if variant.get("in_stock") is not None:
                    in_stock = variant.get("in_stock")
                if variant.get("price"):
                    price = variant.get("price")
                break

    ref_link = variant_ref or product.get("ref_link") or product.get("link")
    source_label = product.get("source_label") or product.get("source") or ""

    return CartItem(
        product_id=str(product.get("id")),
        variant_id=variant_id,
        qty=1,
        brand=product.get("brand"),
        name=product.get("name"),
        price=float(price) if price is not None else None,
        currency=currency,
        price_currency=currency,
        ref_link=ref_link,
        category=product.get("category"),
        variant_name=variant_name,
        in_stock=in_stock,
        image_url=product.get("image") or product.get("image_url"),
        source=_normalize_source(product.get("source")),
        meta={"source_label": source_label},
    )


def _remember_removed(user_id: int, item: CartItem) -> str:
    undo_key = secrets.token_urlsafe(6)
    _undo_buffer[undo_key] = (user_id, item)
    return undo_key


async def _send_undo_prompt(cb: CallbackQuery, item: CartItem, undo_key: str) -> None:
    title = " ".join(filter(None, [item.brand, item.name])) or item.product_id
    text = f"{MSG_REMOVED}: {title}"
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BTN_UNDO, callback_data=f"cart:undo:{undo_key}")]]
    )
    message = await cb.message.answer(sanitize_message(text), reply_markup=markup)

    async def cleanup() -> None:
        await asyncio.sleep(UNDO_TTL_SECONDS)
        if undo_key in _undo_buffer:
            _undo_buffer.pop(undo_key, None)
            try:
                await message.edit_text(MSG_UNDO_EXPIRED)
            except TelegramBadRequest:
                pass
            except Exception as exc:  # pragma: no cover
                logger.debug("Undo cleanup failed: %s", exc)

    asyncio.create_task(cleanup())


async def _send_alternatives(cb: CallbackQuery, products: List[Dict[str, Any]]) -> None:
    if not products:
        await _answer(cb, MSG_UNAVAILABLE, alert=True)
        return
    lines = [MSG_UNAVAILABLE, ""]
    buttons: List[List[InlineKeyboardButton]] = []
    for product in products[:3]:
        title = " ".join(filter(None, [product.get("brand"), product.get("name")])).strip() or str(product.get("id"))
        price_text = _format_price(product.get("price"), product.get("currency"))
        lines.append(f"• {title} — {price_text}")
        buttons.append([
            InlineKeyboardButton(
                text=f"{BTN_ADD} {title[:24]}",
                callback_data=f"cart:add:{_encode_key(str(product.get('id')), None)}",
            )
        ])
    buttons.append([InlineKeyboardButton(text=BTN_BACK_RECO, callback_data="cart:back_reco")])
    await _safe_edit(cb, sanitize_message("\n".join(lines)), InlineKeyboardMarkup(inline_keyboard=buttons))


def _emit_analytics_added(user_id: int, product_id: str, variant_id: Optional[str], source: Optional[str], price_cents: int) -> None:
    try:
        cart_item_added(user_id, product_id, variant_id or "", source or "unknown", price_cents)
    except Exception as exc:  # pragma: no cover
        logger.debug("Analytics cart_item_added failed: %s", exc)


async def _build_checkout_view(user_id: int) -> Tuple[str, InlineKeyboardMarkup, int]:
    items = store.get_cart(user_id)
    if not items:
        empty = await _render_empty_cart(user_id)
        return empty.text, empty.markup, 0

    lines = [CHECKOUT_TITLE, "", "Имя:", "Телефон:", "Email:", "", CHECKOUT_LINKS_READY, ""]
    links = []
    for item in items:
        if not item.ref_link:
            continue
        url = _append_utm(item.ref_link, item.source)
        links.append(url)
        title = " ".join(filter(None, [item.brand, item.name])) or item.product_id
        lines.append(f"• {title}: {url}")
    if not links:
        lines.append(f"• {CHECKOUT_NO_LINK}")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BTN_BACK_RECO, callback_data="cart:back_reco")]]
    )
    return sanitize_message("\n".join(lines).strip()), markup, len(links)


def _append_utm(link: str, source: Optional[str]) -> str:
    from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

    if not link:
        return link
    parsed = urlparse(link)
    query = dict(parse_qsl(parsed.query))
    if "utm_source" not in query:
        query["utm_source"] = source or "skincare_bot"
    query.setdefault("utm_medium", "telegram")
    query.setdefault("utm_campaign", "cart_checkout")
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


__all__ = ["router", "show_cart"]

