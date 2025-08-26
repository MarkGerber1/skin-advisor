"""
Подробный тест на цветотип внешности (8 вопросов)
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
from engine.models import UserProfile, Season, Undertone, ReportData
from engine.selector import SelectorV2
from engine.answer_expander import AnswerExpanderV2
from bot.ui.keyboards import add_home_button

router = Router()

class DetailedPaletteFlow(StatesGroup):
    # 8 детальных вопросов для определения цветотипа
    Q1_HAIR_COLOR = State()      # Естественный цвет волос
    Q2_EYE_COLOR = State()       # Оттенок глаз 
    Q3_SKIN_UNDERTONE = State()  # Подтон кожи (вены на запястье)
    Q4_CONTRAST = State()        # Контраст между волосами, глазами и кожей
    Q5_SUN_REACTION = State()    # Реакция кожи на солнце
    Q6_FACE_SHAPE = State()      # Форма лица (для бронзатора/скульптора)
    Q7_MAKEUP_STYLE = State()    # Предпочтения в макияже
    Q8_LIP_COLOR = State()       # Естественный цвет губ
    RESULT = State()             # Результат теста


def _kb_hair_color() -> InlineKeyboardMarkup:
    """Q1: Естественный цвет волос (без окрашивания)"""
    buttons = [
        [InlineKeyboardButton(text="a) Светлые с золотистым отливом (пшеничные, медовые)", callback_data="hair:a")],
        [InlineKeyboardButton(text="b) Пепельные, русые с холодным подтоном", callback_data="hair:b")],
        [InlineKeyboardButton(text="c) Теплые каштановые, рыжие, медные", callback_data="hair:c")],
        [InlineKeyboardButton(text="d) Темные с синеватым отливом или платиновый блонд", callback_data="hair:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_eye_color() -> InlineKeyboardMarkup:
    """Q2: Оттенок глаз"""
    buttons = [
        [InlineKeyboardButton(text="a) Голубые (сапфиры), светло-зеленые (аквамарины)", callback_data="eyes:a")],
        [InlineKeyboardButton(text="b) Серо-голубые, светло-карие", callback_data="eyes:b")],
        [InlineKeyboardButton(text="c) Карие (терракота), болотные, янтарные", callback_data="eyes:c")],
        [InlineKeyboardButton(text="d) Ярко-синие, изумрудные, темно-карие", callback_data="eyes:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_skin_undertone() -> InlineKeyboardMarkup:
    """Q3: Подтон кожи (посмотрите на вены на запястье в дневном свете)"""
    buttons = [
        [InlineKeyboardButton(text="a) Теплый (зеленоватые вены) — золотистые/персиковые оттенки", callback_data="undertone:a")],
        [InlineKeyboardButton(text="b) Холодный (синие вены) — розовые/голубоватые оттенки", callback_data="undertone:b")],
        [InlineKeyboardButton(text="c) Нейтральный (смешанные вены)", callback_data="undertone:c")],
        [InlineKeyboardButton(text="d) Сложно определить", callback_data="undertone:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_contrast() -> InlineKeyboardMarkup:
    """Q4: Контраст между цветом волос, глаз и кожи"""
    buttons = [
        [InlineKeyboardButton(text="a) Низкий контраст (все оттенки близки по яркости)", callback_data="contrast:a")],
        [InlineKeyboardButton(text="b) Средний контраст", callback_data="contrast:b")],
        [InlineKeyboardButton(text="c) Высокий контраст (яркие глаза на светлой коже или темные волосы с светлыми глазами)", callback_data="contrast:c")],
        [InlineKeyboardButton(text="d) Очень высокий контраст", callback_data="contrast:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_sun_reaction() -> InlineKeyboardMarkup:
    """Q5: Как выглядит ваша кожа после пребывания на солнце?"""
    buttons = [
        [InlineKeyboardButton(text="a) Быстро загорает, редко обгорает", callback_data="sun:a")],
        [InlineKeyboardButton(text="b) Загорает с трудом, часто обгорает", callback_data="sun:b")],
        [InlineKeyboardButton(text="c) Мгновенно обгорает, не загорает", callback_data="sun:c")],
        [InlineKeyboardButton(text="d) Равномерно загорает без проблем", callback_data="sun:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_face_shape() -> InlineKeyboardMarkup:
    """Q6: Какая форма лица у вас преобладает? (для точного подбора бронзатора и скульптора)"""
    buttons = [
        [InlineKeyboardButton(text="a) Овальное", callback_data="face:a")],
        [InlineKeyboardButton(text="b) Круглое", callback_data="face:b")],
        [InlineKeyboardButton(text="c) Квадратное", callback_data="face:c")],
        [InlineKeyboardButton(text="d) Сердцевидное", callback_data="face:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_makeup_style() -> InlineKeyboardMarkup:
    """Q7: Какой эффект вы предпочитаете в макияже?"""
    buttons = [
        [InlineKeyboardButton(text="a) Естественный, \"нулевой\"", callback_data="style:a")],
        [InlineKeyboardButton(text="b) Свежий дневной", callback_data="style:b")],
        [InlineKeyboardButton(text="c) Яркий вечерний", callback_data="style:c")],
        [InlineKeyboardButton(text="d) Профессиональный сценический", callback_data="style:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def _kb_lip_color() -> InlineKeyboardMarkup:
    """Q8: Какой цвет губ у вас естественный?"""
    buttons = [
        [InlineKeyboardButton(text="a) Теплый розовый/персиковый", callback_data="lips:a")],
        [InlineKeyboardButton(text="b) Холодный розовый/фиолетовый", callback_data="lips:b")],
        [InlineKeyboardButton(text="c) Нейтральный бежевый", callback_data="lips:c")],
        [InlineKeyboardButton(text="d) Ярко-коричневый", callback_data="lips:d")]
    ]
    return add_home_button(InlineKeyboardMarkup(inline_keyboard=buttons))


def determine_season(answers: Dict[str, str]) -> str:
    """
    Определение цветотипа на основе ответов из файла:
    • Весна – преобладают ответы «а».
    • Лето – преобладают «b».
    • Осень – преобладают «c».
    • Зима – преобладают «d».
    """
    scores = {"spring": 0, "summer": 0, "autumn": 0, "winter": 0}
    
    # Подсчитываем каждый ответ согласно файлу
    for answer_key, answer_value in answers.items():
        if answer_value == "a":
            scores["spring"] += 1
        elif answer_value == "b":
            scores["summer"] += 1
        elif answer_value == "c":
            scores["autumn"] += 1
        elif answer_value == "d":
            scores["winter"] += 1
    
    # Определяем победителя
    max_score = max(scores.values())
    winners = [season for season, score in scores.items() if score == max_score]
    
    if len(winners) == 1:
        return winners[0]
    
    # При ничьей используем приоритет: Winter > Autumn > Spring > Summer
    # (основано на контрастности цветотипов)
    if "winter" in winners:
        return "winter"
    elif "autumn" in winners:
        return "autumn"
    elif "spring" in winners:
        return "spring"
    else:
        return "summer"


async def start_detailed_palette_flow(message: Message, state: FSMContext) -> None:
    """Запуск детального теста на цветотип"""
    print(f"🎨 Starting detailed palette flow for user {message.from_user.id if message.from_user else 'Unknown'}")
    await state.clear()
    await state.set_state(DetailedPaletteFlow.Q1_HAIR_COLOR)
    print(f"✅ Set state to Q1_HAIR_COLOR")
    
    await message.answer(
        "🎨 **ПРОФЕССИОНАЛЬНЫЙ ТЕСТ НА ЦВЕТОТИП**\n\n"
        "Ответьте честно на 8 вопросов, чтобы определить ваш цветотип "
        "и получить персональные рекомендации по декоративной косметике.\n\n"
        "**Вопрос 1 из 8**\n"
        "🌈 Какой у вас естественный цвет волос (без окрашивания)?",
        reply_markup=_kb_hair_color()
    )


# Handlers for each question
@router.callback_query(F.data.startswith("hair:"), DetailedPaletteFlow.Q1_HAIR_COLOR)
async def q1_hair_color(cb: CallbackQuery, state: FSMContext) -> None:
    print(f"🎯 q1_hair_color called! data={cb.data}, user={cb.from_user.id if cb.from_user else 'Unknown'}")
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        print(f"💡 Processing hair color answer: {answer}")
        await state.update_data(hair=answer)
        await state.set_state(DetailedPaletteFlow.Q2_EYE_COLOR)
        
        await cb.message.edit_text(
            "**Вопрос 2 из 8**\n"
            "👁️ Какой оттенок у ваших глаз?",
            reply_markup=_kb_eye_color()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q1_hair_color: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("eyes:"), DetailedPaletteFlow.Q2_EYE_COLOR)
async def q2_eye_color(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(eyes=answer)
        await state.set_state(DetailedPaletteFlow.Q3_SKIN_UNDERTONE)
        
        await cb.message.edit_text(
            "**Вопрос 3 из 8**\n"
            "🔍 Какой у вас подтон кожи?\n\n"
            "*Посмотрите на вены на запястье в дневном свете:*",
            reply_markup=_kb_skin_undertone()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q2_eye_color: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("undertone:"), DetailedPaletteFlow.Q3_SKIN_UNDERTONE)
async def q3_skin_undertone(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(undertone=answer)
        await state.set_state(DetailedPaletteFlow.Q4_CONTRAST)
        
        await cb.message.edit_text(
            "**Вопрос 4 из 8**\n"
            "⚖️ Какой контраст между цветом волос, глаз и кожи?",
            reply_markup=_kb_contrast()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q3_skin_undertone: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("contrast:"), DetailedPaletteFlow.Q4_CONTRAST)
async def q4_contrast(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(contrast=answer)
        await state.set_state(DetailedPaletteFlow.Q5_SUN_REACTION)
        
        await cb.message.edit_text(
            "**Вопрос 5 из 8**\n"
            "☀️ Как выглядит ваша кожа после пребывания на солнце?",
            reply_markup=_kb_sun_reaction()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q4_contrast: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("sun:"), DetailedPaletteFlow.Q5_SUN_REACTION)
async def q5_sun_reaction(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(sun=answer)
        await state.set_state(DetailedPaletteFlow.Q6_FACE_SHAPE)
        
        await cb.message.edit_text(
            "**Вопрос 6 из 8**\n"
            "👤 Какая форма лица у вас преобладает?\n\n"
            "*Это поможет точно подобрать бронзатор и скульптор:*",
            reply_markup=_kb_face_shape()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q5_sun_reaction: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("face:"), DetailedPaletteFlow.Q6_FACE_SHAPE)
async def q6_face_shape(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(face_shape=answer)
        await state.set_state(DetailedPaletteFlow.Q7_MAKEUP_STYLE)
        
        await cb.message.edit_text(
            "**Вопрос 7 из 8**\n"
            "💄 Какой эффект вы предпочитаете в макияже?",
            reply_markup=_kb_makeup_style()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q6_face_shape: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("style:"), DetailedPaletteFlow.Q7_MAKEUP_STYLE)
async def q7_makeup_style(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(makeup_style=answer)
        await state.set_state(DetailedPaletteFlow.Q8_LIP_COLOR)
        
        await cb.message.edit_text(
            "**Вопрос 8 из 8**\n"
            "💋 Какой цвет губ у вас естественный?",
            reply_markup=_kb_lip_color()
        )
        await cb.answer()
    except Exception as e:
        print(f"❌ Error in q7_makeup_style: {e}")
        await cb.answer("⚠️ Ошибка, попробуйте снова")


@router.callback_query(F.data.startswith("lips:"), DetailedPaletteFlow.Q8_LIP_COLOR)
async def q8_lip_color(cb: CallbackQuery, state: FSMContext) -> None:
    try:
        print("🎨 Starting q8_lip_color handler...")
        answer = cb.data.split(":")[1]  # a, b, c, d
        await state.update_data(lips=answer)
        await state.set_state(DetailedPaletteFlow.RESULT)
        
        # Анализируем результаты
        data = await state.get_data()
        print(f"🔍 Test data: {data}")
        season = determine_season(data)
        print(f"🌸 Determined season: {season}")
        
        # Получаем uid пользователя
        uid = int(cb.from_user.id) if cb.from_user and cb.from_user.id else 0
        print(f"👤 User ID: {uid}")
        
        # Создаем UserProfile для системы рекомендаций
        print("📦 Importing modules...")
        from engine.models import UserProfile, Season, Undertone
        from engine.selector import SelectorV2
        from engine.catalog_store import CatalogStore
        from engine.answer_expander import AnswerExpanderV2
        from engine.models import ReportData
        from bot.ui.pdf import save_last_json, save_text_pdf
        from bot.ui.render import render_makeup_report
        import os
        
        # Определяем цветотип для Engine
        print("🗺️ Mapping season...")
        season_mapping = {
            "spring": Season.SPRING,
            "summer": Season.SUMMER,
            "autumn": Season.AUTUMN,
            "winter": Season.WINTER
        }
        
        # Определяем подтон на основе ответов
        print("🎨 Processing undertone...")
        undertone_answer = data.get("undertone", "")
        if undertone_answer == "a":  # Теплый
            undertone = Undertone.WARM
        elif undertone_answer == "b":  # Холодный
            undertone = Undertone.COOL
        else:  # Нейтральный или сложно определить
            undertone = Undertone.NEUTRAL
        print(f"💄 Undertone: {undertone}")
        
        # Конвертируем цвет глаз из ответов теста в enum
        print("👁️ Processing eye color...")
        from engine.models import EyeColor
        eye_answer = data.get("eyes", "")
        eye_color_mapping = {
            "a": EyeColor.BLUE,    # Голубые, светло-зеленые
            "b": EyeColor.GRAY,    # Серо-голубые, светло-карие  
            "c": EyeColor.BROWN,   # Темные оттенки
            "d": EyeColor.BLUE     # Ярко-синие, изумрудные, темно-карие
        }
        eye_color = eye_color_mapping.get(eye_answer, EyeColor.BROWN)
        print(f"👁️ Eye color: {eye_color}")
        
        print("👤 Creating UserProfile...")
        profile = UserProfile(
            user_id=uid,  # Добавлено обязательное поле
            season=season_mapping[season],
            undertone=undertone,
            age=25,  # Примерный возраст
            hair_color=data.get("hair", ""),
            eye_color=eye_color,  # Используем enum
            face_shape=data.get("face_shape", ""),
            makeup_style=data.get("makeup_style", ""),
            lip_color=data.get("lips", "")
        )
        print("✅ UserProfile created successfully!")
        
        # Получаем каталог продуктов
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()
        print(f"📚 Catalog loaded: {len(catalog) if catalog else 0} products total")
        if catalog:
            makeup_categories = set()
            for product in catalog:
                if hasattr(product, 'category'):
                    makeup_categories.add(product.category)
            print(f"🎨 Available product categories: {sorted(makeup_categories)}")
        else:
            print("❌ No catalog loaded!")
        
        # Генерируем рекомендации через SelectorV2
        print(f"🔧 Profile: season={profile.season}, undertone={profile.undertone}, age={profile.age}")
        selector = SelectorV2()
        # Детальная диагностика каталога
        print(f"📊 Catalog products: {len(catalog) if catalog else 0}")
        if catalog:
            cat_stats = {}
            for prod in catalog:
                cat = getattr(prod, 'category', 'Unknown')
                cat_stats[cat] = cat_stats.get(cat, 0) + 1
            print(f"📈 Category stats: {cat_stats}")
        
        result = selector.select_products_v2(
            profile=profile,
            catalog=catalog,
            partner_code="S1",
            redirect_base="https://skin-advisor.example.com"
        )
        print(f"🛍️ Selector result keys: {list(result.keys()) if result else 'No result'}")
        
        # Детальный анализ результата макияжа
        if result and result.get("makeup"):
            makeup = result["makeup"]
            print(f"💄 Makeup categories in result: {list(makeup.keys())}")
            
            # CRITICAL: Show which categories have products vs which are empty
            print("📊 MAKEUP PRODUCTS BREAKDOWN:")
            total_makeup_products = 0
            populated_categories = []
            empty_categories = []
            
            for cat, products in makeup.items():
                count = len(products) if products else 0
                total_makeup_products += count
                if count > 0:
                    populated_categories.append(f"{cat}({count})")
                    print(f"  ✅ {cat}: {count} products")
                    for prod in products[:1]:  # Show 1 example
                        print(f"    📦 Example: {prod.get('name', 'No name')}")
                else:
                    empty_categories.append(cat)
                    print(f"  ❌ {cat}: EMPTY")
            
            print(f"💄 Total makeup products found: {total_makeup_products}")
            print(f"✅ POPULATED: {populated_categories}")
            print(f"❌ EMPTY: {empty_categories}")
        else:
            print("❌ No makeup products in result")
        
        # Извлекаем макияж продукты для отчета
        makeup_products = []
        makeup_data = result.get("makeup", {})
        for category_products in makeup_data.values():
            if isinstance(category_products, list):
                makeup_products.extend(category_products[:2])  # Первые 2 из каждой категории
        
        # Генерируем отчет
        report_data = ReportData(
            user_profile=profile,
            skincare_products=[],
            makeup_products=makeup_products
        )
        
        expander = AnswerExpanderV2()
        tldr_report = expander.generate_tldr_report(report_data)
        full_report = expander.generate_full_report(report_data)
        
        # Рендерим UI с продуктами
        text, kb = render_makeup_report(result)
        
        # Сохраняем результат для пользователя
        if uid:
            snapshot = {
                "type": "detailed_palette",
                "profile": profile.model_dump(),
                "result": result,
                "tl_dr": tldr_report,
                "full_text": full_report,
                "answers": data
            }
            save_last_json(uid, snapshot)
            save_text_pdf(uid, title="🎨 Отчёт по цветотипу", body_text=full_report)
        
        # Сохраняем результат в состояние
        await state.update_data(
            season=season,
            profile=profile.model_dump(),
            result=result,
            makeup_products=makeup_products,
            tldr_report=tldr_report,
            full_report=full_report
        )
        print(f"💾 Saved to state: season={season}, result_keys={list(result.keys()) if result else 'No result'}")
        print(f"📝 Reports: tldr={len(tldr_report)} chars, full={len(full_report)} chars")
        
        # Показываем результат с продуктами
        season_names = {
            "spring": "🌸 Яркая Весна",
            "summer": "🌊 Мягкое Лето", 
            "autumn": "🍂 Глубокая Осень",
            "winter": "❄️ Холодная Зима"
        }
        
        print(f"🎭 About to show result buttons with state: {await state.get_state()}")
        await cb.message.edit_text(
            f"🎉 **РЕЗУЛЬТАТ ТЕСТА**\n\n"
            f"**Ваш цветотип:** {season_names[season]}\n\n"
            f"📊 **Краткий анализ:**\n{tldr_report}\n\n"
            f"Что вы хотите увидеть?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ℹ️ Полное описание цветотипа", callback_data="result:description")],
                [InlineKeyboardButton(text="💄 Рекомендуемые продукты", callback_data="result:products")],
                [InlineKeyboardButton(text="📄 Получить отчёт", callback_data="report:latest")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
            ])
        )
        print(f"✅ Result buttons displayed for state: {await state.get_state()}")
        await cb.answer("🎊 Тест завершен!")
        
    except Exception as e:
        import traceback
        print(f"❌ Error in q8_lip_color: {e}")
        print(f"📍 Traceback: {traceback.format_exc()}")
        try:
            await cb.answer("⚠️ Ошибка при обработке результата", show_alert=True)
        except:
            pass


# Result handlers
@router.callback_query(F.data == "result:description", DetailedPaletteFlow.RESULT)
async def show_description(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать подробное описание цветотипа"""
    try:
        print(f"🔥 result:description called by user {cb.from_user.id if cb.from_user else 'Unknown'}")
        data = await state.get_data()
        print(f"🔍 State data keys: {list(data.keys())}")
        season = data.get("season", "spring")
        print(f"🌸 Season from state: {season}")
        
        descriptions = {
            "spring": "🌸 **ЯРКАЯ ВЕСНА**\n\nВы обладатель теплого цветотипа с золотистым подтоном кожи. Ваши волосы имеют медовые или пшеничные оттенки, а глаза яркие и чистые.\n\n**Ваши особенности:**\n• Кожа с персиковым или золотистым подтоном\n• Волосы теплых светлых оттенков\n• Яркие, чистые глаза\n• Средний контраст внешности\n\n**Украшения:** Золото подчеркивает вашу естественную красоту",
            
            "summer": "🌊 **МЯГКОЕ ЛЕТО**\n\nВы представитель холодного цветотипа с розовым подтоном кожи. Ваша внешность характеризуется мягкими, приглушенными тонами.\n\n**Ваши особенности:**\n• Кожа с розовым или голубоватым подтоном\n• Волосы пепельных оттенков\n• Мягкие, приглушенные цвета глаз\n• Низкий или средний контраст\n\n**Украшения:** Серебро и платина идеально вам подходят",
            
            "autumn": "🍂 **ГЛУБОКАЯ ОСЕНЬ**\n\nВы обладатель теплого цветотипа с насыщенными, глубокими красками. Ваша внешность отличается богатством и теплотой.\n\n**Ваши особенности:**\n• Кожа с золотистым или оливковым подтоном\n• Волосы глубоких теплых оттенков\n• Насыщенные карие или зеленые глаза\n• Средний или высокий контраст\n\n**Украшения:** Золото, медь и бронза - ваши металлы",
            
            "winter": "❄️ **ХОЛОДНАЯ ЗИМА**\n\nВы представитель холодного цветотипа с высоким контрастом. Ваша внешность поражает яркостью и четкостью линий.\n\n**Ваши особенности:**\n• Кожа с розовым или оливковым подтоном\n• Темные или очень светлые волосы\n• Яркие, контрастные глаза\n• Высокий контраст внешности\n\n**Украшения:** Серебро, платина и белое золото"
        }
        
        await cb.message.edit_text(
            descriptions[season],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад к результатам", callback_data="back:results")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
            ])
        )
        await cb.answer()
        
    except Exception as e:
        print(f"❌ Error in show_description: {e}")
        await cb.answer("⚠️ Ошибка при показе описания")


@router.callback_query(F.data == "result:products", DetailedPaletteFlow.RESULT)
async def show_products(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать рекомендованные продукты с кнопками покупки"""
    try:
        print(f"🛍️ result:products called by user {cb.from_user.id if cb.from_user else 'Unknown'}")
        data = await state.get_data()
        print(f"🔍 State data keys: {list(data.keys())}")
        result = data.get("result", {})
        print(f"🎯 Product result keys: {list(result.keys()) if result else 'No result'}")
        
        # Используем реальные продукты из системы рекомендаций
        from bot.ui.render import render_makeup_report
        
        if result and result.get("makeup"):
            print("🎨 Found makeup in result, calling render_makeup_report")
            text, kb = render_makeup_report(result)
            print(f"📝 Rendered text length: {len(text)}, buttons: {len(kb.inline_keyboard) if kb else 0}")
            
            # Добавляем кнопку возврата
            buttons = kb.inline_keyboard if kb else []
            buttons.append([InlineKeyboardButton(text="⬅️ Назад к результатам", callback_data="back:results")])
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await cb.message.edit_text(
                f"💄 **РЕКОМЕНДОВАННЫЕ ПРОДУКТЫ**\n\n{text}",
                reply_markup=kb
            )
            print("✅ Products displayed successfully")
        else:
            # Fallback если нет продуктов
            print("⚠️ No makeup found in result, showing fallback")
            season = data.get("season", "spring")
            season_names = {
                "spring": "🌸 Яркой Весны",
                "summer": "🌊 Мягкого Лета", 
                "autumn": "🍂 Глубокой Осени",
                "winter": "❄️ Холодной Зимы"
            }
            
            await cb.message.edit_text(
                f"💄 **ПРОДУКТЫ ДЛЯ {season_names[season].upper()}**\n\n"
                f"К сожалению, в данный момент подходящие продукты недоступны в каталоге.\n\n"
                f"Попробуйте позже или обратитесь к консультанту.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад к результатам", callback_data="back:results")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
                ])
            )
        
        await cb.answer()
        
    except Exception as e:
        print(f"❌ Error in show_products: {e}")
        await cb.answer("⚠️ Ошибка при показе продуктов")


@router.callback_query(F.data == "back:results", DetailedPaletteFlow.RESULT)
async def back_to_results(cb: CallbackQuery, state: FSMContext) -> None:
    """Вернуться к результатам теста"""
    try:
        print(f"🔙 back:results called by user {cb.from_user.id if cb.from_user else 'Unknown'}")
        data = await state.get_data()
        season = data.get("season", "spring")
        tldr_report = data.get("tldr_report", "")
        print(f"🌸 Returning to results for season: {season}")
        
        season_names = {
            "spring": "🌸 Яркая Весна",
            "summer": "🌊 Мягкое Лето", 
            "autumn": "🍂 Глубокая Осень",
            "winter": "❄️ Холодная Зима"
        }
        
        # Показываем краткий анализ если он есть
        analysis_text = f"\n\n📊 **Краткий анализ:**\n{tldr_report}" if tldr_report else ""
        
        await cb.message.edit_text(
            f"🎉 **РЕЗУЛЬТАТ ТЕСТА**\n\n"
            f"**Ваш цветотип:** {season_names[season]}{analysis_text}\n\n"
            f"Что вы хотите увидеть?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ℹ️ Полное описание цветотипа", callback_data="result:description")],
                [InlineKeyboardButton(text="💄 Рекомендуемые продукты", callback_data="result:products")],
                [InlineKeyboardButton(text="📄 Получить отчёт", callback_data="report:latest")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="universal:home")]
            ])
        )
        await cb.answer("🔙 Возврат к результатам")
        print("✅ Back to results displayed successfully")
        
    except Exception as e:
        print(f"❌ Error in back_to_results: {e}")
        await cb.answer("⚠️ Ошибка при возврате")
