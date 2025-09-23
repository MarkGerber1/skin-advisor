"""
🛡️ Security Utilities Module

Contains security-related utilities for bot protection:
- Message sanitization
- Anti-spam filtering
- Pin control helpers
"""

import re
import logging
from typing import Optional, List
from aiogram import Bot
from config.env import get_settings

logger = logging.getLogger(__name__)


class MessageSanitizer:
    """Sanitizes outgoing messages to prevent markdown artifacts and spam"""

    # Patterns to clean up
    MARKDOWN_ARTIFACTS = [
        r"\*{3,}",  # Multiple asterisks
        r"#{3,}",  # Multiple hashes
        r"-{3,}",  # Multiple dashes
        r"`{3,}",  # Multiple backticks
        r"\n{3,}",  # Multiple newlines
        r" {2,}",  # Multiple spaces
    ]

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Clean up message text by removing markdown artifacts and normalizing formatting

        Args:
            text: Raw message text

        Returns:
            Sanitized message text
        """
        if not text:
            return text

        # Remove markdown artifacts
        for pattern in MessageSanitizer.MARKDOWN_ARTIFACTS:
            text = re.sub(pattern, lambda m: m.group()[0] * 2, text)

        # Normalize spaces and newlines
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Max 2 consecutive newlines
        text = re.sub(r" +", " ", text)  # Max 1 space

        return text.strip()


class AntiSpamGuard:
    """Anti-spam protection for pinned messages"""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)

    def is_spam_content(self, text: str) -> bool:
        """
        Check if message content contains spam keywords

        Args:
            text: Message text to check

        Returns:
            True if spam detected
        """
        if not text:
            return False

        text_lower = text.lower()
        for keyword in self.settings.security.spam_keywords:
            if keyword.lower() in text_lower:
                self.logger.warning(
                    f"🚨 SPAM DETECTED: keyword '{keyword}' found in: {text[:100]}..."
                )
                return True

        return False

    def should_unpin_message(self, message_text: str, user_id: Optional[int] = None) -> bool:
        """
        Determine if a pinned message should be automatically unpinned

        Args:
            message_text: Text of the pinned message
            user_id: ID of user who pinned (if known)

        Returns:
            True if message should be unpinned
        """
        # Check if pinning is allowed at all
        if not self.settings.security.allow_pin:
            self.logger.info("🚫 PIN BLOCKED: Pinning disabled globally")
            return True

        # Check if user is in whitelist
        if user_id and user_id not in self.settings.security.pin_whitelist:
            self.logger.warning(f"🚫 PIN BLOCKED: User {user_id} not in pin whitelist")
            return True

        # Check for spam content
        if self.is_spam_content(message_text):
            self.logger.warning(f"🚨 SPAM PIN DETECTED: {message_text[:100]}...")
            return True

        return False


class ChatWhitelistFilter:
    """Filters incoming messages based on chat whitelist"""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)

    def is_chat_allowed(self, chat_id: int) -> bool:
        """
        Check if chat is allowed to receive bot messages

        Args:
            chat_id: Telegram chat ID

        Returns:
            True if chat is allowed
        """
        # If whitelist is empty, allow all (backward compatibility)
        if not self.settings.security.chat_whitelist:
            return True

        allowed = chat_id in self.settings.security.chat_whitelist
        if not allowed:
            self.logger.warning(f"🚫 CHAT BLOCKED: Chat {chat_id} not in whitelist")

        return allowed

    def is_user_allowed(self, user_id: Optional[int]) -> bool:
        """
        Check if user is allowed to interact with bot

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is allowed
        """
        # For private chats, check chat whitelist (which includes owner)
        # For group chats, additional logic might be needed
        return True  # For now, allow all users (filtering happens at chat level)


# Global instances
sanitizer = MessageSanitizer()
anti_spam_guard = AntiSpamGuard()
chat_filter = ChatWhitelistFilter()


def sanitize_message(text: str) -> str:
    """Convenience function for message sanitization"""
    return sanitizer.sanitize(text)


def check_spam_content(text: str) -> bool:
    """Convenience function for spam checking"""
    return anti_spam_guard.is_spam_content(text)


def is_chat_allowed(chat_id: int) -> bool:
    """Convenience function for chat filtering"""
    return chat_filter.is_chat_allowed(chat_id)


# Safe message sending utilities
async def safe_send_message(bot, chat_id: int, text: str, **kwargs):
    """
    Safely send message with sanitization and chat filtering.

    Args:
        bot: Bot instance
        chat_id: Target chat ID
        text: Message text
        **kwargs: Additional arguments for send_message

    Returns:
        Message object or None if blocked/filtered
    """
    # Check if chat is allowed
    if not is_chat_allowed(chat_id):
        logger.warning(f"🚫 SEND BLOCKED: Chat {chat_id} not in whitelist")
        return None

    # Sanitize message text
    sanitized_text = sanitize_message(text)

    # Send message
    try:
        return await bot.send_message(chat_id=chat_id, text=sanitized_text, **kwargs)
    except Exception as e:
        logger.error(f"Failed to send message to chat {chat_id}: {e}")
        return None


async def safe_edit_message_text(bot, chat_id: int, message_id: int, text: str, **kwargs):
    """
    Safely edit message text with sanitization.

    Args:
        bot: Bot instance
        chat_id: Target chat ID
        message_id: Message ID to edit
        text: New message text
        **kwargs: Additional arguments for edit_message_text

    Returns:
        Message object or None if failed
    """
    # Sanitize message text
    sanitized_text = sanitize_message(text)

    # Edit message
    try:
        return await bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=sanitized_text, **kwargs
        )
    except Exception as e:
        logger.error(f"Failed to edit message {message_id} in chat {chat_id}: {e}")
        return None


async def safe_pin_message(bot, chat_id: int, message_id: int, user_id: int = None, **kwargs):
    """
    Safely pin message with whitelist and security checks.

    Args:
        bot: Bot instance
        chat_id: Target chat ID
        message_id: Message ID to pin
        user_id: User ID attempting to pin (for whitelist check)
        **kwargs: Additional arguments for pin_chat_message

    Returns:
        True if pinned, False if blocked
    """
    settings = get_settings()

    # Check if pinning is allowed globally
    if not settings.security.allow_pin:
        logger.info(
            f"[PIN-INTENT] BLOCKED: Pinning disabled globally (chat {chat_id}, user {user_id})"
        )
        return False

    # Check if user is in whitelist
    if user_id and user_id not in settings.security.pin_whitelist:
        logger.warning(
            f"[PIN-INTENT] BLOCKED: User {user_id} not in pin whitelist (chat {chat_id})"
        )
        return False

    # Log successful pin intent
    logger.info(
        f"[PIN-INTENT] ALLOWED: Pinning message {message_id} in chat {chat_id} by user {user_id}"
    )

    try:
        await bot.pin_chat_message(chat_id=chat_id, message_id=message_id, **kwargs)
        return True
    except Exception as e:
        logger.error(f"Failed to pin message {message_id} in chat {chat_id}: {e}")
        return False


async def safe_unpin_message(
    bot: Bot, chat_id: int, message_id: int, user_id: Optional[int] = None, **kwargs
) -> bool:
    """
    Safely unpin a message with security checks.

    Args:
        bot: Bot instance
        chat_id: Target chat ID
        message_id: Message ID to unpin
        user_id: User ID attempting to unpin (for whitelist check)
        **kwargs: Additional arguments for unpin_chat_message

    Returns:
        True if unpinned, False if blocked
    """
    settings = get_settings()

    # Check if pinning is allowed globally (unpin is reverse of pin)
    if not settings.security.allow_pin:
        logger.info(
            f"[UNPIN-INTENT] BLOCKED: Unpinning disabled globally (chat {chat_id}, user {user_id})"
        )
        return False

    # Check if user is in whitelist
    if user_id and user_id not in settings.security.pin_whitelist:
        logger.warning(
            f"[UNPIN-INTENT] BLOCKED: User {user_id} not in pin whitelist (chat {chat_id})"
        )
        return False

    # Log successful unpin intent
    logger.info(
        f"[UNPIN-INTENT] ALLOWED: Unpinning message {message_id} in chat {chat_id} by user {user_id}"
    )

    try:
        await bot.unpin_chat_message(chat_id=chat_id, message_id=message_id, **kwargs)
        return True
    except Exception as e:
        logger.error(f"Failed to unpin message {message_id} in chat {chat_id}: {e}")
        return False


async def safe_unpin_all_messages(bot: Bot, chat_id: int, user_id: Optional[int] = None) -> bool:
    """
    Safely unpin all messages in a chat with security checks.

    Args:
        bot: Bot instance
        chat_id: Target chat ID
        user_id: User ID attempting to unpin (for whitelist check)

    Returns:
        True if unpinned, False if blocked
    """
    settings = get_settings()

    if not settings.security.allow_pin:
        logger.info(
            f"[UNPIN-ALL-INTENT] BLOCKED: Unpinning disabled globally (chat {chat_id}, user {user_id})"
        )
        return False

    if user_id and user_id not in settings.security.pin_whitelist:
        logger.warning(
            f"[UNPIN-ALL-INTENT] BLOCKED: User {user_id} not in pin whitelist (chat {chat_id})"
        )
        return False

    logger.info(f"[UNPIN-ALL-INTENT] ALLOWED: Unpinning all in chat {chat_id} by user {user_id}")

    try:
        await bot.unpin_all_chat_messages(chat_id=chat_id)
        return True
    except Exception as e:
        logger.error(f"Failed to unpin all messages in chat {chat_id}: {e}")
        return False
