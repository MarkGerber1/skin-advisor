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
    print(f"🏁 /start command from user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()
    
    # Clear any webhook conflicts
    try:
        from aiogram import Bot
        bot = m.bot
        await bot.delete_webhook(drop_pending_updates=True)
        print("🧹 Webhook cleared for conflict resolution")
    except Exception as e:
        print(f"⚠️ Could not clear webhook: {e}")
    
    main_menu_kb = main_menu()
    print(f"📋 Sending main menu with {len(main_menu_kb.keyboard)} rows")
    
    await m.answer(
        "🏠 **ГЛАВНОЕ МЕНЮ**\n\n"
        "Привет! ✨ Я подберу персональный уход и идеальные оттенки макияжа по вашему профилю.\n\n"
        "**👇 ИСПОЛЬЗУЙТЕ КНОПКИ НИЖЕ:**",
        reply_markup=main_menu_kb,
        parse_mode="Markdown"
    )
    print("✅ Main menu sent successfully")


@router.message(F.text == BTN_SKINCARE)
async def start_skincare(m: Message, state: FSMContext) -> None:
    """Start skincare test - works from ANY state"""
    print(f"🧴 SKINCARE BUTTON PRESSED! User: {m.from_user.id if m.from_user else 'Unknown'}")
    print(f"🧴 Message text: '{m.text}'")
    print(f"🧴 BTN_SKINCARE constant: '{BTN_SKINCARE}'")
    print(f"🧴 Text match: {m.text == BTN_SKINCARE}")
    await state.clear()  # Clear any existing state
    
    try:
        from .detailed_skincare import start_detailed_skincare_flow
        await start_detailed_skincare_flow(m, state)
        print("🧴 Skincare flow started successfully!")
    except Exception as e:
        print(f"❌ Error starting skincare flow: {e}")
        await m.answer("❌ Ошибка запуска диагностики. Попробуйте /start")


@router.message(F.text == BTN_PALETTE)
async def start_palette(m: Message, state: FSMContext) -> None:
    """Start palette test - works from ANY state"""
    print(f"🎨 PALETTE BUTTON PRESSED! User: {m.from_user.id if m.from_user else 'Unknown'}")
    print(f"🎨 Message text: '{m.text}'")
    print(f"🎨 BTN_PALETTE constant: '{BTN_PALETTE}'")
    print(f"🎨 Text match: {m.text == BTN_PALETTE}")
    await state.clear()  # Clear any existing state
    
    try:
        from .detailed_palette import start_detailed_palette_flow
        await start_detailed_palette_flow(m, state)
        print("🎨 Palette flow started successfully!")
    except Exception as e:
        print(f"❌ Error starting palette flow: {e}")
        await m.answer("❌ Ошибка запуска палитомера. Попробуйте /start")


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
    
    # Direct report sending without fake callback
    try:
        import os
        try:
            from aiogram.types import FSInputFile
        except ImportError:
            from aiogram.types import InputFile as FSInputFile
            
        uid = int(m.from_user.id) if m.from_user and m.from_user.id else 0
        if not uid:
            await m.answer("❌ Ошибка идентификации пользователя")
            return
            
        path = os.path.join("data", "reports", str(uid), "last.pdf")
        if not os.path.exists(path):
            await m.answer("📄 Отчёт ещё не сформирован.\nПройдите диагностику или палитомер!")
            return
        
        # Direct document sending
        await m.answer_document(
            document=FSInputFile(path),
            caption="📄 Ваш последний отчёт"
        )
        print("✅ Report sent successfully!")
        
    except Exception as e:
        print(f"❌ Error in report_latest: {e}")
        await m.answer("❌ Ошибка при отправке отчёта. Попробуйте позже.")


# ========================================
# REMOVED CALLBACK HANDLERS - SIDE MENU USES TEXT BUTTONS
# ========================================
# Side menu uses ReplyKeyboardMarkup (text buttons), not InlineKeyboardMarkup (callbacks)
# Text handlers above handle: BTN_PALETTE, BTN_SKINCARE, BTN_ABOUT, etc.


# ========================================
# UNIVERSAL ANTI-HANG PROTECTION  
# ========================================

@router.callback_query(F.data.startswith("noop"))
async def handle_noop_callback(cb: CallbackQuery, state: FSMContext) -> None:
    """Handle refresh/noop buttons to prevent hanging"""
    print(f"🔄 Noop callback from user {cb.from_user.id if cb.from_user else 'Unknown'}")
    await cb.answer("🔄 Обновлено")


# REMOVED: Catch-all callback handler moved to separate router
# This handler was intercepting test callbacks (hair:a, eye:b, etc.)
# Now handled by universal router with lower priority


# ========================================
# DEBUG CATCH-ALL MESSAGE HANDLER
# ========================================

@router.message()
async def debug_all_messages(m: Message, state: FSMContext) -> None:
    """Debug handler to catch ALL unhandled messages"""
    print(f"🔍 UNHANDLED MESSAGE from user {m.from_user.id if m.from_user else 'Unknown'}")
    print(f"📝 Message text: '{m.text}'")
    print(f"🔍 Current state: {await state.get_state()}")
    
    # Check if it's a side menu button
    if m.text in [BTN_PALETTE, BTN_SKINCARE, BTN_ABOUT, BTN_PICK, BTN_SETTINGS, BTN_REPORT]:
        print(f"🚨 CRITICAL: Side menu button '{m.text}' not handled by specific handlers!")
        await m.answer(f"⚠️ Кнопка '{m.text}' обнаружена, но не обработана. Проверьте логи.")
    # Handle common commands user is sending
    elif m.text and m.text.startswith('/'):
        command = m.text.lower()
        if command in ['/results', '/результаты']:
            print(f"📊 /results command detected - redirecting to report")
            await report_latest(m, state)
        elif command in ['/export', '/экспорт']:
            print(f"📤 /export command detected - redirecting to report") 
            await report_latest(m, state)
        elif command in ['/privacy', '/конфиденциальность']:
            print(f"🔒 /privacy command detected - redirecting to about")
            await about(m, state)
        elif command in ['/reset', '/сброс']:
            print(f"🔄 /reset command detected - redirecting to start")
            await state.clear()
            await m.answer("🔄 Состояние сброшено", reply_markup=main_menu())
        elif command in ['/help', '/помощь']:
            print(f"❓ /help command detected - redirecting to about")
            await about(m, state)
        else:
            print(f"❓ Unknown command: '{m.text}'")
            await m.answer(
                f"❓ Неизвестная команда: {m.text}\n\n"
                "Используйте кнопки ниже или /start",
                reply_markup=main_menu()
            )
    else:
        print(f"❓ Unknown message: '{m.text}'")
        # Don't respond to avoid spam
