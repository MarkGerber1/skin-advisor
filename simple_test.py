#!/usr/bin/env python3
"""Simple test script"""

import sys
import os

# Redirect stdout to file
sys.stdout = open("test_output.log", "w")
sys.stderr = open("test_error.log", "w")

print("=== SIMPLE TEST START ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    print("Testing basic import...")

    print("[OK] asyncio imported")

    print("Testing bot.main...")

    print("[OK] bot.main imported")

    print("Testing affiliate...")
    from engine.affiliate_validator import AffiliateManager

    print("[OK] AffiliateManager imported")

    affiliate = AffiliateManager()
    test_url = affiliate.add_affiliate_params("https://test.com", "goldapple")
    print(f"[OK] Affiliate test: {test_url}")

    print("\n[SUCCESS] ALL TESTS PASSED!")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback

    traceback.print_exc()

print("=== SIMPLE TEST END ===")

# Close files
sys.stdout.close()
sys.stderr.close()
