from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.ui.keyboards import (
    main_menu,
    BTN_PALETTE,
    BTN_SKINCARE,
    BTN_ABOUT,
    BTN_PICK,
    BTN_SETTINGS,
    BTN_REPORT,
)


router = Router()


@router.message(CommandStart())
async def on_start(m: Message, state: FSMContext) -> None:
    await state.clear()
    await m.answer(
        "Привет! ✨ Я подберу персональный уход и идеальные оттенки макияжа по вашему профилю.\n\n"
        "Выберите режим:",
        reply_markup=main_menu(),
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
        "🤖 О боте:\n\n"
        "Я - ваш персональный косметолог! ✨\n\n"
        "🔹 Анализ типа кожи и проблем\n"
        "🔹 Определение цветовой палитры (undertone)\n"
        "🔹 Персональные рекомендации по уходу и макияжу\n"
        "🔹 Прямые ссылки на проверенные продукты\n\n"
        "💡 Пройдите диагностику и получите персонализированный отчет!",
        reply_markup=main_menu(),
    )


@router.message(F.text == BTN_PICK, StateFilter(None))
async def my_picks(m: Message, state: FSMContext) -> None:
    await state.clear()
    await m.answer(
        "🛒 Моя подборка\n\n"
        "Здесь будут отображаться ваши сохраненные продукты.\n"
        "Сначала пройдите диагностику кожи или определение палитры!",
        reply_markup=main_menu(),
    )


@router.message(F.text == BTN_SETTINGS, StateFilter(None))
async def settings(m: Message, state: FSMContext) -> None:
    await state.clear()
    await m.answer(
        "⚙️ Настройки\n\n"
        "Настройки бота:\n"
        "• Язык: Русский 🇷🇺\n"
        "• Уведомления: Включены 🔔\n"
        "• Темная тема: Авто 🌙\n\n"
        "Функция в разработке...",
        reply_markup=main_menu(),
    )


@router.message(F.text == BTN_REPORT, StateFilter(None))
async def report_latest(m: Message, state: FSMContext) -> None:
    await state.clear()
    from aiogram.types import CallbackQuery

    # Имитация нажатия кнопки для переиспользования логики report:latest
    class _FakeCb(CallbackQuery):
        pass

    # Вызовем хендлер отправки отчёта напрямую
    from bot.handlers.report import send_latest_report

    cb = _FakeCb(id="0", from_user=m.from_user, chat_instance="0", data="report:latest", message=m)
    try:
        await send_latest_report(cb)
    except Exception:
        await m.answer("Отчёт ещё не сформирован. Пройдите диагностику или палитрометр.")
