from __future__ import annotations

from typing import List
import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from engine.catalog_store import CatalogStore
from engine.models import UserProfile
from engine.selector import select_products
from bot.ui.pdf import save_text_pdf, save_last_json


router = Router()


class SkincareFlow(StatesGroup):
    B1_TYPE = State()
    B2_CONCERNS = State()
    B3_CONFIRM = State()
    B4_REPORT = State()


def _kb_skin_types() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Сухая", callback_data="skin:1:type:dry"), InlineKeyboardButton(text="Жирная", callback_data="skin:1:type:oily")],
        [InlineKeyboardButton(text="Комбинированная", callback_data="skin:1:type:combo")],
        [InlineKeyboardButton(text="Чувствительная", callback_data="skin:1:type:sensitive"), InlineKeyboardButton(text="Нормальная", callback_data="skin:1:type:normal")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_concerns(selected: List[str]) -> InlineKeyboardMarkup:
    options = [
        ("Акне", "acne"),
        ("Обезвоженность", "dehydration"),
        ("Покраснения", "redness"),
        ("Пигментация", "pigmentation"),
        ("Возрастные", "aging"),
        ("Чувствительность", "sensitivity"),
    ]
    rows: List[List[InlineKeyboardButton]] = []
    for title, code in options:
        flag = "✓ " if code in selected else ""
        rows.append([InlineKeyboardButton(text=f"{flag}{title}", callback_data=f"skin:2:concern:{code}")])
    rows.append([InlineKeyboardButton(text="Дальше", callback_data="skin:2:next:go")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_confirm(enabled: bool) -> InlineKeyboardMarkup:
    btns = [
        [InlineKeyboardButton(text="Назад", callback_data="skin:3:back:1")],
    ]
    if enabled:
        btns[0].append(InlineKeyboardButton(text="Сформировать отчёт", callback_data="skin:3:confirm:ok"))
    else:
        btns[0].append(InlineKeyboardButton(text="Сформировать отчёт", callback_data="skin:3:confirm:disabled"))
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def start_flow(m: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(SkincareFlow.B1_TYPE)
    await m.answer("Шаг 1/3 — Выберите свой тип кожи:", reply_markup=_kb_skin_types())


def _parse(data: str) -> List[str]:
    # pattern: skin:<step>:<field>:<value>
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


@router.callback_query(F.data.startswith("skin:"), SkincareFlow.B1_TYPE)
async def on_type(cb: CallbackQuery, state: FSMContext) -> None:
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
    if step != "1" or field != "type":
        await cb.answer("Неверный шаг", show_alert=False)
        return
    await state.update_data(skin_type=value)
    await state.set_state(SkincareFlow.B2_CONCERNS)
    await msg.edit_text("Шаг 2/3 — Выберите проблемы кожи (можно несколько):")
    await msg.edit_reply_markup(reply_markup=_kb_concerns(selected=[]))
    await cb.answer()


@router.callback_query(F.data.startswith("skin:"), SkincareFlow.B2_CONCERNS)
async def on_concerns(cb: CallbackQuery, state: FSMContext) -> None:
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
    d = await state.get_data()
    selected: List[str] = list(d.get("concerns") or [])
    if step == "2" and field == "concern":
        if value in selected:
            selected.remove(value)
        else:
            selected.append(value)
        await state.update_data(concerns=selected)
        await msg.edit_reply_markup(reply_markup=_kb_concerns(selected))
        await cb.answer()
        return
    if step == "2" and field == "next":
        await state.set_state(SkincareFlow.B3_CONFIRM)
        d = await state.get_data()
        skin_type = d.get("skin_type")
        concerns = d.get("concerns") or []
        ready = bool(skin_type)
        text = (
            "Шаг 3/3 — Подтверждение\n\n"
            f"Тип кожи: {skin_type}\n"
            f"Проблемы: {', '.join(concerns) if concerns else '—'}\n\n"
            "Нажмите 'Сформировать отчёт'."
        )
        await msg.edit_text(text)
        await msg.edit_reply_markup(reply_markup=_kb_confirm(enabled=ready))
        await cb.answer()
        return
    await cb.answer("Неверное действие")


@router.callback_query(F.data.startswith("skin:"), SkincareFlow.B3_CONFIRM)
async def on_confirm(cb: CallbackQuery, state: FSMContext) -> None:
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
    if step != "3":
        await cb.answer()
        return
    if field == "confirm" and value == "disabled":
        await cb.answer("Заполните обязательные поля", show_alert=True)
        return
    if field == "back":
        await state.set_state(SkincareFlow.B2_CONCERNS)
        d = await state.get_data()
        await msg.edit_text("Шаг 2/3 — Выберите проблемы кожи (можно несколько):")
        await msg.edit_reply_markup(reply_markup=_kb_concerns(selected=list(d.get("concerns") or [])))
        await cb.answer()
        return
    if field == "confirm" and value == "ok":
        await state.set_state(SkincareFlow.B4_REPORT)
        await msg.edit_text("🔄 Собираю рекомендации…")
        await cb.answer()

        d = await state.get_data()
        profile = UserProfile(skin_type=d.get("skin_type"), concerns=list(d.get("concerns") or []))

        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog = CatalogStore.instance(catalog_path).get()
        result = select_products(
            user_profile=profile,
            catalog=catalog,
            partner_code=os.getenv("PARTNER_CODE", "aff_123"),
            redirect_base=os.getenv("REDIRECT_BASE"),
        )

        # Render
        from bot.ui.render import render_skincare_report

        text, kb = render_skincare_report(result)
        # AnswerExpander (TL;DR/FULL)
        from engine.answer_expander import expand
        enriched = expand(profile.model_dump(), text, result)
        text_to_pdf = enriched.get("full_text") or text
        # Save JSON + PDF
        uid = int(cb.from_user.id) if cb.from_user and cb.from_user.id else 0
        snapshot = {"type": "skincare", "profile": profile.model_dump(), "result": result, "tl_dr": enriched.get("tl_dr"), "full_text": enriched.get("full_text")}
        save_last_json(uid, snapshot)
        save_text_pdf(uid, title="Отчёт по уходу", body_text=text_to_pdf)
        await msg.edit_text(text, disable_web_page_preview=True)
        await msg.edit_reply_markup(reply_markup=kb)
        await state.clear()
        return
    await cb.answer()


