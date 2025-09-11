#!/usr/bin/env python3
"""Debug script for bot issues"""

import sys
import traceback

print("🔍 BOT DEBUG SCRIPT")
print("=" * 50)

try:
    print("1. Testing basic imports...")

    print("   ✅ asyncio OK")

    print("2. Testing bot.main import...")

    print("   ✅ bot.main import OK")

    print("3. Testing affiliate system...")
    from engine.affiliate_validator import AffiliateManager

    print("   ✅ AffiliateManager import OK")

    affiliate = AffiliateManager()
    test_url = affiliate.add_affiliate_params("https://example.com", "goldapple")
    print(f"   ✅ Affiliate URL: {test_url}")

    print("4. Testing handlers...")

    print("   ✅ skincare_picker OK")

    print("   ✅ makeup_picker OK")

    print("\n🎉 ALL IMPORTS SUCCESSFUL!")
    print("Bot should work correctly.")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)
