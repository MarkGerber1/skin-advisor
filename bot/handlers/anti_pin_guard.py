"""
🛡️ Anti-Pin Guard Handler

Automatically detects and removes suspicious pinned messages in private chats.
Provides protection against spam and unauthorized pinning.
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from bot.utils.security import anti_spam_guard, chat_filter
from config.env import get_settings

logger = logging.getLogger(__name__)
router = Router()

@router.pinned_message()
async def handle_pinned_message(message: Message, bot: Bot):
    """
    Handle pinned message events.

    Automatically unpins suspicious content based on:
    - Pinning disabled globally
    - User not in whitelist
    - Spam keywords detected
    """
    try:
        settings = get_settings()

        # Skip if chat not in whitelist
        if not chat_filter.is_chat_allowed(message.chat.id):
            logger.info(f"🚫 PIN IGNORED: Chat {message.chat.id} not in whitelist")
            return

        # Get the pinned message content
        pinned_msg = message.pinned_message
        if not pinned_msg:
            return

        # Extract text content
        message_text = ""
        if pinned_msg.text:
            message_text = pinned_msg.text
        elif pinned_msg.caption:
            message_text = pinned_msg.caption
        else:
            # No text content to analyze
            return

        # Get user who pinned (if available from the pin event)
        user_id = getattr(message.from_user, 'id', None) if message.from_user else None

        # Check if message should be unpinned
        if anti_spam_guard.should_unpin_message(message_text, user_id):
            try:
                # Unpin the message
                await bot.unpin_chat_message(
                    chat_id=message.chat.id,
                    message_id=pinned_msg.message_id
                )

                # Log the action
                logger.warning(
                    f"[ANTI-PIN] Unpinned suspicious message in chat {message.chat.id} "
                    f"by user {user_id}: {message_text[:100]}..."
                )

                # Notify owner if configured
                if settings.owner_id and settings.owner_id != user_id:
                    try:
                        await bot.send_message(
                            chat_id=settings.owner_id,
                            text=(
                                f"🚨 **ANTI-PIN ALERT**\n\n"
                                f"Chat: `{message.chat.id}`\n"
                                f"User: `{user_id or 'Unknown'}`\n"
                                f"Content: `{message_text[:200]}...`\n\n"
                                f"_Message automatically unpinned_"
                            ),
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify owner: {e}")

            except TelegramBadRequest as e:
                logger.error(f"Failed to unpin message: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in anti-pin guard: {e}")

        else:
            # Log successful pin (for monitoring)
            logger.info(
                f"[PIN-ALLOWED] Message pinned in chat {message.chat.id} "
                f"by user {user_id}: {message_text[:50]}..."
            )

    except Exception as e:
        logger.error(f"Error in anti-pin guard handler: {e}")

# Export router
__all__ = ["router"]
