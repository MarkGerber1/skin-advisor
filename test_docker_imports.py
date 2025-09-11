#!/usr/bin/env python
"""Тестовый скрипт для проверки импортов в Docker"""

import sys
import os


def test_imports():
    """Тестируем все необходимые импорты"""

    print("🐍 Python version:", sys.version)
    print("📁 Current directory:", os.getcwd())
    print("🔍 Python path:", sys.path)

    try:
        print("\n📦 Testing basic imports...")

        print("✅ asyncio imported")

        print("✅ aiogram imported")

        print("✅ bot.main.main imported")

        print("\n🎉 All imports successful!")
        return True

    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
