"""Universal handlers for state recovery and navigation"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from bot.ui.keyboards import main_menu, BTN_HOME

router = Router()


# Debug handler moved to end of router chain


@router.callback_query(F.data == "universal:home")
async def universal_home_callback(cb: CallbackQuery, state: FSMContext) -> None:
    """Universal home button - always works from any state"""
    try:
        print(f"🏠 Universal home called by user {cb.from_user.id if cb.from_user else 'Unknown'}")

        # Clear all FSM state
        await state.clear()

        # Send main menu
        if cb.message:
            await cb.message.edit_text(
                "🏠 Главное меню\n\n" "Выберите действие:", reply_markup=None
            )
            # Send main menu keyboard as new message
            await cb.message.answer("Что хотите сделать?", reply_markup=main_menu())

        await cb.answer("🏠 Возврат в главное меню")

    except Exception as e:
        print(f"❌ Error in universal home: {e}")
        try:
            await cb.answer("🏠 Состояние сброшено. Нажмите /start")
        except:
            pass


@router.callback_query(F.data == "universal:retry")
async def universal_retry_callback(cb: CallbackQuery, state: FSMContext) -> None:
    """Universal retry button"""
    try:
        print(f"🔄 Universal retry called by user {cb.from_user.id if cb.from_user else 'Unknown'}")

        # Get current state
        current_state = await state.get_state()
        print(f"🔍 Current state: {current_state}")

        if current_state:
            await cb.answer("🔄 Состояние сохранено, попробуйте снова")
        else:
            # No state, go to main menu
            await state.clear()
            await cb.message.edit_text(
                "🔄 Возврат в главное меню\n\n" "Выберите действие:", reply_markup=None
            )
            await cb.message.answer("Что хотите сделать?", reply_markup=main_menu())
            await cb.answer("🔄 Состояние сброшено")

    except Exception as e:
        print(f"❌ Error in universal retry: {e}")
        try:
            await cb.answer("🔄 Ошибка повтора. Нажмите /start")
        except:
            pass


@router.message(F.text == BTN_HOME)
async def home_button_message(message: Message, state: FSMContext) -> None:
    """Handle home button from text messages"""
    try:
        print(
            f"🏠 Home button pressed by user {message.from_user.id if message.from_user else 'Unknown'}"
        )

        # Clear all state
        await state.clear()

        await message.answer("🏠 Главное меню\n\n" "Что хотите сделать?", reply_markup=main_menu())

    except Exception as e:
        print(f"❌ Error in home button: {e}")
        await message.answer(
            "🏠 Возврат в главное меню.\nЕсли проблемы продолжаются, нажмите /start"
        )


@router.message(F.text.in_({"🏠", "домой", "главное меню", "меню", "назад", "выход"}))
async def emergency_home_keywords(message: Message, state: FSMContext) -> None:
    """Emergency home via keywords"""
    try:
        print(
            f"🚨 Emergency home via keyword '{message.text}' by user {message.from_user.id if message.from_user else 'Unknown'}"
        )

        # Clear all state
        await state.clear()

        await message.answer(
            "🏠 Экстренный возврат в главное меню\n\n" "Что хотите сделать?",
            reply_markup=main_menu(),
        )

    except Exception as e:
        print(f"❌ Error in emergency home: {e}")
        await message.answer("🏠 Нажмите /start для сброса")


# State recovery middleware
async def state_recovery_middleware(message: Message, state: FSMContext) -> bool:
    """Check if user is stuck in bad state and offer recovery"""
    try:
        current_state = await state.get_state()
        state_data = await state.get_data()

        # If user has been in the same state for too long, offer recovery
        if current_state and len(state_data.get("error_count", [])) > 3:
            print(
                f"🚨 User {message.from_user.id if message.from_user else 'Unknown'} seems stuck in state {current_state}"
            )

            await message.answer(
                "⚠️ Похоже, что-то пошло не так.\n\n"
                "Попробуйте:\n"
                "• 🏠 Главное меню\n"
                "• /start для полного сброса",
                reply_markup=main_menu(),
            )

            # Clear problematic state
            await state.clear()
            return True

    except Exception as e:
        print(f"❌ Error in state recovery middleware: {e}")

    return False


# ========================================
# CATCH-ALL CALLBACK HANDLER (LOW PRIORITY)
# ========================================


@router.callback_query()
async def handle_any_unhandled_callback(cb: CallbackQuery, state: FSMContext) -> None:
    """Catch-all for unhandled callbacks - LOWEST priority"""
    print(
        f"❓ TRULY UNHANDLED callback: '{cb.data}' from user {cb.from_user.id if cb.from_user else 'Unknown'}"
    )
    print(f"🔍 Current state: {await state.get_state()}")

    # Don't handle test-related callbacks - let them be processed by test routers
    if cb.data and any(
        prefix in cb.data
        for prefix in [
            "hair:",
            "eye:",
            "skin:",
            "lips:",
            "face:",
            "contrast:",
            "style:",
            "undertone:",
        ]
    ):
        print(f"🧪 Test callback detected: {cb.data} - should be handled by test router")
        print("⚠️ State mismatch - resetting to allow proper handling")

        # Clear state to allow proper handling
        await state.clear()

        try:
            await cb.answer("⚠️ Состояние сброшено. Начните тест заново с /start")
        except:
            pass
        return

    try:
        # Always answer to prevent loading state
        await cb.answer("⚠️ Кнопка не обработана. Используйте боковое меню или /start")

        # Send recovery options
        if cb.message:
            await cb.message.answer(
                "⚠️ Произошла ошибка с кнопкой\n\n"
                "Попробуйте:\n"
                "• Использовать кнопки ниже\n"
                "• Нажать /start для сброса",
                reply_markup=main_menu(),
            )

    except Exception as e:
        print(f"❌ Error in catch-all callback handler: {e}")
        try:
            await cb.answer("❌ Ошибка. Нажмите /start")
        except:
            pass
