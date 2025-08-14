from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.infra.models import DiagnosisResult, SurveyResponse
from app.services.recommendation import build_recommendations
from reco_engine import PricingPolicy
from app.ui import messages
from app.ui.keyboard import build_main_menu

router = Router()


def _build_buy_keyboard(url: str) -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text="🛒 Купить в Золотом Яблоке", url=url)]]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def _policy_from_env() -> PricingPolicy:
    return PricingPolicy(
        user_discount=float(os.getenv("USER_DISCOUNT", "0.05")),
        owner_commission=float(os.getenv("OWNER_COMMISSION", "0.10")),
        merchant_total_discount=0.15,
    )


@router.message(F.text == messages.LEXICON["btn_recommendations"])
@router.callback_query(F.data == "action:get_recs")
async def cmd_recommendations(event: Message | CallbackQuery, session: AsyncSession):
    """Запрашивает ценовую категорию для рекомендаций (если есть результаты)."""
    user_id = event.from_user.id if isinstance(event, Message) else event.from_user.id
    stmt = (
        select(DiagnosisResult)
        .join(SurveyResponse)
        .where(SurveyResponse.user_id == user_id)
        .order_by(DiagnosisResult.created_at.desc())
    )
    result = await session.execute(stmt)
    last_diagnosis = result.scalars().first()

    if not last_diagnosis:
        if isinstance(event, CallbackQuery):
            await event.answer(messages.LEXICON["no_results_yet"], show_alert=True)
        else:
            await event.answer(messages.LEXICON["no_results_yet"])
        return

    res = build_recommendations(last_diagnosis.result_json)

    id_to_product = {p.get("id"): p for p in res.get("products", [])}

    def render(pid_list, limit):
        out = []
        for pid in pid_list[:limit]:
            prod = id_to_product.get(pid)
            if not prod:
                continue
            out.append(messages.render_item_text_with_link(prod))
        return out

    text_lines = []
    max_total = 8
    total = 0

    def add_block(title: str, ids: list[int], limit: int):
        nonlocal total
        if total >= max_total:
            return
        picks = ids[: max(0, min(limit, max_total - total))]
        if not picks:
            return
        text_lines.append(title)
        block = render(picks, len(picks))
        text_lines.extend(block)
        text_lines.append("")
        total += len(block)

    routines = res.get("routines", {})
    add_block("☀️ AM-уход", routines.get("am", []), 3)
    add_block("🌙 PM-уход", routines.get("pm", []), 3)
    add_block("✨ Еженедельный", routines.get("weekly", []), 2)

    if total < max_total:
        if mk := res.get("makeup"):
            text_lines.append("💄 Макияж")
            for grp, pid_list in list(mk.items())[:2]:  # не больше 2 групп
                if total >= max_total:
                    break
                text_lines.append(f"• {grp.capitalize()}:")
                for pid in pid_list[:2]:
                    if total >= max_total:
                        break
                    prod = id_to_product.get(pid)
                    if not prod:
                        continue
                    text_lines.append("  " + messages.render_item_text_with_link(prod))
                    total += 1

    text_lines.append("\n" + res["summary"].get("disclaimer", ""))
    final_text = "\n".join(text_lines)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(final_text, parse_mode="HTML")
        await event.message.answer("Готово ✅", reply_markup=build_main_menu())
    else:
        await event.answer(
            final_text, parse_mode="HTML", reply_markup=build_main_menu()
        )
