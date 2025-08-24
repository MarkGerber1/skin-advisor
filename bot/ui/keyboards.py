from __future__ import annotations

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from typing import List


# Константы для кнопок главного меню
BTN_PALETTE = "🎨 Палитомеp — мой идеальный цвет"
BTN_SKINCARE = "✨ Диагностика кожи PRO"
BTN_ABOUT = "ⓘ О боте"
BTN_PICK = "🛒 Моя подборка"
BTN_SETTINGS = "⚙️ Настройки"
BTN_REPORT = "📄 Отчёт"
BTN_BACK = "⬅️ Назад"


def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_PALETTE)],
            [KeyboardButton(text=BTN_SKINCARE)],
            [KeyboardButton(text=BTN_ABOUT), KeyboardButton(text=BTN_PICK)],
            [KeyboardButton(text=BTN_REPORT), KeyboardButton(text=BTN_SETTINGS)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )


def back_button() -> ReplyKeyboardMarkup:
    """Кнопка возврата"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BACK)]],
        resize_keyboard=True,
    )


def confirm_buttons(yes_text: str = "✅ Да", no_text: str = "❌ Нет") -> InlineKeyboardMarkup:
    """Кнопки подтверждения"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=yes_text, callback_data="confirm:yes")],
            [InlineKeyboardButton(text=no_text, callback_data="confirm:no")],
        ]
    )


def navigation_buttons(
    prev_callback: str = None, next_callback: str = None, back_callback: str = None
) -> InlineKeyboardMarkup:
    """Кнопки навигации"""
    buttons: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []

    if back_callback:
        row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback))

    if prev_callback:
        row.append(InlineKeyboardButton(text="◀️ Предыдущий", callback_data=prev_callback))

    if next_callback:
        row.append(InlineKeyboardButton(text="Следующий ▶️", callback_data=next_callback))

    if row:
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


def loading_message() -> str:
    """Сообщение о загрузке"""
    return "⏳ Обрабатываю ваш запрос..."


def error_message() -> str:
    """Сообщение об ошибке"""
    return "❌ Произошла ошибка. Попробуйте еще раз."
