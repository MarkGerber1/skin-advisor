from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from typing import Optional

from services.cart_store import get_cart_store

BTN_PALETTE = "🎨 Тон & сияние"
BTN_SKINCARE = "💧 Портрет кожи"
BTN_CART = "🛒 Корзина"
BTN_ABOUT = "ℹ️ О боте"
BTN_SETTINGS = "⚙️ Настройки"
BTN_REPORT = "📄 Мои рекомендации"
BTN_BACK = "⬅ Назад"
BTN_HOME = "🏠 Главное меню"

BTN_CONFIRM_YES = "✅ Да"
BTN_CONFIRM_NO = "✖️ Нет"
BTN_RETRY = "🔁 Повторить"

_store = get_cart_store()


def _cart_caption(count: int) -> str:
    return BTN_CART if count <= 0 else f"{BTN_CART} ({count})"


def _resolve_count(cart_count: Optional[int], user_id: Optional[int]) -> int:
    if cart_count is not None:
        return max(cart_count, 0)
    if not user_id:
        return 0
    try:
        return _store.get_cart_count(int(user_id))
    except Exception:  # pragma: no cover - diagnostics only
        return 0


def is_cart_button_text(text: Optional[str]) -> bool:
    return bool(text and text.startswith(BTN_CART))


def main_menu(cart_count: Optional[int] = None, *, user_id: Optional[int] = None) -> ReplyKeyboardMarkup:
    count = _resolve_count(cart_count, user_id)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_PALETTE)],
            [KeyboardButton(text=BTN_SKINCARE)],
            [KeyboardButton(text=_cart_caption(count))],
            [KeyboardButton(text=BTN_ABOUT), KeyboardButton(text=BTN_REPORT)],
            [KeyboardButton(text=BTN_SETTINGS)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Что хотите сделать?",
    )


def main_menu_inline(cart_count: Optional[int] = None, *, user_id: Optional[int] = None) -> InlineKeyboardMarkup:
    count = _resolve_count(cart_count, user_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_PALETTE, callback_data="start_palette")],
            [InlineKeyboardButton(text=BTN_SKINCARE, callback_data="start_skincare")],
            [InlineKeyboardButton(text=_cart_caption(count), callback_data="cart:open")],
            [InlineKeyboardButton(text=BTN_ABOUT, callback_data="about"), InlineKeyboardButton(text=BTN_REPORT, callback_data="show_report")],
            [InlineKeyboardButton(text=BTN_SETTINGS, callback_data="settings")],
        ]
    )


def back_button() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BACK)]],
        resize_keyboard=True,
    )


def confirm_buttons(yes_text: str = BTN_CONFIRM_YES, no_text: str = BTN_CONFIRM_NO) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=yes_text, callback_data="confirm:yes")],
            [InlineKeyboardButton(text=no_text, callback_data="confirm:no")],
        ]
    )


def navigation_buttons(
    prev_callback: Optional[str] = None,
    next_callback: Optional[str] = None,
    back_callback: Optional[str] = None,
    include_home: bool = True,
) -> InlineKeyboardMarkup:
    rows = []
    nav_row = []
    if prev_callback:
        nav_row.append(InlineKeyboardButton(text="⬅ Назад", callback_data=prev_callback))
    if next_callback:
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=next_callback))
    if back_callback:
        nav_row.insert(0, InlineKeyboardButton(text=BTN_BACK, callback_data=back_callback))
    if nav_row:
        rows.append(nav_row)
    if include_home:
        rows.append([InlineKeyboardButton(text=BTN_HOME, callback_data="universal:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def loading_message() -> str:
    return "Подождите, готовим ответ..."


def error_message() -> str:
    return "Что-то пошло не так. Попробуйте ещё раз."


def emergency_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_HOME, callback_data="universal:home")],
            [InlineKeyboardButton(text=BTN_RETRY, callback_data="universal:retry")],
        ]
    )


def add_home_button(keyboard: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    if not keyboard or not keyboard.inline_keyboard:
        return emergency_keyboard()
    new_rows = list(keyboard.inline_keyboard)
    new_rows.append([InlineKeyboardButton(text=BTN_HOME, callback_data="universal:home")])
    return InlineKeyboardMarkup(inline_keyboard=new_rows)


# Backwards compatibility aliases
BTN_PICK = BTN_CART
