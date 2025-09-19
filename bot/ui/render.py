from __future__ import annotations

from typing import Dict, List, Tuple
from urllib.parse import quote_plus
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from i18n.ru import BTN_ADD, BTN_DETAILS, BTN_VIEW_CART

NARROW_NBSP = "\u202f"
CURRENCY_SYMBOLS = {"RUB": "₽", "USD": "$", "EUR": "€"}


def format_price(amount: float, currency: str = "RUB") -> str:
    if amount is None:
        return "—"
    symbol = CURRENCY_SYMBOLS.get(currency.upper(), currency.upper())
    if amount == int(amount):
        value = f"{int(amount):,}".replace(",", NARROW_NBSP)
    else:
        value = f"{amount:,.2f}".replace(",", NARROW_NBSP)
    return f"{value}{NARROW_NBSP}{symbol}".strip()


def build_cart_row(item: Dict[str, str]) -> str:
    title = " ".join(filter(None, [item.get("brand"), item.get("name")])).strip() or item.get("product_id", "")
    price = format_price(item.get("price", 0), item.get("currency", "RUB"))
    return f"• {title} — {price}"


def quick_pick_keyboard(products: List[Dict[str, str]]) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for product in products:
        pid = str(product.get("id"))
        rows.append([
            InlineKeyboardButton(text=BTN_ADD, callback_data=f"cart:add:{quote_plus(pid)}:"),
            InlineKeyboardButton(text=BTN_DETAILS, callback_data=f"rec:open:{pid}")
        ])
    rows.append([InlineKeyboardButton(text=BTN_VIEW_CART, callback_data="cart:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def render_cart_summary(items: List[Dict[str, str]]) -> Tuple[str, InlineKeyboardMarkup]:
    lines = []
    for item in items:
        lines.append(build_cart_row(item))
    markup = quick_pick_keyboard(items[:3]) if items else InlineKeyboardMarkup(inline_keyboard=[])
    return "\n".join(lines), markup
