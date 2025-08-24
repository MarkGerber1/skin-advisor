from __future__ import annotations

from typing import List
import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from engine.catalog_store import CatalogStore
from engine.models import UserProfile, SkinType, Sensitivity, ReportData
from engine.selector import select_products, SelectorV2
from engine.answer_expander import AnswerExpanderV2

try:
    from bot.ui.pdf import save_text_pdf, save_last_json
except ImportError as e:
    print(f"Warning: Could not import pdf module: {e}")

    def save_text_pdf(*args, **kwargs):
        return ""

    def save_last_json(*args, **kwargs):
        pass


router = Router()


class SkincareFlow(StatesGroup):
    B1_TYPE = State()
    B2_CONCERNS = State()
    B3_CONFIRM = State()
    B4_REPORT = State()


def _kb_skin_types() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Сухая", callback_data="skin:1:type:dry"),
            InlineKeyboardButton(text="Жирная", callback_data="skin:1:type:oily"),
        ],
        [InlineKeyboardButton(text="Комбинированная", callback_data="skin:1:type:combo")],
        [
            InlineKeyboardButton(text="Чувствительная", callback_data="skin:1:type:sensitive"),
            InlineKeyboardButton(text="Нормальная", callback_data="skin:1:type:normal"),
        ],
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
        rows.append(
            [InlineKeyboardButton(text=f"{flag}{title}", callback_data=f"skin:2:concern:{code}")]
        )
    rows.append([InlineKeyboardButton(text="Дальше", callback_data="skin:2:next:go")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _kb_confirm(enabled: bool) -> InlineKeyboardMarkup:
    btns = [
        [InlineKeyboardButton(text="Назад", callback_data="skin:3:back:1")],
    ]
    if enabled:
        btns[0].append(
            InlineKeyboardButton(text="Сформировать отчёт", callback_data="skin:3:confirm:ok")
        )
    else:
        btns[0].append(
            InlineKeyboardButton(text="Сформировать отчёт", callback_data="skin:3:confirm:disabled")
        )
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
        await msg.edit_reply_markup(
            reply_markup=_kb_concerns(selected=list(d.get("concerns") or []))
        )
        await cb.answer()
        return
    if field == "confirm" and value == "ok":
        await state.set_state(SkincareFlow.B4_REPORT)
        await msg.edit_text("🔄 Собираю рекомендации…")
        await cb.answer()

        d = await state.get_data()
        uid = int(cb.from_user.id) if cb.from_user and cb.from_user.id else 1
        
        # Create Engine v2 UserProfile
        profile = UserProfile(
            user_id=uid,
            skin_type=SkinType(d.get("skin_type", "normal")),
            concerns=list(d.get("concerns") or [])
        )

        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog = CatalogStore.instance(catalog_path).get()
        
        # Use Engine v2 Selector
        selector = SelectorV2()
        result = selector.select_products_v2(
            profile=profile,
            catalog=catalog,
            partner_code=os.getenv("PARTNER_CODE", "aff_123"),
            redirect_base=os.getenv("REDIRECT_BASE")
        )

        # Extract products for ReportData
        skincare_products = []
        for category_products in result.get("skincare", {}).values():
            for prod_dict in category_products:
                # Convert dict back to Product for report
                from engine.models import Product
                product = Product(
                    key=prod_dict["id"],
                    title=prod_dict["name"],
                    brand=prod_dict["brand"],
                    category=prod_dict["category"],
                    price=prod_dict.get("price"),
                    actives=prod_dict.get("actives", []),
                    tags=prod_dict.get("tags", []),
                    buy_url=prod_dict.get("link")
                )
                skincare_products.append(product)

        # Generate Engine v2 reports
        report_data = ReportData(
            user_profile=profile,
            skincare_products=skincare_products,
            makeup_products=[]
        )
        
        expander = AnswerExpanderV2()
        tldr_report = expander.generate_tldr_report(report_data)
        full_report = expander.generate_full_report(report_data)

        # Render for UI
        from bot.ui.render import render_skincare_report
        text, kb = render_skincare_report(result)
        
        # Save JSON + PDF
        snapshot = {
            "type": "skincare",
            "profile": profile.model_dump(),
            "result": result,
            "tl_dr": tldr_report,
            "full_text": full_report,
        }
        save_last_json(uid, snapshot)
        save_text_pdf(uid, title="📊 Skin Advisor - Отчёт по уходу", body_text=full_report)
        await msg.edit_text(text, disable_web_page_preview=True)
        await msg.edit_reply_markup(reply_markup=kb)
        await state.clear()
        return
    await cb.answer()
