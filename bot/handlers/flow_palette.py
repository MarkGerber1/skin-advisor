from __future__ import annotations

import os
from typing import List

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from engine.catalog_store import CatalogStore
from engine.models import UserProfile
from engine.selector import select_products


router = Router()


class PaletteFlow(StatesGroup):
    A1_UNDERTONE = State()
    A2_VALUE = State()
    A3_HAIR = State()
    A4_BROWS = State()
    A5_EYES = State()
    A6_CONTRAST = State()
    A7_REPORT = State()


def _kb_undertone() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Холодный", callback_data="pal:1:undertone:cool"), InlineKeyboardButton(text="Тёплый", callback_data="pal:1:undertone:warm")],
        [InlineKeyboardButton(text="Нейтральный", callback_data="pal:1:undertone:neutral"), InlineKeyboardButton(text="Оливковый", callback_data="pal:1:undertone:olive")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_value() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t, callback_data=f"pal:2:value:{c}") for t, c in [("Светлый", "light"), ("Средний", "medium"), ("Тёмный", "deep")]]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_next() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Дальше", callback_data="pal:next")]])


async def start_flow(m: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(PaletteFlow.A1_UNDERTONE)
    await m.answer("Шаг 1/6 — Определим подтон кожи:", reply_markup=_kb_undertone())


def _parse(data: str) -> List[str]:
    return data.split(":", 3)


async def _debounce(cb: CallbackQuery, state: FSMContext) -> bool:
    d = await state.get_data()
    last_cb = d.get("last_cb")
    if last_cb == cb.data:
        try:
            await cb.answer()
        finally:
            return True
    await state.update_data(last_cb=cb.data)
    return False


@router.callback_query(F.data.startswith("pal:"), PaletteFlow.A1_UNDERTONE)
async def a1(cb: CallbackQuery, state: FSMContext) -> None:
    if await _debounce(cb, state):
        return
    if not cb.data:
        await cb.answer()
        return
    msg = cb.message
    if not isinstance(msg, Message):
        await cb.answer()
        return
    _, step, field, value = _parse(cb.data)
    if step != "1" or field != "undertone":
        await cb.answer()
        return
    await state.update_data(undertone=value)
    await state.set_state(PaletteFlow.A2_VALUE)
    await msg.edit_text("Шаг 2/6 — Светлота кожи (value):")
    await msg.edit_reply_markup(reply_markup=_kb_value())
    await cb.answer()


@router.callback_query(F.data.startswith("pal:"), PaletteFlow.A2_VALUE)
async def a2(cb: CallbackQuery, state: FSMContext) -> None:
    if await _debounce(cb, state):
        return
    if not cb.data:
        await cb.answer()
        return
    msg = cb.message
    if not isinstance(msg, Message):
        await cb.answer()
        return
    _, step, field, value = _parse(cb.data)
    if step != "2" or field != "value":
        await cb.answer()
        return
    await state.update_data(value=value)
    await state.set_state(PaletteFlow.A3_HAIR)
    await msg.edit_text("Шаг 3/6 — Глубина волос:")
    await msg.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"pal:3:hair:{c}") for t, c in [("Светлые", "light"), ("Средние", "medium"), ("Тёмные", "dark")]]]))
    await cb.answer()


@router.callback_query(F.data.startswith("pal:"), PaletteFlow.A3_HAIR)
async def a3(cb: CallbackQuery, state: FSMContext) -> None:
    if await _debounce(cb, state):
        return
    if not cb.data:
        await cb.answer()
        return
    msg = cb.message
    if not isinstance(msg, Message):
        await cb.answer()
        return
    _, step, field, value = _parse(cb.data)
    if step != "3" or field != "hair":
        await cb.answer()
        return
    await state.update_data(hair_depth=value)
    await state.set_state(PaletteFlow.A4_BROWS)
    await msg.edit_text("Шаг 4/6 — Брови:")
    await msg.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"pal:4:brows:{c}") for t, c in [("Светлые", "light"), ("Средние", "medium"), ("Тёмные", "dark")]]]))
    await cb.answer()


@router.callback_query(F.data.startswith("pal:"), PaletteFlow.A4_BROWS)
async def a4(cb: CallbackQuery, state: FSMContext) -> None:
    if await _debounce(cb, state):
        return
    if not cb.data:
        await cb.answer()
        return
    msg = cb.message
    if not isinstance(msg, Message):
        await cb.answer()
        return
    _, step, field, value = _parse(cb.data)
    if step != "4" or field != "brows":
        await cb.answer()
        return
    await state.update_data(brows=value)
    await state.set_state(PaletteFlow.A5_EYES)
    await msg.edit_text("Шаг 5/6 — Цвет глаз:")
    await msg.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"pal:5:eyes:{c}") for t, c in [("Голубые", "blue"), ("Зелёные", "green"), ("Карие", "brown")]]]))
    await cb.answer()


@router.callback_query(F.data.startswith("pal:"), PaletteFlow.A5_EYES)
async def a5(cb: CallbackQuery, state: FSMContext) -> None:
    if await _debounce(cb, state):
        return
    if not cb.data:
        await cb.answer()
        return
    msg = cb.message
    if not isinstance(msg, Message):
        await cb.answer()
        return
    _, step, field, value = _parse(cb.data)
    if step != "5" or field != "eyes":
        await cb.answer()
        return
    await state.update_data(eye_color=value)
    await state.set_state(PaletteFlow.A6_CONTRAST)
    await msg.edit_text("Шаг 6/6 — Контраст внешности:")
    await msg.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=f"pal:6:contrast:{c}") for t, c in [("Низкий", "low"), ("Средний", "medium"), ("Высокий", "high")]]]))
    await cb.answer()


@router.callback_query(F.data.startswith("pal:"), PaletteFlow.A6_CONTRAST)
async def a6(cb: CallbackQuery, state: FSMContext) -> None:
    if await _debounce(cb, state):
        return
    if not cb.data:
        await cb.answer()
        return
    msg = cb.message
    if not isinstance(msg, Message):
        await cb.answer()
        return
    _, step, field, value = _parse(cb.data)
    if step != "6" or field != "contrast":
        await cb.answer()
        return
    await state.update_data(contrast=value)
    await state.set_state(PaletteFlow.A7_REPORT)
    await msg.edit_text("🔄 Собираю макияж по палитре…")
    await cb.answer()

    d = await state.get_data()
    profile = UserProfile(
        undertone=d.get("undertone"),
        value=d.get("value"),
        hair_depth=d.get("hair_depth"),
        eye_color=d.get("eye_color"),
        contrast=d.get("contrast"),
    )

    catalog_path = os.getenv("CATALOG_PATH", "data/fixed_catalog.yaml")
    catalog = CatalogStore.instance(catalog_path).get()
    result = select_products(
        user_profile=profile,
        catalog=catalog,
        partner_code=os.getenv("PARTNER_CODE", "aff_123"),
        redirect_base=os.getenv("REDIRECT_BASE"),
    )

    from bot.ui.render import render_makeup_report

    text, kb = render_makeup_report(result)
    await msg.edit_text(text, disable_web_page_preview=True)
    await msg.edit_reply_markup(reply_markup=kb)
    await state.clear()


