from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.infra.models import DiagnosisResult, SurveyResponse
from app.services.recommendation import build_recommendations
from reco_engine import load_catalog, PricingPolicy, env_deeplink_config
from app.ui import messages

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


@router.message(F.text == messages.LEXICON['btn_recommendations'])
@router.callback_query(F.data == 'action:get_recs')
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
			await event.answer(messages.LEXICON['no_results_yet'], show_alert=True)
		else:
			await event.answer(messages.LEXICON['no_results_yet'])
		return

	catalog = load_catalog()
	res = build_recommendations(last_diagnosis.result_json, catalog)

	def render(pid_list):
		out = []
		for pid in pid_list:
			prod = next((p for p in res["products"] if p["id"] == pid), None)
			if not prod:
				continue
			out.append(messages.render_item_text(prod))
		return out

	text_lines = []
	text_lines.append("☀️ AM-уход")
	text_lines += render(res["routines"].get("am", []))
	text_lines.append("")
	text_lines.append("🌙 PM-уход")
	text_lines += render(res["routines"].get("pm", []))
	text_lines.append("")
	text_lines.append("✨ Еженедельный")
	text_lines += render(res["routines"].get("weekly", []))

	if mk := res.get("makeup"):
		text_lines.append("")
		text_lines.append("💄 Макияж")
		for grp, pid_list in mk.items():
			text_lines.append(f"• {grp.capitalize()}:")
			for pid in pid_list:
				prod = next((p for p in res["products"] if p["id"] == pid), None)
				if not prod:
					continue
				text_lines.append("  " + messages.render_item_text(prod))

	text_lines.append("\n" + res["summary"].get("disclaimer", ""))
	final_text = "\n".join(text_lines)

	first = res["products"][0] if res.get("products") else None
	kb = _build_buy_keyboard(first["ref_link"]) if first and first.get("ref_link") else None
	if isinstance(event, CallbackQuery):
		await event.message.edit_text(final_text, reply_markup=kb)
	else:
		await event.answer(final_text, reply_markup=kb)
