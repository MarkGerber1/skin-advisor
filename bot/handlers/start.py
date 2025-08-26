from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.ui.keyboards import (
    main_menu,
    BTN_PALETTE,
    BTN_SKINCARE,
    BTN_ABOUT,
    BTN_PICK,
    BTN_SETTINGS,
    BTN_REPORT,
)


router = Router()


@router.message(CommandStart())
async def on_start(m: Message, state: FSMContext) -> None:
    await state.clear()
    await m.answer(
        "Привет! ✨ Я подберу персональный уход и идеальные оттенки макияжа по вашему профилю.\n\n"
        "Выберите режим:",
        reply_markup=main_menu(),
    )


@router.message(F.text == BTN_SKINCARE)
async def start_skincare(m: Message, state: FSMContext) -> None:
    """Start skincare test - works from ANY state"""
    print(f"🧴 Skincare button pressed by user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()  # Clear any existing state
    
    from .detailed_skincare import start_detailed_skincare_flow
    await start_detailed_skincare_flow(m, state)


@router.message(F.text == BTN_PALETTE)
async def start_palette(m: Message, state: FSMContext) -> None:
    """Start palette test - works from ANY state"""
    print(f"🎨 Palette button pressed by user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()  # Clear any existing state
    
    from .detailed_palette import start_detailed_palette_flow
    await start_detailed_palette_flow(m, state)


@router.message(F.text == BTN_ABOUT)
async def about(m: Message, state: FSMContext) -> None:
    """Show about info - works from ANY state"""
    print(f"ℹ️ About button pressed by user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()
    await m.answer(
        "🤖 О боте:\n\n"
        "Я - ваш персональный косметолог! ✨\n\n"
        "🔹 Анализ типа кожи и проблем\n"
        "🔹 Определение цветовой палитры (undertone)\n"
        "🔹 Персональные рекомендации по уходу и макияжу\n"
        "🔹 Прямые ссылки на проверенные продукты\n\n"
        "💡 Пройдите диагностику и получите персонализированный отчет!",
        reply_markup=main_menu(),
    )


@router.message(F.text == BTN_PICK)
async def my_picks(m: Message, state: FSMContext) -> None:
    """Show user picks - works from ANY state"""
    print(f"🛒 Picks button pressed by user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()
    
    # Проверяем, есть ли сохраненные отчеты пользователя
    from bot.ui.pdf import load_last_report_json
    
    uid = int(m.from_user.id) if m.from_user and m.from_user.id else 0
    if uid:
        report_data = load_last_report_json(uid)
        if report_data:
            # Пользователь прошел тест, показываем корзину
            from bot.handlers.cart import show_cart
            await show_cart(m, state)
            return
    
    # Если нет данных, показываем приглашение пройти тест
    await m.answer(
        "🛒 Моя подборка\n\n"
        "Здесь будут отображаться ваши сохраненные продукты.\n"
        "Сначала пройдите диагностику кожи или определение палитры!",
        reply_markup=main_menu(),
    )


@router.message(F.text == BTN_SETTINGS)
async def settings(m: Message, state: FSMContext) -> None:
    """Show settings - works from ANY state"""
    print(f"⚙️ Settings button pressed by user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()
    await m.answer(
        "⚙️ Настройки\n\n"
        "Настройки бота:\n"
        "• Язык: Русский 🇷🇺\n"
        "• Уведомления: Включены 🔔\n"
        "• Темная тема: Авто 🌙\n\n"
        "Функция в разработке...",
        reply_markup=main_menu(),
    )


@router.message(F.text == BTN_REPORT)
async def report_latest(m: Message, state: FSMContext) -> None:
    """Show latest report - works from ANY state"""
    print(f"📊 Report button pressed by user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()
    from aiogram.types import CallbackQuery

    # Имитация нажатия кнопки для переиспользования логики report:latest
    class _FakeCb(CallbackQuery):
        pass

    # Вызовем хендлер отправки отчёта напрямую
    from bot.handlers.report import send_latest_report

    cb = _FakeCb(id="0", from_user=m.from_user, chat_instance="0", data="report:latest", message=m)
    try:
        await send_latest_report(cb)
    except Exception:
        await m.answer("Отчёт ещё не сформирован. Пройдите диагностику или палитрометр.")


# ========================================
# CALLBACK HANDLERS FOR INLINE BUTTONS
# ========================================

@router.callback_query(F.data == "menu:skincare")
async def callback_start_skincare(cb: CallbackQuery, state: FSMContext) -> None:
    """Skincare button as callback - works from ANY state"""
    print(f"🧴 Skincare callback pressed by user {cb.from_user.id if cb.from_user else 'Unknown'}")
    await state.clear()
    
    from .detailed_skincare import start_detailed_skincare_flow
    
    # Convert callback to message-like object
    if cb.message:
        await start_detailed_skincare_flow(cb.message, state)
        await cb.answer("🧴 Запуск диагностики кожи")


@router.callback_query(F.data == "menu:palette")  
async def callback_start_palette(cb: CallbackQuery, state: FSMContext) -> None:
    """Palette button as callback - works from ANY state"""
    print(f"🎨 Palette callback pressed by user {cb.from_user.id if cb.from_user else 'Unknown'}")
    await state.clear()
    
    from .detailed_palette import start_detailed_palette_flow
    
    # Convert callback to message-like object  
    if cb.message:
        await start_detailed_palette_flow(cb.message, state)
        await cb.answer("🎨 Запуск палитомера")


@router.callback_query(F.data == "menu:about")
async def callback_about(cb: CallbackQuery, state: FSMContext) -> None:
    """About button as callback - works from ANY state"""
    print(f"ℹ️ About callback pressed by user {cb.from_user.id if cb.from_user else 'Unknown'}")
    await state.clear()
    
    if cb.message:
        await cb.message.edit_text(
            "🤖 О боте:\n\n"
            "Я - ваш персональный косметолог! ✨\n\n"
            "🔹 Анализ типа кожи и проблем\n"
            "🔹 Определение цветовой палитры (undertone)\n"
            "🔹 Персональные рекомендации по уходу и макияжу\n"
            "🔹 Прямые ссылки на проверенные продукты\n\n"
            "💡 Пройдите диагностику и получите персонализированный отчет!",
            reply_markup=main_menu(),
        )
        await cb.answer("ℹ️ Информация о боте")


@router.callback_query(F.data == "menu:picks") 
async def callback_my_picks(cb: CallbackQuery, state: FSMContext) -> None:
    """Picks button as callback - works from ANY state"""
    print(f"🛒 Picks callback pressed by user {cb.from_user.id if cb.from_user else 'Unknown'}")
    await state.clear()
    
    # Check if user has saved reports
    from bot.ui.pdf import load_last_report_json
    
    uid = int(cb.from_user.id) if cb.from_user and cb.from_user.id else 0
    if uid:
        report_data = load_last_report_json(uid)
        if report_data and cb.message:
            # User has test results, show cart
            from bot.handlers.cart import show_cart
            await show_cart(cb.message, state)
            await cb.answer("🛒 Ваша подборка")
            return
    
    # No data, show invitation to take test
    if cb.message:
        await cb.message.edit_text(
            "🛒 Моя подборка\n\n"
            "Здесь будут отображаться ваши сохраненные продукты.\n"
            "Пройдите диагностику, чтобы получить персональные рекомендации!",
            reply_markup=main_menu(),
        )
        await cb.answer("🛒 Пройдите тесты для рекомендаций")


@router.callback_query(F.data == "menu:settings")
async def callback_settings(cb: CallbackQuery, state: FSMContext) -> None:
    """Settings button as callback - works from ANY state"""
    print(f"⚙️ Settings callback pressed by user {cb.from_user.id if cb.from_user else 'Unknown'}")
    await state.clear()
    
    if cb.message:
        await cb.message.edit_text(
            "⚙️ Настройки\n\n"
            "Настройки бота:\n"
            "• Язык: Русский 🇷🇺\n"
            "• Уведомления: Включены 🔔\n"
            "• Темная тема: Авто 🌙\n\n"
            "Функция в разработке...",
            reply_markup=main_menu(),
        )
        await cb.answer("⚙️ Настройки бота")


@router.callback_query(F.data == "menu:report")
async def callback_report(cb: CallbackQuery, state: FSMContext) -> None:
    """Report button as callback - works from ANY state"""
    print(f"📊 Report callback pressed by user {cb.from_user.id if cb.from_user else 'Unknown'}")
    await state.clear()
    
    try:
        from bot.handlers.report import send_latest_report
        await send_latest_report(cb)
    except Exception as e:
        print(f"❌ Error in callback report: {e}")
        if cb.message:
            await cb.message.answer("Отчёт ещё не сформирован. Пройдите диагностику или палитрометр.")
        await cb.answer("📊 Нет готовых отчётов")


# ========================================
# UNIVERSAL ANTI-HANG PROTECTION  
# ========================================

@router.callback_query(F.data.startswith("noop"))
async def handle_noop_callback(cb: CallbackQuery, state: FSMContext) -> None:
    """Handle refresh/noop buttons to prevent hanging"""
    print(f"🔄 Noop callback from user {cb.from_user.id if cb.from_user else 'Unknown'}")
    await cb.answer("🔄 Обновлено")


# Last resort callback handler for any unhandled callbacks
@router.callback_query()
async def handle_any_unhandled_callback(cb: CallbackQuery, state: FSMContext) -> None:
    """Catch-all for unhandled callbacks to prevent hanging"""
    print(f"❓ Unhandled callback: '{cb.data}' from user {cb.from_user.id if cb.from_user else 'Unknown'}")
    print(f"🔍 Current state: {await state.get_state()}")
    
    try:
        # Always answer to prevent loading state
        await cb.answer("⚠️ Кнопка не обработана. Используйте боковое меню или /start")
        
        # Send recovery options
        if cb.message:
            from bot.ui.keyboards import main_menu
            await cb.message.answer(
                "⚠️ Произошла ошибка с кнопкой\n\n"
                "Попробуйте:\n"
                "• Использовать кнопки ниже\n"
                "• Нажать /start для сброса",
                reply_markup=main_menu()
            )
            
    except Exception as e:
        print(f"❌ Error in unhandled callback handler: {e}")
        try:
            await cb.answer("❌ Ошибка. Нажмите /start")
        except:
            pass
