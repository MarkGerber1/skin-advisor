"""Universal error handler for bot callbacks"""
from functools import wraps
from typing import Callable, Any
from aiogram.types import CallbackQuery, Message


def callback_error_handler(func: Callable) -> Callable:
    """Decorator to handle errors in callback query handlers"""
    @wraps(func)
    async def wrapper(cb: CallbackQuery, *args, **kwargs) -> Any:
        try:
            return await func(cb, *args, **kwargs)
        except Exception as e:
            print(f"❌ Error in {func.__name__}: {e}")
            try:
                # Try to answer callback to prevent "loading" state
                await cb.answer("❌ Произошла ошибка, попробуйте снова", show_alert=True)
            except Exception as answer_error:
                print(f"❌ Could not answer callback: {answer_error}")
            
            # Try to send error message to user
            try:
                if cb.message and hasattr(cb.message, 'answer'):
                    await cb.message.answer(
                        "⚠️ Что-то пошло не так. Попробуйте:\n"
                        "• Нажать /start для перезапуска\n"
                        "• Подождать несколько секунд и повторить"
                    )
            except Exception as msg_error:
                print(f"❌ Could not send error message: {msg_error}")
                
    return wrapper


def message_error_handler(func: Callable) -> Callable:
    """Decorator to handle errors in message handlers"""
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs) -> Any:
        try:
            return await func(message, *args, **kwargs)
        except Exception as e:
            print(f"❌ Error in {func.__name__}: {e}")
            try:
                await message.answer(
                    "⚠️ Произошла ошибка. Попробуйте:\n"
                    "• Нажать /start для перезапуска\n" 
                    "• Подождать несколько секунд и повторить"
                )
            except Exception as msg_error:
                print(f"❌ Could not send error message: {msg_error}")
                
    return wrapper



