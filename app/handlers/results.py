from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infra.models import DiagnosisResult, SurveyResponse
from app.services.recommendation import build_recommendations
from pdf_report import build_pdf
from app.ui import keyboards, messages

router = Router()


aSYNC = AsyncSession


async def show_last_result(
    user_id: int, session: AsyncSession, chat: Message | CallbackQuery
):
    """Отображает последний результат диагностики."""
    stmt = (
        select(DiagnosisResult)
        .join(SurveyResponse)
        .where(SurveyResponse.user_id == user_id)
        .order_by(DiagnosisResult.created_at.desc())
    )
    result = await session.execute(stmt)
    last_diagnosis = result.scalars().first()

    if not last_diagnosis:
        if isinstance(chat, Message):
            await chat.answer(messages.LEXICON["no_results_yet"])
        else:
            await chat.message.answer(messages.LEXICON["no_results_yet"])
        return

    diagnosis_data = last_diagnosis.result_json
    text = messages.format_diagnosis_result(diagnosis_data)

    if isinstance(chat, Message):
        await chat.answer(text, reply_markup=keyboards.create_results_keyboard())
    else:
        await chat.message.answer(
            text, reply_markup=keyboards.create_results_keyboard()
        )


@router.message(Command("results"))
@router.message(F.text == messages.LEXICON["btn_results"])
async def cmd_results(message: Message, session: AsyncSession):
    await show_last_result(message.from_user.id, session, message)


@router.callback_query(F.data == "action:show_results")
async def cb_show_results(callback: CallbackQuery, session: AsyncSession):
    await callback.message.delete()
    await show_last_result(callback.from_user.id, session, callback)


@router.callback_query(F.data == "action:get_pdf")
async def cb_get_pdf(callback: CallbackQuery, session: AsyncSession):
    """Отправляет PDF отчет по последней диагностике с рекомендациями (price = mid по умолчанию)."""
    stmt = (
        select(DiagnosisResult)
        .join(SurveyResponse)
        .where(SurveyResponse.user_id == callback.from_user.id)
        .order_by(DiagnosisResult.created_at.desc())
    )
    result = await session.execute(stmt)
    last_diagnosis = result.scalars().first()

    if not last_diagnosis:
        await callback.answer("Сначала пройдите диагностику.", show_alert=True)
        return

    diagnosis_data = last_diagnosis.result_json
    # строим рекомендации так же, как в боевом пайплайне
    rec = build_recommendations(diagnosis_data)
    if not rec.get("products"):
        await callback.answer(
            "Сейчас рекомендации пустые. Попробуйте позже.", show_alert=True
        )
        return
    out_path = f"out/{callback.from_user.id}.pdf"
    pdf_path = await build_pdf(diagnosis_data, rec, out_path)
    with open(pdf_path, "rb") as f:
        await callback.message.answer_document(
            BufferedInputFile(f.read(), filename="skin_advisor_report.pdf"),
            caption="Ваш персональный отчет по уходу за кожей.",
        )
    await callback.answer()
