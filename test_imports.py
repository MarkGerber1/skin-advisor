#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""
import sys
import os

print("=== TESTING IMPORTS ===")

# Test cart_service import
try:
    from services.cart_service import get_cart_service, CartServiceError, CartErrorCode
    print("✅ services.cart_service imported successfully")
except ImportError as e:
    print(f"❌ services.cart_service import failed: {e}")

# Test skincare_picker import
try:
    from bot.handlers.skincare_picker import router as skincare_picker_router
    print("✅ bot.handlers.skincare_picker imported successfully")
except ImportError as e:
    print(f"❌ bot.handlers.skincare_picker import failed: {e}")

# Test source_resolver import
try:
    from engine.source_resolver import resolve_source
    print("✅ engine.source_resolver imported successfully")
except ImportError as e:
    print(f"❌ engine.source_resolver import failed: {e}")

# Test analytics functions
try:
    from engine.analytics import track_skincare_recommendations_viewed, track_category_opened
    print("✅ engine.analytics skincare functions imported successfully")
except ImportError as e:
    print(f"❌ engine.analytics import failed: {e}")

print("\n=== IMPORT TEST COMPLETE ===")
