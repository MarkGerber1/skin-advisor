#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

print("Testing imports...")

# Test direct i18n import
try:
    from i18n import ru

    print("✅ i18n.ru imported successfully")
    print(f"  BTN_CLEANSE = {ru.BTN_CLEANSE}")
except ImportError as e:
    print(f"❌ i18n.ru import failed: {e}")

# Test i18n.__init__.py
try:
    import i18n

    print("✅ i18n package imported successfully")
    if hasattr(i18n, "BTN_CLEANSE"):
        print(f"  BTN_CLEANSE from i18n = {i18n.BTN_CLEANSE}")
    else:
        print("  BTN_CLEANSE not in i18n namespace")
except ImportError as e:
    print(f"❌ i18n package import failed: {e}")

# Test skincare_picker constants
try:
    # Import the module to trigger fallback
    import bot.handlers.skincare_picker

    print("✅ skincare_picker imported successfully")

    # Check if constants are defined
    import bot.handlers.skincare_picker as sp

    if hasattr(sp, "BTN_CLEANSE"):
        print(f"  BTN_CLEANSE from skincare_picker = {sp.BTN_CLEANSE}")
    else:
        print("  BTN_CLEANSE not in skincare_picker namespace")
except ImportError as e:
    print(f"❌ skincare_picker import failed: {e}")
except Exception as e:
    print(f"❌ skincare_picker error: {e}")

print("Test completed.")
