"""
Подробный тест на тип и состояние лица (8 вопросов)
Основан на профессиональном файле "УЛУЧШЕННЫЙ ТЕСТ НА ЦВЕТОТИП ВНЕШНОС.txt"
"""
from __future__ import annotations

import os
from typing import List, Dict
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from engine.catalog_store import CatalogStore
from engine.models import UserProfile, SkinType, ReportData
from engine.selector import SelectorV2
from engine.answer_expander import AnswerExpanderV2
from bot.ui.keyboards import add_home_button

# Analytics import with fallback
try:
    from engine.analytics import get_analytics_tracker
    ANALYTICS_AVAILABLE = True
except ImportError:
    print("⚠️ analytics not available in detailed_skincare")
    ANALYTICS_AVAILABLE = False
    def get_analytics_tracker():
        return None

router = Router()

class DetailedSkincareFlow(StatesGroup):
    # 8 детальных вопросов для определения типа и состояния лица
    Q1_TIGHTNESS = State()       # Ощущение стянутости после умывания
    Q2_SUN_REACTION = State()    # Реакция лица на солнце  
    Q3_IMPERFECTIONS = State()   # Основные несовершенства
    Q4_EYE_AREA = State()        # Состояние зоны вокруг глаз
    Q5_COUPEROSE = State()       # Купероз/сосудистые звездочки
    Q6_CURRENT_CARE = State()    # Текущий уход
    Q7_ALLERGIES = State()       # Аллергические реакции
    Q8_DESIRED_EFFECT = State()  # Желаемый эффект от ухода
    RESULT = State()             # Результат теста


def _kb_tightness() -> InlineKeyboardMarkup:
    """Q1: Ощущение стянутости через 30 минут после умывания"""
    buttons = [
        [InlineKeyboardButton(text="a) Да, есть шелушения", callback_data="tightness:a")],
        [InlineKeyboardButton(text="b) Нет, ощущения комфортны", callback_data="tightness:b")],
        [InlineKeyboardButton(text="c) Только в Т-зоне", callback_data="tightness:c")],
        [InlineKeyboardButton(text="d) Периодически, зависит от времени года", callback_data="tightness:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_sun_reaction() -> InlineKeyboardMarkup:
    """Q2: Реакция лица на солнце"""
    buttons = [
        [InlineKeyboardButton(text="a) Быстро загорает без ожогов", callback_data="sun:a")],
        [InlineKeyboardButton(text="b) Загорает с трудом, появляются веснушки", callback_data="sun:b")],
        [InlineKeyboardButton(text="c) Мгновенно обгорает, появляется пигментация", callback_data="sun:c")],
        [InlineKeyboardButton(text="d) Не реагирует, сохраняет тон", callback_data="sun:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_imperfections() -> InlineKeyboardMarkup:
    """Q3: Основные несовершенства"""
    buttons = [
        [InlineKeyboardButton(text="a) Расширенные поры и черные точки", callback_data="imperfections:a")],
        [InlineKeyboardButton(text="b) Воспаления и акне", callback_data="imperfections:b")],
        [InlineKeyboardButton(text="c) Сухость и шелушение", callback_data="imperfections:c")],
        [InlineKeyboardButton(text="d) Пигментные пятна и покраснения", callback_data="imperfections:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_eye_area() -> InlineKeyboardMarkup:
    """Q4: Состояние зоны вокруг глаз"""
    buttons = [
        [InlineKeyboardButton(text="a) Мешки и отеки", callback_data="eye:a")],
        [InlineKeyboardButton(text="b) Темные круги", callback_data="eye:b")],
        [InlineKeyboardButton(text="c) Мимические морщины", callback_data="eye:c")],
        [InlineKeyboardButton(text="d) Упругая и ровная", callback_data="eye:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_couperose() -> InlineKeyboardMarkup:
    """Q5: Купероз или сосудистые звездочки"""
    buttons = [
        [InlineKeyboardButton(text="a) Да, выраженные", callback_data="couperose:a")],
        [InlineKeyboardButton(text="b) Незначительные", callback_data="couperose:b")],
        [InlineKeyboardButton(text="c) Отсутствуют", callback_data="couperose:c")],
        [InlineKeyboardButton(text="d) Появляются при перепадах температур", callback_data="couperose:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_current_care() -> InlineKeyboardMarkup:
    """Q6: Текущий уход"""
    buttons = [
        [InlineKeyboardButton(text="a) Минимальный (очищение + увлажнение)", callback_data="care:a")],
        [InlineKeyboardButton(text="b) Полный (очищение, тоник, сыворотка, крем)", callback_data="care:b")],
        [InlineKeyboardButton(text="c) Профессиональный с SPF и специальными средствами", callback_data="care:c")],
        [InlineKeyboardButton(text="d) Не использую уходовые средства", callback_data="care:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_allergies() -> InlineKeyboardMarkup:
    """Q7: Аллергические реакции на косметику"""
    buttons = [
        [InlineKeyboardButton(text="a) Часто", callback_data="allergies:a")],
        [InlineKeyboardButton(text="b) Редко", callback_data="allergies:b")],
        [InlineKeyboardButton(text="c) Нет", callback_data="allergies:c")],
        [InlineKeyboardButton(text="d) Не знаю, не проверял(а)", callback_data="allergies:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_desired_effect() -> InlineKeyboardMarkup:
    """Q8: Желаемый эффект от ухода"""
    buttons = [
        [InlineKeyboardButton(text="a) Увлажнение и питание", callback_data="effect:a")],
        [InlineKeyboardButton(text="b) Контроль жирности", callback_data="effect:b")],
        [InlineKeyboardButton(text="c) Антивозрастной уход", callback_data="effect:c")],
        [InlineKeyboardButton(text="d) Выравнивание тона и текстуры", callback_data="effect:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def determine_skin_type(answers: Dict[str, str]) -> Dict[str, str]:
    """
    Определение типа и состояния кожи на основе ответов
    Возвращает словарь с типом кожи и основными проблемами
    """
    skin_analysis = {
        "type": "normal",
        "concerns": [],
        "sensitivity": "normal",
        "care_level": "basic"
    }
    
    # Q1: Стянутость после умывания
    tightness = answers.get("tightness", "")
    if tightness == "a":  # Да, шелушится
        skin_analysis["type"] = "dry"
        skin_analysis["concerns"].append("dehydration")
    elif tightness == "c":  # Только в Т-зоне
        skin_analysis["type"] = "combination"
    elif tightness == "d":  # Периодически
        skin_analysis["concerns"].append("seasonal_changes")

    # Q2: Реакция на солнце
    sun = answers.get("sun", "")
    if sun == "c":  # Обгорает, пигментация
        skin_analysis["concerns"].append("pigmentation")
        skin_analysis["sensitivity"] = "sensitive"

    # Q3: Основные несовершенства
    imperfections = answers.get("imperfections", "")
    if imperfections == "a":  # Поры и черные точки
        if skin_analysis["type"] != "dry":
            skin_analysis["type"] = "oily"
        skin_analysis["concerns"].append("enlarged_pores")
    elif imperfections == "b":  # Воспаления и акне
        skin_analysis["type"] = "oily"
        skin_analysis["concerns"].append("acne")
    elif imperfections == "c":  # Сухость и шелушение
        skin_analysis["type"] = "dry"
        skin_analysis["concerns"].append("dehydration")
    elif imperfections == "d":  # Пигментация и покраснения
        skin_analysis["concerns"].extend(["pigmentation", "redness"])

    # Q4: Зона глаз
    eye = answers.get("eye", "")
    if eye == "a":  # Мешки и отеки
        skin_analysis["concerns"].append("puffiness")
    elif eye == "b":  # Темные круги
        skin_analysis["concerns"].append("dark_circles")
    elif eye == "c":  # Морщины
        skin_analysis["concerns"].append("aging")

    # Q5: Купероз
    couperose = answers.get("couperose", "")
    if couperose in ["a", "b", "d"]:  # Есть купероз
        skin_analysis["concerns"].append("couperose")
        skin_analysis["sensitivity"] = "sensitive"

    # Q6: Текущий уход
    care = answers.get("care", "")
    if care == "b":  # Полный уход
        skin_analysis["care_level"] = "advanced"
    elif care == "c":  # Профессиональный
        skin_analysis["care_level"] = "professional"
    elif care == "d":  # Не использую
        skin_analysis["care_level"] = "none"

    # Q7: Аллергии
    allergies = answers.get("allergies", "")
    if allergies == "a":  # Часто
        skin_analysis["sensitivity"] = "very_sensitive"
    elif allergies == "b":  # Редко
        skin_analysis["sensitivity"] = "sensitive"

    # Q8: Желаемый эффект
    effect = answers.get("effect", "")
    if effect == "a":  # Увлажнение
        if "dehydration" not in skin_analysis["concerns"]:
            skin_analysis["concerns"].append("hydration_needed")
    elif effect == "b":  # Контроль жирности
        if skin_analysis["type"] != "dry":
            skin_analysis["type"] = "oily"
    elif effect == "c":  # Антивозрастной
        skin_analysis["concerns"].append("aging")

    return skin_analysis


async def start_detailed_skincare_flow(message: Message, state: FSMContext) -> None:
    """Запуск детального теста на тип лица"""
    user_id = message.from_user.id if message.from_user else 0
    print(f"🧴 Starting detailed skincare flow for user {user_id}")
    
    # Analytics: Track test start
    if ANALYTICS_AVAILABLE:
        analytics = get_analytics_tracker()
        if analytics:
            analytics.user_started_test(user_id, "skin")
    
    # Store test start time for completion analytics
    import time
    await state.update_data(test_start_time=time.time())
    
    await state.clear()
    await state.set_state(DetailedSkincareFlow.Q1_TIGHTNESS)
    
    # Import i18n for subtitles
    try:
        from i18n.ru import SKINCARE_TEST_SUBTITLE
        subtitle = SKINCARE_TEST_SUBTITLE
    except ImportError:
        subtitle = "10 вопросов · 2 минуты · соберём уход и SPF по целям"
    
    await message.answer(
        "🧴 **ПОРТРЕТ ЛИЦА**\n\n"
        f"_{subtitle}_\n\n"
        "Ответьте честно на вопросы, чтобы определить ваш тип и состояние лица "
        "и получить персональные рекомендации по уходовой косметике.\n\n"
        "**Вопрос 1 из 10**\n"
        "🚿 Есть ли ощущение стянутости через 30 минут после умывания?",
        reply_markup=_kb_tightness(),
        parse_mode="Markdown"
    )


# Handlers for each question
@router.callback_query(F.data.startswith("tightness:"), DetailedSkincareFlow.Q1_TIGHTNESS)
async def q1_tightness(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(tightness=answer)
        await state.set_state(DetailedSkincareFlow.Q2_SUN_REACTION)
        
        await cb.message.edit_text(
            "**Вопрос 2 из 10**\n"
            "☀️ Как ваше лицо реагирует на солнце?",
            reply_markup=_kb_sun_reaction()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q1_tightness: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("sun:"), DetailedSkincareFlow.Q2_SUN_REACTION)
async def q2_sun_reaction(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(sun=answer)
        await state.set_state(DetailedSkincareFlow.Q3_IMPERFECTIONS)
        
        await cb.message.edit_text(
            "**Вопрос 3 из 10**\n"
            "🎯 Какие несовершенства беспокоят чаще всего?",
            reply_markup=_kb_imperfections()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q2_sun_reaction: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("imperfections:"), DetailedSkincareFlow.Q3_IMPERFECTIONS)
async def q3_imperfections(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(imperfections=answer)
        await state.set_state(DetailedSkincareFlow.Q4_EYE_AREA)
        
        await cb.message.edit_text(
            "**Вопрос 4 из 10**\n"
            "👁️ Как выглядит зона вокруг глаз?",
            reply_markup=_kb_eye_area()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q3_imperfections: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("eye:"), DetailedSkincareFlow.Q4_EYE_AREA)
async def q4_eye_area(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(eye=answer)
        await state.set_state(DetailedSkincareFlow.Q5_COUPEROSE)
        
        await cb.message.edit_text(
            "**Вопрос 5 из 10**\n"
            "🩸 Есть ли купероз или сосудистые звездочки?",
            reply_markup=_kb_couperose()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q4_eye_area: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("couperose:"), DetailedSkincareFlow.Q5_COUPEROSE)
async def q5_couperose(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(couperose=answer)
        await state.set_state(DetailedSkincareFlow.Q6_CURRENT_CARE)
        
        await cb.message.edit_text(
            "**Вопрос 6 из 10**\n"
            "🧴 Какой уход вы используете сейчас?",
            reply_markup=_kb_current_care()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q5_couperose: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("care:"), DetailedSkincareFlow.Q6_CURRENT_CARE)
async def q6_current_care(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(care=answer)
        await state.set_state(DetailedSkincareFlow.Q7_ALLERGIES)
        
        await cb.message.edit_text(
            "**Вопрос 7 из 10**\n"
            "⚠️ Есть ли аллергические реакции на косметику?",
            reply_markup=_kb_allergies()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q6_current_care: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("allergies:"), DetailedSkincareFlow.Q7_ALLERGIES)
async def q7_allergies(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(allergies=answer)
        await state.set_state(DetailedSkincareFlow.Q8_DESIRED_EFFECT)
        
        await cb.message.edit_text(
            "**Вопрос 8 из 10**\n"
            "🎯 Какой эффект вы хотите получить от ухода?",
            reply_markup=_kb_desired_effect()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q7_allergies: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("effect:"), DetailedSkincareFlow.Q8_DESIRED_EFFECT)
async def q8_desired_effect(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(effect=answer)
        await state.set_state(DetailedSkincareFlow.RESULT)
        
        # Анализируем результаты
        data = await state.get_data()
        skin_analysis = determine_skin_type(data)
        
        # Создаем UserProfile для системы рекомендаций
        from engine.models import UserProfile, SkinType, Sensitivity
        from engine.selector import SelectorV2
        from engine.catalog_store import CatalogStore
        from engine.answer_expander import AnswerExpanderV2
        from engine.models import ReportData
        from bot.ui.pdf import save_last_json, save_text_pdf
        from bot.ui.render import render_skincare_report
        import os
        
        # Определяем тип лица для Engine
        skin_type_mapping = {
            "dry": SkinType.DRY,
            "oily": SkinType.OILY,
            "combination": SkinType.COMBO,  # Исправлено: COMBO, не COMBINATION
            "normal": SkinType.NORMAL
        }
        
        # Определяем чувствительность
        sensitivity_mapping = {
            "normal": Sensitivity.LOW,
            "sensitive": Sensitivity.MID,  # Исправлено: MID, не MEDIUM
            "very_sensitive": Sensitivity.HIGH
        }
        
        skin_type = skin_analysis["type"]
        sensitivity = skin_analysis["sensitivity"]
        concerns = skin_analysis["concerns"]
        
        # Получаем uid пользователя
        uid = int(cb.from_user.id) if cb.from_user and cb.from_user.id else 0
        
        # Создаем профиль пользователя
        profile = UserProfile(
            user_id=uid,  # Добавлено обязательное поле
            skin_type=skin_type_mapping.get(skin_type, SkinType.NORMAL),
            sensitivity=sensitivity_mapping.get(sensitivity, Sensitivity.LOW),
            age=25,  # Примерный возраст
            acne_prone="acne" in concerns,
            dehydrated="dehydration" in concerns or "hydration_needed" in concerns,
            enlarged_pores="enlarged_pores" in concerns,
            pigmentation="pigmentation" in concerns,
            anti_aging="aging" in concerns,
            couperose="couperose" in concerns
        )
        
        # Получаем каталог продуктов
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()
        
        # ДИАГНОСТИКА: Проверяем каталог перед селектором
        print(f"📊 CATALOG DIAGNOSTIC:")
        print(f"  📦 Total products in catalog: {len(catalog)}")
        
        # Подсчитываем товары по категориям
        category_counts = {}
        skincare_products_found = []
        for product in catalog:
            cat = product.category.lower() if product.category else "unknown"
            category_counts[cat] = category_counts.get(cat, 0) + 1
            
            # Проверяем на skincare
            skincare_keywords = ["очищ", "тоник", "сыв", "крем", "маск", "spf", "санскрин", "cleanser", "serum", "moisturizer"]
            if any(keyword in cat for keyword in skincare_keywords):
                skincare_products_found.append(f"{product.brand} {product.title} (category: {cat})")
        
        print(f"  📋 Categories found: {dict(sorted(category_counts.items()))}")
        print(f"  🧴 Potential skincare products found: {len(skincare_products_found)}")
        for i, prod in enumerate(skincare_products_found[:5]):  # Show first 5
            print(f"    {i+1}. {prod}")
        if len(skincare_products_found) > 5:
            print(f"    ... and {len(skincare_products_found) - 5} more")
        
        # Генерируем рекомендации через SelectorV2
        selector = SelectorV2()
        print(f"🔧 DETAILED SKINCARE: Calling selector with profile: skin_type={profile.skin_type}, concerns={[c for c in concerns]}")
        result = selector.select_products_v2(
            profile=profile,
            catalog=catalog,
            partner_code=os.getenv("PARTNER_CODE", "aff_skinbot"),
            redirect_base=os.getenv("REDIRECT_BASE")  # None = direct links with aff param
        )
        print(f"📦 DETAILED SKINCARE result: {list(result.keys()) if result else 'None'}")
        if result and result.get("skincare"):
            for step, products in result["skincare"].items():
                print(f"  🧴 Step {step}: {len(products)} products")
        
        # Извлекаем продукты для ухода за кожей
        skincare_products = []
        skincare_data = result.get("skincare", {})
        print(f"📊 DETAILED SKINCARE: skincare_data keys: {list(skincare_data.keys())}")
        for step_name, time_products in skincare_data.items():
            if isinstance(time_products, list):
                print(f"  ✅ Step {step_name}: {len(time_products)} products available")
                skincare_products.extend(time_products[:2])  # Первые 2 из каждой категории
            else:
                print(f"  ⚠️ Step {step_name}: unexpected type {type(time_products)}")
        
        print(f"📦 DETAILED SKINCARE: Total extracted {len(skincare_products)} products")
        
        # КРИТИЧЕСКИ ВАЖНО: Сохраняем профиль в FSM coordinator для корзины
        from bot.handlers.fsm_coordinator import get_fsm_coordinator
        coordinator = get_fsm_coordinator()
        
        # Обновляем сессию с данными профиля для корзины
        try:
            session = await coordinator.get_session(uid)
            if session:
                # Добавляем профиль пользователя в flow_data
                session.flow_data.update({
                    "skin_type": skin_type,
                    "sensitivity": sensitivity, 
                    "concerns": concerns,
                    "test_type": "detailed_skincare"
                })
                print(f"✅ SAVED profile to FSM coordinator: skin_type={skin_type}, concerns={concerns}")
            else:
                print(f"⚠️ No FSM session found for user {uid} - creating new session for cart")
        except Exception as session_error:
            print(f"❌ Error saving profile to FSM: {session_error}")
        
        # Генерируем отчет
        report_data = ReportData(
            user_profile=profile,
            skincare_products=skincare_products,
            makeup_products=[]
        )
        
        expander = AnswerExpanderV2()
        tldr_report = expander.generate_tldr_report(report_data)
        full_report = expander.generate_full_report(report_data)
        
        # Сохраняем результат для пользователя
        uid = int(cb.from_user.id) if cb.from_user and cb.from_user.id else 0
        if uid:
            snapshot = {
                "type": "detailed_skincare",
                "profile": profile.model_dump(),
                "result": result,
                "skin_analysis": skin_analysis,
                "tl_dr": tldr_report,
                "full_text": full_report,
                "answers": data
            }
            save_last_json(uid, snapshot)
            save_text_pdf(uid, title="🧴 Отчёт по уходу за кожей", body_text=full_report)
        
        # Сохраняем профиль в FSM coordinator для корзины
        print(f"💾 Saving profile to FSM coordinator for user {uid}")
        from bot.handlers.fsm_coordinator import get_fsm_coordinator
        coordinator = get_fsm_coordinator()
        # Используем update_step для сохранения профиля
        await coordinator.update_step(uid, "RESULT", {
            "user_id": uid,
            "skin_type": skin_type,
            "concerns": concerns,
            "sensitivity": sensitivity,
            "test_type": "detailed_skincare",
            "profile": profile.model_dump()
        })
        
        # Сохраняем профиль в user_profile_store
        from bot.handlers.user_profile_store import get_user_profile_store
        profile_store = get_user_profile_store()
        profile_data = {
            "user_id": uid,
            "skin_type": skin_type,
            "concerns": concerns,
            "sensitivity": sensitivity,
            "season": "spring",  # default
            "undertone": "neutral",  # default
            "contrast": "medium"  # default
        }
        profile_store.save_profile(uid, profile_data)
        print(f"✅ Profile saved to user_profile_store for user {uid}")

        # Сохраняем результат в состояние
        await state.update_data(
            skin_analysis=skin_analysis,
            profile=profile.model_dump(),
            result=result,
            skincare_products=skincare_products,
            tldr_report=tldr_report,
            full_report=full_report
        )
        print(f"✅ Profile and results saved successfully")
        
        # Показываем результат
        skin_type_names = {
            "dry": "🏜️ Сухой тип",
            "oily": "🛢️ Жирный тип",
            "combination": "⚖️ Комбинированный тип",
            "normal": "✨ Нормальный тип"
        }
        
        # Формируем описание состояния
        concerns_text = ""
        if concerns:
            concerns_readable = {
                "dehydration": "обезвоженность",
                "pigmentation": "пигментация", 
                "acne": "акне",
                "enlarged_pores": "расширенные поры",
                "aging": "возрастные изменения",
                "couperose": "купероз",
                "redness": "покраснения",
                "puffiness": "отечность",
                "dark_circles": "темные круги",
                "seasonal_changes": "сезонные изменения",
                "hydration_needed": "нужно увлажнение"
            }
            concerns_list = [concerns_readable.get(c, c) for c in concerns[:3]]  # Первые 3 проблемы
            concerns_text = f"\n**Основные проблемы:** {', '.join(concerns_list)}"
            
        sensitivity_text = ""
        if sensitivity != "normal":
            sensitivity_names = {
                "sensitive": "чувствительная",
                "very_sensitive": "очень чувствительная"
            }
            sensitivity_text = f"\n**Чувствительность:** {sensitivity_names[sensitivity]}"
        
        # Import i18n for skincare picker
        try:
            from i18n.ru import HEAD_SKINCARE_PICK, SUB_PICK
            pick_header = HEAD_SKINCARE_PICK
            pick_subtitle = SUB_PICK
        except ImportError:
            pick_header = "Подборка ухода по результатам"
            pick_subtitle = "Выберите категорию, затем добавьте средства в корзину"

        await cb.message.edit_text(
            f"🎉 **РЕЗУЛЬТАТ ДИАГНОСТИКИ**\n\n"
            f"**Ваш тип лица:** {skin_type_names[skin_type]}{concerns_text}{sensitivity_text}\n\n"
            f"📊 **Краткий анализ:**\n{tldr_report}\n\n"
            f"---\n\n"
            f"🛍️ **{pick_header}**\n"
            f"_{pick_subtitle}_\n\n"
            f"Что вы хотите увидеть?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🧴 Подобрать уход", callback_data="skincare_picker:start")],
                [InlineKeyboardButton(text="ℹ️ Полное описание типа лица", callback_data="skincare_result:description")],
                [InlineKeyboardButton(text="🛍️ Что купить", callback_data="skincare_result:products")],
                [InlineKeyboardButton(text="📄 Получить отчёт", callback_data="report:latest")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
            ]),
            parse_mode="Markdown"
        )
        # Генерируем визуальную карточку
        try:
            from report.cards import generate_visual_cards
            print("🎨 Generating visual card for skincare test...")
            recommendations = []  # Можно добавить реальные рекомендации
            card_files = generate_visual_cards({"user_id": uid, "skin_type": skin_type, "concerns": concerns}, recommendations)
            print(f"✅ Visual card generated: {card_files}")

            # Отправляем карточку в чат
            if card_files and len(card_files) > 0:
                card_path = card_files[0]  # Берем первый файл из списка
                if os.path.exists(card_path):
                    print(f"📤 Sending card to user: {card_path}")

                    # Отправляем как текстовое сообщение с путем к файлу
                    await cb.message.answer(
                        f"🎨 Ваша визуальная карточка создана!\n📁 Файл: {os.path.basename(card_path)}",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back:main")]
                        ])
                    )
                print("✅ Card sent successfully")
            else:
                print("⚠️ No visual card file found to send")

        except Exception as e:
            print(f"❌ Error generating/sending visual card: {e}")
            import traceback
            traceback.print_exc()

        # Analytics: Track test completion
        if ANALYTICS_AVAILABLE:
            user_id = cb.from_user.id if cb.from_user else 0
            analytics = get_analytics_tracker()
            if analytics:
                test_start_time = data.get("test_start_time")
                duration = None
                if test_start_time:
                    import time
                    duration = time.time() - test_start_time
                analytics.user_completed_test(user_id, "skin", duration)

        await cb.answer("🎊 Диагностика завершена!")
        
    except Exception as e:
        import traceback
        print(f"❌ Error in q8_desired_effect: {e}")
        print(f"📍 Traceback: {traceback.format_exc()}")
        try:
            await cb.answer("⚠️ Ошибка при обработке результата", show_alert=True)
        except:
            pass


# Result handlers
@router.callback_query(F.data == "skincare_result:description", DetailedSkincareFlow.RESULT)
async def show_skin_description(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать подробное описание типа лица"""
    try:
        data = await state.get_data()
        skin_analysis = data.get("skin_analysis", {})
        skin_type = skin_analysis.get("type", "normal")
        
        descriptions = {
            "dry": "🏜️ **СУХОЙ ТИП**\n\nВаше лицо испытывает недостаток липидов и влаги. Часто ощущается стянутость, особенно после умывания.\n\n**Характеристики:**\n• Ощущение стянутости и дискомфорта\n• Склонность к шелушению\n• Мелкие поры\n• Матовая текстура\n• Раннее появление мимических морщин\n\n**Особенности ухода:** Нужно мягкое очищение, интенсивное увлажнение и питание",
            
            "oily": "🛢️ **ЖИРНЫЙ ТИП**\n\nВаше лицо производит избыточное количество себума, что приводит к жирному блеску и расширенным порам.\n\n**Характеристики:**\n• Жирный блеск, особенно в Т-зоне\n• Расширенные поры\n• Склонность к высыпаниям\n• Плотная текстура\n• Медленное старение\n\n**Особенности ухода:** Нужно тщательное очищение, себорегуляция и легкое увлажнение",
            
            "combination": "⚖️ **КОМБИНИРОВАННЫЙ ТИП**\n\nВаше лицо сочетает признаки разных типов: жирная Т-зона и нормальная или сухая область на щеках.\n\n**Характеристики:**\n• Жирный блеск в Т-зоне\n• Нормальная или сухая область на щеках\n• Поры разного размера в разных зонах\n• Возможны высыпания в Т-зоне\n\n**Особенности ухода:** Нужен дифференцированный уход для разных зон лица",
            
            "normal": "✨ **НОРМАЛЬНЫЙ ТИП**\n\nВаше лицо находится в оптимальном балансе влаги и липидов, выглядит здоровым и ухоженным.\n\n**Характеристики:**\n• Комфортные ощущения в течение дня\n• Ровная текстура и цвет\n• Умеренный размер пор\n• Отсутствие жирного блеска\n• Хорошая эластичность\n\n**Особенности ухода:** Нужен поддерживающий уход для сохранения баланса"
        }
        
        await cb.message.edit_text(
            descriptions[skin_type],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад к результатам", callback_data="back:skincare_results")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
            ])
        )
        await cb.answer()
        
    except Exception as e:
        print(f"❌ Error in show_skin_description: {e}")
        await cb.answer("⚠️ Ошибка при показе описания")


@router.callback_query(F.data == "skincare_result:products", DetailedSkincareFlow.RESULT)
async def show_skincare_products(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать рекомендованные продукты для ухода с кнопками покупки"""
    try:
        data = await state.get_data()
        result = data.get("result", {})
        
        # Используем реальные продукты из системы рекомендаций
        from bot.ui.render import render_skincare_report
        
        if result and result.get("skincare"):
            # Analytics: Track recommendations viewed
            if ANALYTICS_AVAILABLE:
                user_id = cb.from_user.id if cb.from_user else 0
                analytics = get_analytics_tracker()
                if analytics:
                    skincare_products = result.get("skincare", {})
                    total_products = sum(len(products) for products in skincare_products.values() if products)
                    analytics.recommendations_viewed(user_id, "skincare", total_products)
            
            # Рендерим UI с продуктами с fallback
            try:
                from bot.ui.render import render_skincare_report
                text, kb = render_skincare_report(result)
                print("✅ Skincare report rendered successfully")
            except Exception as e:
                print(f"❌ Render failed: {e}")
                import traceback
                traceback.print_exc()

                # Fallback: краткий профиль и кнопки
                skin_analysis = data.get("skin_analysis", {})
                skin_type = skin_analysis.get("type", "normal")
                concerns = skin_analysis.get("concerns", [])

                skin_type_names = {
                    "dry": "🏜️ Сухой тип",
                    "oily": "🫧 Жирный тип",
                    "combination": "🔄 Комбинированный тип",
                    "normal": "✅ Нормальный тип"
                }

                concerns_text = ", ".join(concerns) if concerns else "общий уход"
                fallback_text = (
                    f"🧴 **Ваш тип кожи определён!**\n\n"
                    f"**Тип кожи:** {skin_type_names.get(skin_type, skin_type)}\n"
                    f"**Проблемы:** {concerns_text}\n\n"
                    f"🔍 **Рекомендуемые категории ухода:**\n"
                    f"• Очищающие средства\n"
                    f"• Тоники\n"
                    f"• Сыворотки\n"
                    f"• Кремы\n"
                    f"• Солнцезащита\n\n"
                    f"Нажмите на категории ниже для подбора средств:"
                )

                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🧼 Очищение", callback_data="show_skincare_category:cleanser")],
                    [InlineKeyboardButton(text="💧 Тоник", callback_data="show_skincare_category:toner")],
                    [InlineKeyboardButton(text="🧪 Сыворотка", callback_data="show_skincare_category:serum")],
                    [InlineKeyboardButton(text="🧴 Крем", callback_data="show_skincare_category:moisturizer")],
                    [InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")]
                ])
                text = fallback_text
            
            # Добавляем кнопку возврата
            buttons = kb.inline_keyboard if kb else []
            buttons.append([InlineKeyboardButton(text="⬅️ Назад к результатам", callback_data="back:skincare_results")])
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await cb.message.edit_text(
                f"🛍️ **ЧТО КУПИТЬ**\n\n{text}",
                reply_markup=kb
            )
        else:
            # Fallback если нет продуктов
            skin_analysis = data.get("skin_analysis", {})
            skin_type = skin_analysis.get("type", "normal")
            
            skin_type_names = {
                "dry": "🏜️ сухого типа",
                "oily": "🛢️ жирного типа",
                "combination": "⚖️ комбинированного типа",
                "normal": "✨ нормального типа"
            }
            
            await cb.message.edit_text(
                f"🧴 **ПРОДУКТЫ ДЛЯ {skin_type_names[skin_type].upper()}**\n\n"
                f"К сожалению, в данный момент подходящие продукты недоступны в каталоге.\n\n"
                f"Попробуйте позже или обратитесь к консультанту.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад к результатам", callback_data="back:skincare_results")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
                ])
            )
        
        await cb.answer()
        
    except Exception as e:
        print(f"❌ Error in show_skincare_products: {e}")
        await cb.answer("⚠️ Ошибка при показе продуктов")


@router.callback_query(F.data == "skincare_result:products")
async def show_skincare_products_universal(cb: CallbackQuery, state: FSMContext) -> None:
    """Универсальный обработчик для показа продуктов ухода"""
    try:
        print(f"🛍️ skincare_result:products callback from user {cb.from_user.id}")

        # Пытаемся получить данные из состояния
        data = await state.get_data()
        result = data.get("result", {})

        if not result or not result.get("skincare"):
            # Если нет данных в состоянии, пытаемся получить из сохраненного профиля
            user_id = cb.from_user.id
            from bot.handlers.user_profile_store import get_user_profile_store
            profile_store = get_user_profile_store()
            profile = profile_store.load_profile(user_id)

            if profile:
                # Создаем результат на основе профиля
                result = {
                    "skincare": {
                        "cleanser": [{"id": "fallback_cleanser", "brand": "Рекомендуемый", "name": "Средство для очищения", "price": 1500}],
                        "toner": [{"id": "fallback_toner", "brand": "Рекомендуемый", "name": "Тоник", "price": 1200}],
                        "serum": [{"id": "fallback_serum", "brand": "Рекомендуемый", "name": "Сыворотка", "price": 2500}],
                        "moisturizer": [{"id": "fallback_moisturizer", "brand": "Рекомендуемый", "name": "Увлажняющий крем", "price": 1800}]
                    }
                }
            else:
                await cb.answer("⚠️ Профиль не найден. Пожалуйста, пройдите тест заново.")
                return

        # Используем реальные продукты из системы рекомендаций
        from bot.ui.render import render_skincare_report

        text, kb = render_skincare_report(result)

        # Добавляем кнопку возврата
        buttons = kb.inline_keyboard if kb else []
        buttons.append([InlineKeyboardButton(text="⬅️ Назад к результатам", callback_data="back:skincare_results")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await cb.message.edit_text(
            f"🛍️ **ЧТО КУПИТЬ**\n\n{text}",
            reply_markup=kb,
            parse_mode="Markdown"
        )

        # Analytics
        if ANALYTICS_AVAILABLE:
            user_id = cb.from_user.id if cb.from_user else 0
            analytics = get_analytics_tracker()
            if analytics and result.get("skincare"):
                skincare_products = result.get("skincare", {})
                total_products = sum(len(products) for products in skincare_products.values() if products)
                analytics.recommendations_viewed(user_id, "skincare", total_products)

        await cb.answer()

    except Exception as e:
        print(f"❌ Error in show_skincare_products_universal: {e}")
        await cb.answer("⚠️ Ошибка при показе рекомендаций")


@router.callback_query(F.data == "back:skincare_results", DetailedSkincareFlow.RESULT)
async def back_to_skincare_results(cb: CallbackQuery, state: FSMContext) -> None:
    """Вернуться к результатам диагностики лица"""
    try:
        data = await state.get_data()
        skin_analysis = data.get("skin_analysis", {})
        skin_type = skin_analysis.get("type", "normal")
        tldr_report = data.get("tldr_report", "")
        
        skin_type_names = {
            "dry": "🏜️ Сухой тип",
            "oily": "🛢️ Жирный тип", 
            "combination": "⚖️ Комбинированный тип",
            "normal": "✨ Нормальный тип"
        }
        
        concerns = skin_analysis.get("concerns", [])
        sensitivity = skin_analysis.get("sensitivity", "normal")
        
        # Формируем описание состояния
        concerns_text = ""
        if concerns:
            concerns_readable = {
                "dehydration": "обезвоженность",
                "pigmentation": "пигментация", 
                "acne": "акне",
                "enlarged_pores": "расширенные поры",
                "aging": "возрастные изменения",
                "couperose": "купероз",
                "redness": "покраснения",
                "puffiness": "отечность",
                "dark_circles": "темные круги",
                "seasonal_changes": "сезонные изменения",
                "hydration_needed": "нужно увлажнение"
            }
            concerns_list = [concerns_readable.get(c, c) for c in concerns[:3]]
            concerns_text = f"\n**Основные проблемы:** {', '.join(concerns_list)}"
            
        sensitivity_text = ""
        if sensitivity != "normal":
            sensitivity_names = {
                "sensitive": "чувствительная",
                "very_sensitive": "очень чувствительная"
            }
            sensitivity_text = f"\n**Чувствительность:** {sensitivity_names[sensitivity]}"
        
        # Показываем краткий анализ если он есть
        analysis_text = f"\n\n📊 **Краткий анализ:**\n{tldr_report}" if tldr_report else ""
        
        await cb.message.edit_text(
            f"🎉 **РЕЗУЛЬТАТ ДИАГНОСТИКИ**\n\n"
            f"**Ваш тип лица:** {skin_type_names[skin_type]}{concerns_text}{sensitivity_text}{analysis_text}\n\n"
            f"Что вы хотите увидеть?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ℹ️ Полное описание типа лица", callback_data="skincare_result:description")],
                [InlineKeyboardButton(text="🛍️ Подобрать уход", callback_data="skincare_result:products")],
                [InlineKeyboardButton(text="📄 Получить отчёт", callback_data="report:latest")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
            ])
        )
        await cb.answer()
        
    except Exception as e:
        print(f"❌ Error in back_to_skincare_results: {e}")
        await cb.answer("⚠️ Ошибка при возврате")
