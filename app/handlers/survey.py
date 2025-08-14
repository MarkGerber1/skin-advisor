from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, BufferedInputFile, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, update, func
import logging

from app.domain.diagnosis import diagnose_skin
from app.infra.models import (
    SurveyResponse,
    DiagnosisResult,
    SurveySession,
    Recommendation,
    Download,
)
from app.ui import keyboards, messages
from app.ui.keyboard import build_main_menu
from app.services.recommendation import build_recommendations
from pdf_report import build_pdf

router = Router()
logger = logging.getLogger(__name__)


class SurveyStates(StatesGroup):
    Q1 = State()
    Q2 = State()
    Q3 = State()
    Q4 = State()
    Q5 = State()
    Q6 = State()
    Q7 = State()
    Q8 = State()
    Q9 = State()
    Q10 = State()
    Q11 = State()
    Q12 = State()
    Q13 = State()
    Q14 = State()
    CONFIRM = State()


QUESTIONS = [
    {
        "id": "Q1",
        "state": SurveyStates.Q1,
        "text": messages.LEXICON["q1"],
        "multi": False,
        "options": {"Q1_A1": "Да", "Q1_A2": "Нет"},
    },
    {
        "id": "Q2",
        "state": SurveyStates.Q2,
        "text": messages.LEXICON["q2"],
        "multi": False,
        "options": {
            "Q2_A1": "Жирный блеск через 2–3 часа",
            "Q2_A2": "Жирный блеск к вечеру",
            "Q2_A3": "К обеду стянутость",
            "Q2_A4": "Т‑зона блестит, периферия стянута",
        },
    },
    {
        "id": "Q3",
        "state": SurveyStates.Q3,
        "text": messages.LEXICON["q3"],
        "multi": False,
        "options": {
            "Q3_A1": "Практически незаметны",
            "Q3_A2": "Немного в Т‑зоне",
            "Q3_A3": "Чётко видны на щеках и носу",
            "Q3_A4": "Сильно по всей поверхности",
        },
    },
    {
        "id": "Q4",
        "state": SurveyStates.Q4,
        "text": messages.LEXICON["q4"],
        "multi": False,
        "options": {"Q4_A1": "Да", "Q4_A2": "Нет"},
    },
    {
        "id": "Q5",
        "state": SurveyStates.Q5,
        "text": messages.LEXICON["q5"],
        "multi": True,
        "options": {
            "Q5_A1": "Чёрные точки в Т‑зоне",
            "Q5_A2": "Иногда единичные воспаления",
            "Q5_A3": "Кожа чистая и ровная",
        },
    },
    {
        "id": "Q6",
        "state": SurveyStates.Q6,
        "text": messages.LEXICON["q6"],
        "multi": False,
        "options": {
            "Q6_A1": "Отсутствует",
            "Q6_A2": "В отдельных зонах",
            "Q6_A3": "По всей поверхности",
        },
    },
    {
        "id": "Q7",
        "state": SurveyStates.Q7,
        "text": messages.LEXICON["q7"],
        "multi": False,
        "options": {
            "Q7_A1": "Нет",
            "Q7_A2": "В отдельных зонах",
            "Q7_A3": "По всей поверхности",
        },
    },
    {
        "id": "Q8",
        "state": SurveyStates.Q8,
        "text": messages.LEXICON["q8"],
        "multi": False,
        "options": {
            "Q8_A1": "Нет выраженных",
            "Q8_A2": "Немного, в основном мимические",
            "Q8_A3": "Хорошо видны мелкие и крупные",
        },
    },
    {
        "id": "Q9",
        "state": SurveyStates.Q9,
        "text": messages.LEXICON["q9"],
        "multi": True,
        "options": {
            "Q9_A1": "Частые отёки/мешки",
            "Q9_A2": "Тёмные круги",
            "Q9_A3": "Морщины вокруг глаз",
            "Q9_A4": "Всё в порядке",
        },
    },
    {
        "id": "Q10",
        "state": SurveyStates.Q10,
        "text": messages.LEXICON["q10"],
        "multi": False,
        "options": {"Q10_A1": "Да", "Q10_A2": "Нет"},
    },
    {
        "id": "Q11",
        "state": SurveyStates.Q11,
        "text": messages.LEXICON["q11"],
        "multi": False,
        "options": {
            "Q11_A1": "Да, всё ровно",
            "Q11_A2": "Тусклая/уставшая кожа",
            "Q11_A3": "Покраснения/сосудики",
            "Q11_A4": "Шелушения/раздражения",
        },
    },
    {
        "id": "Q12",
        "state": SurveyStates.Q12,
        "text": messages.LEXICON["q12"],
        "multi": False,
        "options": {
            "Q12_A1": "Есть купероз",
            "Q12_A2": "Есть небольшие «звёздочки»",
            "Q12_A3": "Нет",
        },
    },
    {
        "id": "Q13",
        "state": SurveyStates.Q13,
        "text": messages.LEXICON["q13"],
        "multi": False,
        "options": {
            "Q13_A1": "Тёплый (вены зеленоватые)",
            "Q13_A2": "Холодный (вены синеватые)",
            "Q13_A3": "Нейтральный",
        },
    },
    {
        "id": "Q14",
        "state": SurveyStates.Q14,
        "text": messages.LEXICON["q14"],
        "multi": False,
        "options": {
            "Q14_A1": "Карие",
            "Q14_A2": "Синие",
            "Q14_A3": "Зелёные",
            "Q14_A4": "Серые",
            "Q14_A5": "Ореховые",
        },
    },
]


# Удалили перехват /start здесь, чтобы /start показывал главное меню в start.py


@router.message(Command("resume"))
async def resume(message: Message, state: FSMContext):
    data = await state.get_data()
    q_index = data.get("current_q", 0)
    if q_index >= len(QUESTIONS):
        await message.answer(
            "Анкета уже завершена. Нажмите Рекомендации для выдачи.",
            reply_markup=keyboards.set_main_menu(),
        )
        return
    await ask_question(message, state)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    await message.answer("Анкета отменена. Вы можете начать заново командой /start.")
    await session.execute(
        update(SurveySession)
        .where(SurveySession.user_id == message.from_user.id)
        .values(status="aborted")
    )
    await session.commit()


@router.message(F.text == messages.LEXICON["btn_start_survey"], StateFilter(None))
async def start_from_button(message: Message, state: FSMContext, session: AsyncSession):
    """Запуск анкеты по кнопке из главного меню."""
    try:
        await _begin_survey(message, state, session)
    except Exception:
        logger.exception("start_from_button error")
        await message.answer("Не удалось запустить анкету. Попробуйте /start")


# Альтернативный запуск по тексту из нового нижнего меню
@router.message(F.text == "🧪 Пройти анкету", StateFilter(None))
async def start_from_main_menu_text(
    message: Message, state: FSMContext, session: AsyncSession
):
    try:
        await _begin_survey(message, state, session)
    except Exception:
        logger.exception("start_from_main_menu_text error")
        await message.answer("Не удалось запустить анкету. Попробуйте /start")


@router.message(Command("reset"))
@router.message(
    F.text == messages.LEXICON["btn_reset"]
)  # работает всегда, в любом состоянии
async def reset_and_restart(message: Message, state: FSMContext, session: AsyncSession):
    """Сброс текущей анкеты и запуск новой."""
    try:
        await state.clear()
        # пометим предыдущую сессию как прерванную
        await session.execute(
            update(SurveySession)
            .where(SurveySession.user_id == message.from_user.id)
            .values(status="aborted")
        )
        await session.commit()
        await _begin_survey(message, state, session)
    except Exception:
        logger.exception("reset_and_restart error")
        await message.answer("Не удалось перезапустить. Попробуйте /start")


async def ask_question(message: Message, state: FSMContext):
    data = await state.get_data()
    q_index = data.get("current_q", 0)
    if q_index >= len(QUESTIONS):
        await state.set_state(SurveyStates.CONFIRM)
        await message.answer(
            messages.LEXICON["survey_finish_prompt"],
            reply_markup=keyboards.create_confirm_keyboard(
                "action:show_results", messages.LEXICON["btn_show_results"]
            ),
        )
        return
    question = QUESTIONS[q_index]
    progress_text = messages.LEXICON["survey_progress"].format(
        current=q_index + 1, total=len(QUESTIONS)
    )
    await message.answer(
        f"{progress_text}\n\n{question['text']}",
        reply_markup=keyboards.create_survey_keyboard(
            question["id"], question["options"], question["multi"]
        ),
    )


@router.callback_query(F.data.startswith("survey:"))
async def handle_survey_answer(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    try:
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer()
            return
        _, q_id, answer = parts
        data = await state.get_data()
        q_index = data.get("current_q", 0)
        question = QUESTIONS[q_index]
        if question["multi"]:
            current_answers = data.get(q_id)
            if not isinstance(current_answers, list):
                current_answers = []
            if answer != "next":
                if answer in current_answers:
                    current_answers.remove(answer)
                else:
                    current_answers.append(answer)
                await state.update_data({q_id: current_answers})
                await callback.answer(
                    f"Выбрано: {len(current_answers)}. Нажмите 'Далее ➡️'"
                )
                return
        else:
            await state.update_data({q_id: answer})
        # переходим к следующему вопросу: аккуратно удаляем пред. сообщение, если оно существует
        try:
            await callback.message.delete()
        except Exception:
            pass
        q_index += 1
        await state.update_data(current_q=q_index)
        if q_index >= len(QUESTIONS):
            await finalize_survey(callback.message, state, session)
        else:
            await ask_question(callback.message, state)
    except Exception:
        logger.exception("survey step error")
        await callback.message.answer(
            "Произошла ошибка. Попробуйте еще раз /resume или /start"
        )
        await callback.answer()


async def finalize_survey(message: Message, state: FSMContext, session: AsyncSession):
    try:
        answers = await state.get_data()
        await state.clear()
        survey_response = SurveyResponse(user_id=message.chat.id, answers_json=answers)
        session.add(survey_response)
        await session.flush()
        diagnosis_data = diagnose_skin(answers)
        diagnosis_result = DiagnosisResult(
            survey_response_id=survey_response.id, result_json=diagnosis_data
        )
        session.add(diagnosis_result)
        await session.execute(
            update(SurveySession)
            .where(SurveySession.user_id == message.chat.id)
            .values(
                status="completed",
                finished_at=func.now(),
                updated_at=func.now(),
                answers_json=answers,
            )
        )
        await session.commit()

        rec = build_recommendations(diagnosis_data)
        rec_row = Recommendation(
            session_id=survey_response.id,
            summary_json=rec.get("summary", {}),
            products_json={"products": rec.get("products", [])},
            unavailable_json={"ids": rec.get("unavailable", [])},
            replaced_json={"pairs": rec.get("replaced", [])},
        )
        session.add(rec_row)
        await session.commit()

        # pdf only if there are products
        pdf_path = None
        if rec.get("products"):
            out_path = f"out/{message.chat.id}.pdf"
            pdf_path = await build_pdf(diagnosis_data, rec, out_path)
            session.add(Download(session_id=survey_response.id, pdf_path=pdf_path))
            await session.commit()

        await message.answer(
            messages.LEXICON["survey_finish_prompt"],
            reply_markup=build_main_menu(),
        )
        if pdf_path:
            await message.answer_document(
                BufferedInputFile(
                    open(pdf_path, "rb").read(), filename="skin_advisor_report.pdf"
                ),
                caption="Ваш персональный план ухода",
            )
            # Также отправим до 6 карточек с кнопкой "Купить"
            shown = 0
            for item in rec.get("products", []):
                if shown >= 6:
                    break
                try:
                    from app.ui.messages import render_item_text
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

                    text = render_item_text(item)
                    ref = item.get("ref_link") or ""
                    kb = InlineKeyboardMarkup(
                        inline_keyboard=[[InlineKeyboardButton(text="Купить", url=ref)]]
                    )
                    await message.answer(text, reply_markup=kb)
                except Exception:
                    pass
                shown += 1
        else:
            await message.answer("Пока ничего в наличии не нашли. Попробуйте позже.")
    except Exception:
        logger.exception("finalize error")
        await message.answer("Сбой при завершении анкеты. Попробуйте /start заново.")


async def _begin_survey(message: Message, state: FSMContext, session: AsyncSession):
    """Начинает (или перезапускает) прохождение анкеты."""
    await state.clear()
    await state.set_state(SurveyStates.Q1)
    await state.update_data(current_q=0)
    # убираем главное меню на время анкеты, чтобы кнопка "Сброс" не мешала
    await message.answer("Начинаем анкету…", reply_markup=ReplyKeyboardRemove())
    await session.execute(
        insert(SurveySession).values(
            user_id=message.from_user.id, status="started", answers_json={}
        )
    )
    await session.commit()
    await ask_question(message, state)
