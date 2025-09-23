#!/usr/bin/env python3
"""
🛡️ Security Measures Test Script

Tests all implemented security features:
- Message sanitization
- Spam detection
- Chat filtering
- Pin control
- Configuration validation
"""

import sys
import os

# Set test environment before importing
os.environ["BOT_TOKEN"] = "test_token_12345"
os.environ["ALLOW_PIN"] = "false"
os.environ["PIN_WHITELIST"] = ""
os.environ["CHAT_WHITELIST"] = ""
os.environ["SANITIZE_MESSAGES"] = "true"

sys.path.append(".")

from config.env import SecurityConfig, get_settings
from bot.utils.security import (
    MessageSanitizer,
    sanitize_message,
    AntiSpamGuard,
    ChatWhitelistFilter,
)


# Create test instances without requiring full config
def create_test_security_config():
    """Create test security config for testing"""
    return SecurityConfig(
        allow_pin=False, pin_whitelist=[], chat_whitelist=[], sanitize_messages=True
    )


def test_message_sanitization():
    """Test message sanitization"""
    print("🧹 Testing Message Sanitization...")

    sanitizer = MessageSanitizer()

    # Test cases
    test_cases = [
        ("Normal message", "Normal message"),
        ("***Bold***", "**Bold**"),
        ("###Header###", "##Header##"),
        ("---Strikethrough---", "--Strikethrough--"),
        ("```code```", "``code``"),
        ("Multiple   spaces", "Multiple spaces"),
        ("Line1\n\n\nLine2", "Line1\n\nLine2"),
        ("Mixed***\n\n\n###formatting###", "Mixed**\n\n##formatting##"),
    ]

    passed = 0
    for input_text, expected in test_cases:
        result = sanitizer.sanitize(input_text)
        if result == expected:
            print(f"  ✅ '{input_text}' -> '{result}'")
            passed += 1
        else:
            print(f"  ❌ '{input_text}' -> '{result}' (expected: '{expected}')")

    print(f"  📊 Sanitization: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_spam_detection():
    """Test spam detection"""
    print("🚨 Testing Spam Detection...")

    # Create guard with test config
    from bot.utils.security import AntiSpamGuard

    test_config = create_test_security_config()

    class TestAntiSpamGuard(AntiSpamGuard):
        def __init__(self):
            self.settings = type("TestSettings", (), {"security": test_config})()
            # Add logger for testing
            import logging

            self.logger = logging.getLogger("test_guard")

    guard = TestAntiSpamGuard()

    # Test cases
    spam_cases = [
        ("Buy crypto now! BTC to the moon!", True),
        ("airdrop giveaway free money", True),
        ("USDT trading signals x100 profit", True),
        ("FOXY token investment opportunity", True),
        ("Normal skincare advice", False),
        ("Foundation makeup tips", False),
        ("Serum reviews", False),
    ]

    passed = 0
    for text, should_be_spam in spam_cases:
        is_spam = guard.is_spam_content(text)
        if is_spam == should_be_spam:
            status = "🚨 SPAM" if is_spam else "✅ CLEAN"
            print(f"  {status} '{text[:30]}...'")
            passed += 1
        else:
            print(
                f"  ❌ MISMATCH '{text[:30]}...' (expected: {'spam' if should_be_spam else 'clean'})"
            )

    print(f"  📊 Spam detection: {passed}/{len(spam_cases)} passed\n")
    return passed == len(spam_cases)


def test_chat_filtering():
    """Test chat whitelist filtering"""
    print("🚪 Testing Chat Filtering...")

    # Test with default config (empty whitelist = allow all)
    from bot.utils.security import ChatWhitelistFilter

    test_config = create_test_security_config()

    class TestChatFilter(ChatWhitelistFilter):
        def __init__(self):
            self.settings = type("TestSettings", (), {"security": test_config})()

    filter_instance = TestChatFilter()

    test_chats = [
        (123456789, True),  # Should be allowed (empty whitelist)
        (987654321, True),  # Should be allowed (empty whitelist)
    ]

    passed = 0
    for chat_id, should_be_allowed in test_chats:
        allowed = filter_instance.is_chat_allowed(chat_id)
        if allowed == should_be_allowed:
            status = "✅ ALLOWED" if allowed else "🚫 BLOCKED"
            print(f"  {status} Chat {chat_id}")
            passed += 1
        else:
            print(
                f"  ❌ MISMATCH Chat {chat_id} (expected: {'allowed' if should_be_allowed else 'blocked'})"
            )

    print(f"  📊 Chat filtering: {passed}/{len(test_chats)} passed\n")
    return passed == len(test_chats)


def test_security_config():
    """Test security configuration"""
    print("⚙️ Testing Security Configuration...")

    try:
        settings = get_settings()
        security = settings.security

        # Check configuration structure
        assert isinstance(security, SecurityConfig), "Security config not properly loaded"
        assert hasattr(security, "allow_pin"), "Missing allow_pin setting"
        assert hasattr(security, "pin_whitelist"), "Missing pin_whitelist setting"
        assert hasattr(security, "chat_whitelist"), "Missing chat_whitelist setting"
        assert hasattr(security, "sanitize_messages"), "Missing sanitize_messages setting"
        assert hasattr(security, "spam_keywords"), "Missing spam_keywords setting"

        # Check default values
        assert (
            security.allow_pin == False
        ), f"allow_pin should be False by default, got {security.allow_pin}"
        assert isinstance(security.spam_keywords, list), "spam_keywords should be a list"
        assert len(security.spam_keywords) > 0, "spam_keywords should not be empty"

        print("  ✅ Security config structure valid")
        print(f"  ✅ allow_pin: {security.allow_pin}")
        print(f"  ✅ pin_whitelist: {security.pin_whitelist}")
        print(f"  ✅ chat_whitelist: {security.chat_whitelist}")
        print(f"  ✅ spam_keywords: {len(security.spam_keywords)} keywords")

        return True

    except Exception as e:
        print(f"  ❌ Security config test failed: {e}")
        return False


def test_pin_control():
    """Test pin control logic"""
    print("📌 Testing Pin Control...")

    # Create guard with test config
    from bot.utils.security import AntiSpamGuard

    test_config = create_test_security_config()

    class TestAntiSpamGuard(AntiSpamGuard):
        def __init__(self):
            self.settings = type("TestSettings", (), {"security": test_config})()
            # Add logger for testing
            import logging

            self.logger = logging.getLogger("test_guard")

    guard = TestAntiSpamGuard()

    # Test pin control with default settings (pinning disabled)
    test_cases = [
        ("Normal message", None, True),  # Should be unpinned (pinning disabled)
        ("airdrop giveaway free BTC", None, True),  # Should be unpinned (spam + disabled)
        ("Normal skincare message", 123456789, True),  # Should be unpinned (pinning disabled)
    ]

    passed = 0
    for message_text, user_id, should_unpin in test_cases:
        unpin = guard.should_unpin_message(message_text, user_id)
        if unpin == should_unpin:
            status = "🛡️ UNPINNED" if unpin else "📌 ALLOWED"
            print(f"  {status} '{message_text[:30]}...' (user: {user_id})")
            passed += 1
        else:
            print(
                f"  ❌ MISMATCH '{message_text[:30]}...' (expected: {'unpin' if should_unpin else 'allow'})"
            )

    print(f"  📊 Pin control: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def main():
    """Run all security tests"""
    print("🛡️ SECURITY MEASURES TEST SUITE")
    print("=" * 50)

    tests = [
        ("Message Sanitization", test_message_sanitization),
        ("Spam Detection", test_spam_detection),
        ("Chat Filtering", test_chat_filtering),
        ("Security Config", test_security_config),
        ("Pin Control", test_pin_control),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULT: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ALL SECURITY MEASURES WORKING CORRECTLY!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - REVIEW SECURITY IMPLEMENTATION")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
