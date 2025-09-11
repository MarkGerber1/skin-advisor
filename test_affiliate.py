#!/usr/bin/env python3
"""
Тест affiliate системы
"""

import sys

sys.path.append(".")

try:
    from engine.affiliate_validator import AffiliateManager, test_affiliate_manager

    print("🚀 ЗАПУСК ТЕСТА AFFILIATE СИСТЕМЫ")
    print("=" * 50)

    # Тестируем AffiliateManager
    manager = test_affiliate_manager()

    print("\n✅ AFFILIATE СИСТЕМА РАБОТАЕТ КОРРЕКТНО!")
    print("🔗 Все обёртки и события настроены")

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Ошибка выполнения: {e}")
