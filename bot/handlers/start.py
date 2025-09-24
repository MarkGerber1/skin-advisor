from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart
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
from .fsm_coordinator import get_fsm_coordinator


router = Router()


@router.message(CommandStart())
async def on_start(m: Message, state: FSMContext) -> None:
    print(f"🏁 /start command from user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()

    # Clear any webhook conflicts
    try:

        bot = m.bot
        await bot.delete_webhook(drop_pending_updates=True)
        print("🧹 Webhook cleared for conflict resolution")
    except Exception as e:
        print(f"⚠️ Could not clear webhook: {e}")

    main_menu_kb = main_menu()
    print(f"📋 Sending main menu with {len(main_menu_kb.keyboard)} rows")

    from bot.utils.security import sanitize_message

    await m.answer(
        sanitize_message(
            "🏠 ГЛАВНОЕ МЕНЮ\n\n"
            "Привет! ✨ Я подберу персональный уход и идеальные оттенки макияжа по вашему профилю.\n\n"
            "👇 ИСПОЛЬЗУЙТЕ КНОПКИ НИЖЕ:"
        ),
        reply_markup=main_menu_kb,
    )
    print("✅ Main menu sent successfully")


@router.message(F.text == BTN_SKINCARE)
async def start_skincare(m: Message, state: FSMContext) -> None:
    """Start skincare test with FSM coordination"""
    print(f"🧴 SKINCARE BUTTON PRESSED! User: {m.from_user.id if m.from_user else 'Unknown'}")

    coordinator = get_fsm_coordinator()
    user_id = m.from_user.id if m.from_user else 0

    # АГРЕССИВНАЯ очистка - принудительно удаляем ЛЮБУЮ существующую сессию
    print(f"🧹 SKINCARE: Force clearing any existing session for user {user_id}")
    await coordinator.clear_user_session(user_id)
    await coordinator.force_cleanup_expired_sessions()

    # Check for flow conflicts
    can_start, conflict_msg = await coordinator.can_start_flow(user_id, "detailed_skincare")
    if not can_start:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Продолжить текущий", callback_data="recovery:continue"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Начать заново", callback_data="recovery:restart:detailed_skincare"
                    )
                ],
                [InlineKeyboardButton(text="🏠 Домой", callback_data="recovery:home")],
            ]
        )
        from bot.utils.security import sanitize_message

        await m.answer(sanitize_message(conflict_msg), reply_markup=kb)
        return

    # Check for session recovery - НЕ ДОЛЖНО срабатывать после принудительной очистки
    recovery_msg = await coordinator.get_recovery_message(user_id)
    if recovery_msg:
        print("⚠️ UNEXPECTED: Recovery message still exists after cleanup!")
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Продолжить", callback_data="recovery:continue")],
                [
                    InlineKeyboardButton(
                        text="🔄 Начать заново", callback_data="recovery:restart:detailed_skincare"
                    )
                ],
                [InlineKeyboardButton(text="🏠 Домой", callback_data="recovery:home")],
            ]
        )
        from bot.utils.security import sanitize_message

        await m.answer(sanitize_message(recovery_msg), reply_markup=kb)
        return

    await state.clear()  # Clear any existing state

    try:
        # Start new coordinated flow
        await coordinator.start_flow(user_id, "detailed_skincare", state)

        from .detailed_skincare import start_detailed_skincare_flow

        await start_detailed_skincare_flow(m, state)
        print("🧴 Skincare flow started successfully!")
    except Exception as e:
        print(f"❌ Error starting skincare flow: {e}")
        await coordinator.abandon_flow(user_id, state)
        await m.answer("❌ Ошибка запуска диагностики. Попробуйте /start")


@router.message(F.text == BTN_PALETTE)
async def start_palette(m: Message, state: FSMContext) -> None:
    """Start palette test with FSM coordination"""
    print(f"🎨 PALETTE BUTTON PRESSED! User: {m.from_user.id if m.from_user else 'Unknown'}")

    coordinator = get_fsm_coordinator()
    user_id = m.from_user.id if m.from_user else 0

    # АГРЕССИВНАЯ очистка - принудительно удаляем ЛЮБУЮ существующую сессию
    print(f"🧹 PALETTE: Force clearing any existing session for user {user_id}")
    await coordinator.clear_user_session(user_id)
    await coordinator.force_cleanup_expired_sessions()

    # Check for flow conflicts
    can_start, conflict_msg = await coordinator.can_start_flow(user_id, "detailed_palette")
    if not can_start:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Продолжить текущий", callback_data="recovery:continue"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Начать заново", callback_data="recovery:restart:detailed_palette"
                    )
                ],
                [InlineKeyboardButton(text="🏠 Домой", callback_data="recovery:home")],
            ]
        )
        from bot.utils.security import sanitize_message

        await m.answer(sanitize_message(conflict_msg), reply_markup=kb)
        return

    # Check for session recovery - НЕ ДОЛЖНО срабатывать после принудительной очистки
    recovery_msg = await coordinator.get_recovery_message(user_id)
    if recovery_msg:
        print("⚠️ UNEXPECTED: Recovery message still exists after cleanup!")
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Продолжить", callback_data="recovery:continue")],
                [
                    InlineKeyboardButton(
                        text="🔄 Начать заново", callback_data="recovery:restart:detailed_palette"
                    )
                ],
                [InlineKeyboardButton(text="🏠 Домой", callback_data="recovery:home")],
            ]
        )
        from bot.utils.security import sanitize_message

        await m.answer(sanitize_message(recovery_msg), reply_markup=kb)
        return

    await state.clear()  # Clear any existing state

    try:
        # Start new coordinated flow
        await coordinator.start_flow(user_id, "detailed_palette", state)

        from .detailed_palette import start_detailed_palette_flow

        await start_detailed_palette_flow(m, state)
        print("🎨 Palette flow started successfully!")
    except Exception as e:
        print(f"❌ Error starting palette flow: {e}")
        await coordinator.abandon_flow(user_id, state)
        await m.answer("❌ Ошибка запуска палитомера. Попробуйте /start")


@router.message(F.text == BTN_ABOUT)
async def about(m: Message, state: FSMContext) -> None:
    """Show about info - works from ANY state"""
    print(f"ℹ️ About button pressed by user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()
    await m.answer(
        "🤖 **О боте:**\n\n"
        "Я - ваш персональный косметолог! ✨\n\n"
        "🔹 Анализ типа кожи и проблем\n"
        "🔹 Определение цветовой палитры (undertone)\n"
        "🔹 Персональные рекомендации по уходу и макияжу\n"
        "🔹 Прямые ссылки на проверенные продукты\n\n"
        "💡 Пройдите диагностику и получите персонализированный отчет!\n\n"
        "═══════════════════════\n"
        "👨‍💻 **Разработчик:** Laboratory from Larin R.R\n"
        "📱 **Telegram:** @GerberMark\n"
        "🌐 **Сайт:** stasya-makeuphair.ru\n"
        "═══════════════════════",
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
            from bot.handlers.cart_v2 import show_cart

            await show_cart(m, state)
            return

    # Если нет данных, показываем приглашение пройти тест
    await m.answer(
        "🛒 Моя подборка\n\n"
        "Здесь будут отображаться ваши сохраненные продукты.\n"
        "Сначала пройдите диагностику лица или определение палитры!",
        reply_markup=main_menu(),
    )


@router.message(F.text == BTN_SETTINGS)
async def settings(m: Message, state: FSMContext) -> None:
    """Show settings - works from ANY state"""
    print(f"⚙️ Settings button pressed by user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()

    from bot.ui.keyboards import InlineKeyboardMarkup, InlineKeyboardButton

    settings_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Очистить данные", callback_data="settings:clear_data")],
            [InlineKeyboardButton(text="📞 Поддержка", callback_data="settings:support")],
            [
                InlineKeyboardButton(
                    text="🔒 Политика конфиденциальности", callback_data="settings:privacy"
                )
            ],
            [InlineKeyboardButton(text="ℹ️ О боте", callback_data="settings:about")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="settings:back")],
        ]
    )

    await m.answer(
        "⚙️ **НАСТРОЙКИ БОТА**\n\n" "Доступные функции:",
        reply_markup=settings_kb,
        parse_mode="Markdown",
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
        await m.answer_document(document=FSInputFile(path), caption="📄 Ваш последний отчёт")
        print("✅ Report sent successfully!")

    except Exception as e:
        print(f"❌ Error in report_latest: {e}")
        await m.answer("❌ Ошибка при отправке отчёта. Попробуйте позже.")


async def privacy_policy(m: Message, state: FSMContext) -> None:
    """Show privacy policy"""
    print(f"🔒 Privacy policy shown to user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()

    privacy_text = """🔒 **ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ**

**Сбор данных:**
• Мы НЕ сохраняем персональные данные
• Анализируем только ответы на тесты
• Результаты хранятся локально на устройстве

**Использование данных:**
• Данные используются только для генерации рекомендаций
• Не передаются третьим лицам
• Не используются для рекламы

**Ваши права:**
• Удаление данных: /reset или "Очистить данные" в настройках
• Запрос информации: обратитесь в поддержку
• Отказ от обработки: прекратите использование бота

**Контакты:**
• Поддержка: команда /help
• Вопросы: напишите администратору

Используя бота, вы соглашаетесь с данной политикой."""

    from bot.ui.keyboards import InlineKeyboardMarkup, InlineKeyboardButton

    privacy_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Понятно", callback_data="privacy:accept")],
            [InlineKeyboardButton(text="🗑️ Удалить мои данные", callback_data="privacy:delete")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="privacy:back")],
        ]
    )

    from bot.utils.security import sanitize_message

    await m.answer(sanitize_message(privacy_text), reply_markup=privacy_kb)


# ========================================
# SETTINGS CALLBACK HANDLERS
# ========================================


@router.callback_query(F.data.startswith("settings:"))
async def handle_settings(cb: CallbackQuery, state: FSMContext) -> None:
    """Handle settings menu interactions"""
    action = cb.data.split(":")[1]

    if action == "clear_data":
        await cb.answer("🗑️ Данные очищены! Нажмите /start для перезапуска", show_alert=True)
        await state.clear()

    elif action == "support":
        if cb.message:
            await cb.message.answer(
                "📞 **ПОДДЕРЖКА**\n\n"
                "• Проблемы с ботом: команда /help\n"
                "• Вопросы по товарам: используйте ссылки в рекомендациях\n"
                "• Технические вопросы: перезапустите бота командой /start\n\n"
                "Бот работает автоматически 24/7",
            )
        await cb.answer("📞 Информация о поддержке отправлена")

    elif action == "privacy":
        if cb.message:
            # Convert message to fake message for privacy_policy function
            class FakeMessage:
                def __init__(self, original_message):
                    self.from_user = original_message.chat
                    self.answer = original_message.answer

            fake_msg = FakeMessage(cb.message)
            await privacy_policy(fake_msg, state)
        await cb.answer("🔒 Политика конфиденциальности")

    elif action == "about":
        if cb.message:
            await cb.message.answer(
                "🤖 **О боте:**\n\n"
                "Я - ваш персональный косметолог! ✨\n\n"
                "🔹 Анализ типа кожи и проблем\n"
                "🔹 Определение цветовой палитры (undertone)\n"
                "🔹 Персональные рекомендации по уходу и макияжу\n"
                "🔹 Прямые ссылки на проверенные продукты\n\n"
                "💡 Пройдите диагностику и получите персонализированный отчет!\n\n"
                "═══════════════════════\n"
                "👨‍💻 **Разработчик:** Laboratory from Larin R.R\n"
                "📱 **Telegram:** @GerberMark\n"
                "🌐 **Сайт:** stasya-makeuphair.ru\n"
                "═══════════════════════",
            )
        await cb.answer("ℹ️ Информация о боте отправлена")

    elif action == "back":
        if cb.message:
            await cb.message.edit_text(
                "🏠 Главное меню\n\nВыберите действие:", reply_markup=main_menu()
            )
        await cb.answer("⬅️ Возврат в меню")


@router.callback_query(F.data.startswith("privacy:"))
async def handle_privacy(cb: CallbackQuery, state: FSMContext) -> None:
    """Handle privacy policy interactions"""
    action = cb.data.split(":")[1]

    if action == "accept":
        await cb.answer("✅ Спасибо за ознакомление с политикой")

    elif action == "delete":
        await cb.answer(
            "🗑️ Все ваши данные удалены! Нажмите /start для нового начала", show_alert=True
        )
        await state.clear()

    elif action == "back":
        if cb.message:
            await cb.message.edit_text(
                "🏠 Главное меню\n\nВыберите действие:", reply_markup=main_menu_inline()
            )
        await cb.answer("⬅️ Возврат в меню")


@router.callback_query(F.data.startswith("recovery:"))
async def handle_recovery(cb: CallbackQuery, state: FSMContext) -> None:
    """Handle session recovery interactions"""

    coordinator = get_fsm_coordinator()
    user_id = cb.from_user.id if cb.from_user else 0

    action = cb.data.split(":")[1]

    if action == "continue":
        # Continue existing session
        session = await coordinator.get_session(user_id)
        if not session:
            await cb.answer("❌ Сеанс истек, начните заново", show_alert=True)
            if cb.message:
                # Используем inline версию для edit_text
                from bot.ui.keyboards import main_menu_inline

                await cb.message.edit_text(
                    "🏠 Главное меню\n\nВыберите действие:", reply_markup=main_menu_inline()
                )
            return

        # Resume flow - restart from beginning since resume functions cause loops
        try:
            await cb.answer("🔄 Перезапускаем тест с начала...")
            await coordinator.abandon_flow(user_id, state)

            if session.current_flow == "detailed_palette":
                await coordinator.start_flow(user_id, "detailed_palette", state)
                from .detailed_palette import start_detailed_palette_flow

                # Convert callback to message for compatibility
                fake_message = type(
                    "obj",
                    (object,),
                    {
                        "from_user": cb.from_user,
                        "answer": cb.message.answer if cb.message else lambda *a, **k: None,
                    },
                )()
                await start_detailed_palette_flow(fake_message, state)

            elif session.current_flow == "detailed_skincare":
                await coordinator.start_flow(user_id, "detailed_skincare", state)
                from .detailed_skincare import start_detailed_skincare_flow

                # Convert callback to message for compatibility
                fake_message = type(
                    "obj",
                    (object,),
                    {
                        "from_user": cb.from_user,
                        "answer": cb.message.answer if cb.message else lambda *a, **k: None,
                    },
                )()
                await start_detailed_skincare_flow(fake_message, state)

            else:
                await cb.answer("❌ Неизвестный тип потока", show_alert=True)
                await coordinator.abandon_flow(user_id, state)
                # Go to main menu
                from bot.ui.keyboards import main_menu_inline

                if cb.message:
                    await cb.message.edit_text(
                        "🏠 Главное меню\n\nВыберите действие:", reply_markup=main_menu_inline()
                    )

        except Exception as e:
            print(f"❌ Error in recovery restart: {e}")
            await cb.answer("❌ Ошибка. Переходим в главное меню", show_alert=True)
            await coordinator.abandon_flow(user_id, state)

            # Go to main menu
            from bot.ui.keyboards import main_menu_inline

            if cb.message:
                await cb.message.edit_text(
                    "🏠 Главное меню\n\nВыберите действие:", reply_markup=main_menu_inline()
                )

    elif action == "restart":
        # Start new flow, abandon current
        await coordinator.abandon_flow(user_id, state)

        # Get new flow type
        parts = cb.data.split(":")
        if len(parts) >= 3:
            new_flow = parts[2]

            # Start new flow
            await coordinator.start_flow(user_id, new_flow, state)

            if new_flow == "detailed_palette":
                from .detailed_palette import start_detailed_palette_flow

                # Convert callback to message for compatibility
                fake_message = type(
                    "obj",
                    (object,),
                    {
                        "from_user": cb.from_user,
                        "answer": cb.message.answer if cb.message else lambda *a, **k: None,
                    },
                )()
                await start_detailed_palette_flow(fake_message, state)

            elif new_flow == "detailed_skincare":
                from .detailed_skincare import start_detailed_skincare_flow

                # Convert callback to message for compatibility
                fake_message = type(
                    "obj",
                    (object,),
                    {
                        "from_user": cb.from_user,
                        "answer": cb.message.answer if cb.message else lambda *a, **k: None,
                    },
                )()
                await start_detailed_skincare_flow(fake_message, state)

        await cb.answer("🔄 Новый тест запущен")

    elif action == "home":
        # Go to main menu, abandon flow
        await coordinator.abandon_flow(user_id, state)

        if cb.message:
            await cb.message.edit_text(
                "🏠 **ГЛАВНОЕ МЕНЮ**\n\n"
                "Привет! ✨ Я подберу персональный уход и идеальные оттенки макияжа по вашему профилю.\n\n"
                "**👇 ИСПОЛЬЗУЙТЕ КНОПКИ НИЖЕ:**",
                reply_markup=main_menu(),
            )

        await cb.answer("🏠 Возврат в главное меню")


# ========================================
# REMOVED CALLBACK HANDLERS - SIDE MENU USES TEXT BUTTONS
# ========================================
# Side menu uses ReplyKeyboardMarkup (text buttons), not InlineKeyboardMarkup (callbacks)
# Text handlers above handle: BTN_PALETTE, BTN_SKINCARE, BTN_ABOUT, etc.


async def help_command(m: Message, state: FSMContext) -> None:
    """Show help information - works from ANY state"""
    print(f"❓ Help requested by user {m.from_user.id if m.from_user else 'Unknown'}")
    await state.clear()
    await m.answer(
        "❓ **Как пользоваться ботом:**\n\n"
        "1. **🧴 Уход для лица** — пройдите тест для определения типа лица и получите персональные рекомендации\n"
        "2. **🎨 Палитометр** — определите свой цветотип и подберите идеальные оттенки макияжа\n"
        "3. **📄 Отчёт** — просмотрите результаты последней диагностики\n"
        "4. **🛍 Моя подборка** — сохраненные рекомендованные продукты\n"
        "5. **⚙️ Настройки** — настройки бота и профиля\n\n"
        "**Команды:**\n"
        "• `/start` — перезапуск бота\n"
        "• `/help` — эта справка\n"
        "• `/privacy` — политика конфиденциальности\n\n"
        "💡 **Совет:** Начните с тестов для получения персональных рекомендаций!",
        reply_markup=main_menu(),
    )


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
    elif m.text and m.text.startswith("/"):
        command = m.text.lower()
        if command in ["/results", "/результаты"]:
            print("📊 /results command detected - redirecting to report")
            await report_latest(m, state)
        elif command in ["/export", "/экспорт"]:
            print("📤 /export command detected - redirecting to report")
            await report_latest(m, state)
        elif command in ["/privacy", "/конфиденциальность"]:
            print("🔒 /privacy command detected - showing privacy policy")
            await privacy_policy(m, state)
        elif command in ["/reset", "/сброс"]:
            print("🔄 /reset command detected - redirecting to start")
            await state.clear()
            await m.answer("🔄 Состояние сброшено", reply_markup=main_menu())
        elif command in ["/help", "/помощь"]:
            print("❓ /help command detected - showing help")
            await help_command(m, state)
        else:
            print(f"❓ Unknown command: '{m.text}'")
            await m.answer(
                f"❓ Неизвестная команда: {m.text}\n\n" "Используйте кнопки ниже или /start",
                reply_markup=main_menu(),
            )
    else:
        print(f"❓ Unknown message: '{m.text}'")
        # Don't respond to avoid spam
