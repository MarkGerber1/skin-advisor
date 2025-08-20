from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu() -> ReplyKeyboardMarkup:
    from bot.handlers.start import BTN_PALETTE, BTN_SKINCARE, BTN_ABOUT, BTN_PICK, BTN_SETTINGS

    return ReplyKeyboardMarkup(
        keyboard=
        [
            [KeyboardButton(text=BTN_PALETTE)],
            [KeyboardButton(text=BTN_SKINCARE)],
            [KeyboardButton(text=BTN_ABOUT), KeyboardButton(text=BTN_PICK), KeyboardButton(text=BTN_SETTINGS)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )


