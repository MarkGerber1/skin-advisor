from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message

from app.ui.keyboard import build_main_menu
from app.services.recommendation import build_recommendations
from app.ui.messages import render_item_text_with_link


router = Router()

BTN_SURVEY = "🧪 Пройти анкету"
BTN_RECO = "📄 Мои рекомендации"
BTN_BAL = "💰 Баланс"
BTN_REF = "🔗 Моя реферальная ссылка"


@router.message(Command("menu"), StateFilter(None))
async def menu_cmd(m: Message):
    await m.answer("Меню", reply_markup=build_main_menu())


@router.message(F.text == BTN_RECO, StateFilter(None))
async def my_reco(m: Message):
    # Заглушка профиля (лучше брать из БД последнюю анкету)
    user_profile = {"skin_type": "normal", "concerns": []}
    try:
        rec = build_recommendations(user_profile)
    except Exception:
        await m.answer(
            "Не удалось собрать рекомендации. Попробуйте позже.",
            reply_markup=build_main_menu(),
        )
        return
    products = rec.get("products", [])
    if not products:
        await m.answer(
            "Сейчас нет позиций в наличии. Нажмите «📄 Мои рекомендации» позже или пройдите анкету заново.",
            reply_markup=build_main_menu(),
        )
        return
    # ограничим выдачу: до 2-3 на каждую ключевую секцию
    sections = {"am": 3, "pm": 3, "weekly": 2}
    routines = rec.get("routines", {})
    shown_ids = set()
    for sec, limit in sections.items():
        ids = routines.get(sec, [])[:limit]
        for pid in ids:
            it = next(
                (
                    p
                    for p in products
                    if p.get("id") == pid and p.get("id") not in shown_ids
                ),
                None,
            )
            if not it:
                continue
            shown_ids.add(it.get("id"))
            text = render_item_text_with_link(it)
            await m.answer(text, parse_mode="HTML")
    await m.answer("Готово ✅", reply_markup=build_main_menu())
    await m.answer("Готово ✅", reply_markup=build_main_menu())


@router.message(F.text == BTN_SURVEY, StateFilter(None))
async def survey_entry(m: Message):
    from app.handlers.survey import _begin_survey  # reuse existing

    # для /menu запускаем новую анкету
    await _begin_survey(
        m, m.bot["fsm_context"], m.bot["session"]
    )  # may be replaced with a proper call


@router.message(F.text == BTN_BAL, StateFilter(None))
async def balance(m: Message):
    await m.answer("Ваш баланс: 0 баллов", reply_markup=build_main_menu())


@router.message(F.text == BTN_REF, StateFilter(None))
async def my_ref(m: Message):
    await m.answer(
        "Ваша реферальная ссылка: скоро добавим", reply_markup=build_main_menu()
    )
