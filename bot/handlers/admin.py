"""
🛡️ Admin Commands Handler

Administrative commands for bot owner:
- /reset_pins - Unpin all messages in owner chat
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command

from config.env import get_settings

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("reset_pins"))
async def handle_reset_pins(message: Message, bot: Bot):
    """
    Admin command to unpin all messages in owner chat.

    Only works for owner_id user.
    """
    try:
        settings = get_settings()
        user_id = message.from_user.id

        # Check if user is owner
        if not settings.owner_id or user_id != settings.owner_id:
            await message.answer("🚫 Доступ запрещен. Эта команда только для владельца бота.")
            logger.warning(f"[ADMIN] Unauthorized access to /reset_pins by user {user_id}")
            return

        # Unpin all messages in owner chat
        from bot.utils.security import safe_unpin_all_messages

        await safe_unpin_all_messages(bot, settings.owner_id, user_id)

        # Send confirmation
        await message.answer("✅ Все пины очищены в вашем приватном чате.")

        # Log action
        logger.info(
            f"[ADMIN] User {user_id} executed /reset_pins - unpinned all in chat {settings.owner_id}"
        )

    except Exception as e:
        logger.error(f"Error in /reset_pins command: {e}")
        await message.answer("❌ Произошла ошибка при очистке пинов.")


# Export router
__all__ = ["router"]
