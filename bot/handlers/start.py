from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext


router = Router()


BTN_PALETTE = "Палитрометр — мой идеальный цвет"
BTN_SKINCARE = "Диагностика кожи PRO"
BTN_ABOUT = "ⓘ О боте"
BTN_PICK = "🛒 Моя подборка"
BTN_SETTINGS = "⚙️ Настройки"


def build_main_menu() -> ReplyKeyboardMarkup:
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


@router.message(CommandStart())
async def on_start(m: Message, state: FSMContext) -> None:
    await state.clear()
    await m.answer(
        "Привет! Я подберу уход и идеальные оттенки. Выберите режим:",
        reply_markup=build_main_menu(),
    )


@router.message(F.text == BTN_SKINCARE, StateFilter(None))
async def start_skincare(m: Message, state: FSMContext) -> None:
    from .flow_skincare import start_flow

    await start_flow(m, state)


@router.message(F.text == BTN_PALETTE, StateFilter(None))
async def start_palette(m: Message, state: FSMContext) -> None:
    from .flow_palette import start_flow

    await start_flow(m, state)


@router.message(F.text == BTN_ABOUT, StateFilter(None))
async def about(m: Message, state: FSMContext) -> None:
    await state.clear()
    await m.answer(
        "О боте: подбор ухода и макияжа по профилю. Пройдите один из потоков и получите отчёт с ссылками.",
        reply_markup=build_main_menu(),
    )


