from __future__ import annotations

import os
from typing import List

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from engine.catalog_store import CatalogStore
from engine.models import UserProfile, Season, Undertone, ReportData
from engine.selector import select_products, SelectorV2
from engine.answer_expander import AnswerExpanderV2

try:
    from bot.ui.pdf import save_text_pdf, save_last_json  # type: ignore
except ImportError as e:
    print(f"Warning: Could not import pdf module: {e}")

    def save_text_pdf(*args, **kwargs):
        return ""

    def save_last_json(*args, **kwargs):
        pass


router = Router()


def _determine_season(data: dict) -> Season:
    """Determine season based on palette data"""
    undertone = data.get("undertone", "unknown")
    value = data.get("value", "medium")

    # Simple season determination logic
    if undertone == "warm":
        if value in ["light", "medium"]:
            return Season.SPRING
        else:
            return Season.AUTUMN
    elif undertone == "cool":
        if value in ["light", "medium"]:
            return Season.SUMMER
        else:
            return Season.WINTER
    else:
        return None  # Neutral/unknown


class PaletteFlow(StatesGroup):
    A1_UNDERTONE = State()
    A2_VALUE = State()
    A3_HAIR = State()
    A4_BROWS = State()
    A5_EYES = State()
    A6_CONTRAST = State()
    A7_CONFIRM = State()
    A8_REPORT = State()


def _kb_undertone() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Холодный", callback_data="pal:1:undertone:cool"),
            InlineKeyboardButton(text="Тёплый", callback_data="pal:1:undertone:warm"),
        ],
        [
            InlineKeyboardButton(text="Нейтральный", callback_data="pal:1:undertone:neutral"),
            InlineKeyboardButton(text="Оливковый", callback_data="pal:1:undertone:olive"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_value() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=t, callback_data=f"pal:2:value:{c}")
            for t, c in [("Светлый", "light"), ("Средний", "medium"), ("Тёмный", "deep")]
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_hair() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=t, callback_data=f"pal:3:hair:{c}")
            for t, c in [("Светлые", "light"), ("Средние", "medium"), ("Тёмные", "dark")]
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_brows() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=t, callback_data=f"pal:4:brows:{c}")
            for t, c in [("Светлые", "light"), ("Средние", "medium"), ("Тёмные", "dark")]
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_eyes() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=t, callback_data=f"pal:5:eyes:{c}")
            for t, c in [("Голубые", "blue"), ("Зелёные", "green"), ("Карие", "brown")]
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_contrast() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=t, callback_data=f"pal:6:contrast:{c}")
            for t, c in [("Низкий", "low"), ("Средний", "medium"), ("Высокий", "high")]
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_confirm(enabled: bool) -> InlineKeyboardMarkup:
    btns = [
        [InlineKeyboardButton(text="Назад", callback_data="pal:7:back:6")],
    ]
    if enabled:
        btns[0].append(
            InlineKeyboardButton(text="Сформировать отчёт", callback_data="pal:7:confirm:ok")
        )
    else:
        btns[0].append(
            InlineKeyboardButton(text="Сформировать отчёт", callback_data="pal:7:confirm:disabled")
        )
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def start_flow(m: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(PaletteFlow.A1_UNDERTONE)
    await m.answer("Шаг 1/7 — Определим подтон лица:", reply_markup=_kb_undertone())


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
    try:
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
        await msg.edit_text("Шаг 2/7 — Светлота лица (value):")
        await msg.edit_reply_markup(reply_markup=_kb_value())
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in palette a1 handler: {e}")
        try:
            await cb.answer("⚠️ Произошла ошибка, попробуйте снова", show_alert=True)
        except:
            pass


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
    await msg.edit_text("Шаг 3/7 — Глубина волос:")
    await msg.edit_reply_markup(reply_markup=_kb_hair())
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
    await msg.edit_text("Шаг 4/7 — Брови:")
    await msg.edit_reply_markup(reply_markup=_kb_brows())
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
    await msg.edit_text("Шаг 5/7 — Цвет глаз:")
    await msg.edit_reply_markup(reply_markup=_kb_eyes())
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
    await msg.edit_text("Шаг 6/7 — Контраст внешности:")
    await msg.edit_reply_markup(reply_markup=_kb_contrast())
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
    await state.set_state(PaletteFlow.A7_CONFIRM)

    d = await state.get_data()
    undertone = d.get("undertone")
    value = d.get("value")
    hair_depth = d.get("hair_depth")
    brows = d.get("brows")
    eye_color = d.get("eye_color")
    contrast = d.get("contrast")

    ready = bool(undertone and value and hair_depth and brows and eye_color and contrast)

    text = (
        "Шаг 7/7 — Подтверждение\n\n"
        f"Подтон: {undertone}\n"
        f"Светлота: {value}\n"
        f"Волосы: {hair_depth}\n"
        f"Брови: {brows}\n"
        f"Глаза: {eye_color}\n"
        f"Контраст: {contrast}\n\n"
        "Нажмите 'Сформировать отчёт'."
    )
    await msg.edit_text(text)
    await msg.edit_reply_markup(reply_markup=_kb_confirm(enabled=ready))
    await cb.answer()


@router.callback_query(F.data.startswith("pal:"), PaletteFlow.A7_CONFIRM)
async def a7(cb: CallbackQuery, state: FSMContext) -> None:
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
    if step != "7":
        await cb.answer()
        return
    if field == "confirm" and value == "disabled":
        await cb.answer("Заполните обязательные поля", show_alert=True)
        return
    if field == "back":
        await state.set_state(PaletteFlow.A6_CONTRAST)
        await msg.edit_text("Шаг 6/7 — Контраст внешности:")
        await msg.edit_reply_markup(reply_markup=_kb_contrast())
        await cb.answer()
        return
    if field == "confirm" and value == "ok":
        await state.set_state(PaletteFlow.A8_REPORT)
        await msg.edit_text("🔄 Собираю макияж по палитре…")
        await cb.answer()

        d = await state.get_data()
        uid = int(cb.from_user.id) if cb.from_user and cb.from_user.id else 1

        # Create Engine v2 UserProfile with color analysis
        profile = UserProfile(
            user_id=uid,
            undertone=Undertone(d.get("undertone", "unknown")),
            season=_determine_season(d),
            contrast=d.get("contrast"),
            hair_color=d.get("hair_depth"),
            eye_color=d.get("eye_color"),
        )

        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog = CatalogStore.instance(catalog_path).get()

        # Use Engine v2 Selector for makeup
        selector = SelectorV2()
        result = selector.select_products_v2(
            profile=profile,
            catalog=catalog,
            partner_code=os.getenv("PARTNER_CODE", "aff_123"),
            redirect_base=os.getenv("REDIRECT_BASE"),
        )

        # Extract makeup products for ReportData
        makeup_products = []
        for category_products in result.get("makeup", {}).values():
            for prod_dict in category_products:
                from engine.models import Product

                product = Product(
                    key=prod_dict["id"],
                    title=prod_dict["name"],
                    brand=prod_dict["brand"],
                    category=prod_dict["category"],
                    price=prod_dict.get("price"),
                    actives=prod_dict.get("actives", []),
                    tags=prod_dict.get("tags", []),
                    buy_url=prod_dict.get("link"),
                )
                makeup_products.append(product)

        # Generate Engine v2 reports
        report_data = ReportData(
            user_profile=profile, skincare_products=[], makeup_products=makeup_products
        )

        expander = AnswerExpanderV2()
        tldr_report = expander.generate_tldr_report(report_data)
        full_report = expander.generate_full_report(report_data)

        from bot.ui.render import render_makeup_report

        text, kb = render_makeup_report(result)

        # Сохраняем профиль пользователя для будущих рекомендаций
        from bot.handlers.user_profile_store import get_user_profile_store

        profile_store = get_user_profile_store()
        profile_store.save_profile(
            uid, profile, metadata={"test_type": "palette", "completed_at": "now"}
        )
        print(f"💾 Profile saved for user {uid} after palette test completion")

        enriched = {"tl_dr": tldr_report, "full_text": full_report}
        text_to_pdf = enriched.get("full_text") or text
        # Save JSON + PDF
        uid = int(cb.from_user.id) if cb.from_user and cb.from_user.id else 0
        snapshot = {
            "type": "palette",
            "profile": profile.model_dump(),
            "result": result,
            "tl_dr": enriched.get("tl_dr"),
            "full_text": enriched.get("full_text"),
        }
        save_last_json(uid, snapshot)
        save_text_pdf(uid, title="Отчёт по палитре", body_text=text_to_pdf)
        await msg.edit_text(text, disable_web_page_preview=True)
        await msg.edit_reply_markup(reply_markup=kb)
        await state.clear()
        return
    await cb.answer()
