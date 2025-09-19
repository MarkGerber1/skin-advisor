from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from typing import List, Optional


# �᭮��� ������ �������� ����
BTN_PALETTE = "?? ��� � 梥�"
BTN_SKINCARE = "?? �室 �� �����"
BTN_ABOUT = "?? � ���"
BTN_SETTINGS = "?? ����ன��"
BTN_REPORT = "?? ��� ४������樨"
BTN_HOME = "?? �������"
BTN_BACK = "?? �����"
BTN_SUPPORT = "?? �����প�"
BTN_CLEAR_DATA = "?? ������ �����"

# �᭮��� ������ �������� ����
BTN_VIEW_CART = "?? ��২��"
BTN_VIEW_CART_TEMPLATE = "?? ��২�� ({count})"


def _cart_caption(cart_count: Optional[int]) -> str:
    if cart_count and cart_count > 0:
        return BTN_VIEW_CART_TEMPLATE.format(count=cart_count)
    return BTN_VIEW_CART


def _resolve_cart_count(user_id: Optional[int]) -> Optional[int]:
    """Resolve current cart count for the user if possible."""
    if not user_id:
        return None
    try:
        from services.cart_store import get_cart_store

        return get_cart_store().get_cart_count(int(user_id))
    except Exception as exc:  # pragma: no cover
        print(f"?? Unable to resolve cart count for {user_id}: {exc}")
        return None


def main_menu(cart_count: Optional[int] = None, *, user_id: Optional[int] = None) -> ReplyKeyboardMarkup:
    """������� ���� � ������� ��২��."""
    if cart_count is None and user_id is not None:
        cart_count = _resolve_cart_count(user_id)

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_PALETTE)],
            [KeyboardButton(text=BTN_SKINCARE)],
            [KeyboardButton(text=_cart_caption(cart_count))],
            [KeyboardButton(text=BTN_ABOUT), KeyboardButton(text=BTN_REPORT)],
            [KeyboardButton(text=BTN_SETTINGS)],
        ],
        resize_keyboard=True,
        input_field_placeholder="�롥�� ����⢨�:",
    )


def main_menu_inline(cart_count: Optional[int] = None, *, user_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Inline-����� �������� ���� (��� edit_text)."""
    if cart_count is None and user_id is not None:
        cart_count = _resolve_cart_count(user_id)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_PALETTE, callback_data="start_palette")],
            [InlineKeyboardButton(text=BTN_SKINCARE, callback_data="start_skincare")],
            [InlineKeyboardButton(text=_cart_caption(cart_count), callback_data="cart:open")],
            [
                InlineKeyboardButton(text=BTN_ABOUT, callback_data="about"),
                InlineKeyboardButton(text=BTN_REPORT, callback_data="show_report"),
            ],
            [InlineKeyboardButton(text=BTN_SETTINGS, callback_data="settings")],
        ]
    )

def back_button() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BACK)]],
        resize_keyboard=True,
    )


def confirm_buttons(yes_text: str = "✅ Да", no_text: str = "✖️ Нет") -> InlineKeyboardMarkup:
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
    buttons: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []

    if back_callback:
        row.append(InlineKeyboardButton(text=BTN_BACK, callback_data=back_callback))
    if prev_callback:
        row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=prev_callback))
    if next_callback:
        row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=next_callback))

    if row:
        buttons.append(row)

    if include_home:
        buttons.append([InlineKeyboardButton(text=BTN_HOME, callback_data="universal:home")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def loading_message() -> str:
    return "⏳ Подождите, готовлю ответ…"


def error_message() -> str:
    return "⚠️ Что-то пошло не так. Попробуйте ещё раз."


def emergency_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_HOME, callback_data="universal:home")],
            [InlineKeyboardButton(text="🔁 Повторить", callback_data="universal:retry")],
        ]
    )


def add_home_button(keyboard: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    if not keyboard or not keyboard.inline_keyboard:
        return emergency_keyboard()
    new_rows = list(keyboard.inline_keyboard)
    new_rows.append([InlineKeyboardButton(text=BTN_HOME, callback_data="universal:home")])
    return InlineKeyboardMarkup(inline_keyboard=new_rows)








