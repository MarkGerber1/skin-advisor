#!/usr/bin/env python3
"""Быстрый тест исправлений"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """Тест конфигурации"""
    print("🔧 Тестирую конфигурацию...")
    try:
        from config.env import get_settings
        settings = get_settings()
        print(f"✅ Конфигурация загружена: {settings.bot_token[:10]}...")
        return True
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def test_cart():
    """Тест корзины"""
    print("\n🛒 Тестирую корзину...")
    try:
        from services.cart_store import CartStore, CartItem
        cart = CartStore()

        # Тест создания CartItem с price_currency
        item = CartItem(
            product_id="test123",
            name="Test Product",
            price=100.0,
            price_currency="RUB"
        )
        print("✅ CartItem создан успешно")
        print(f"   - ID: {item.product_id}")
        print(f"   - Цена: {item.price} {item.price_currency}")

        # Тест добавления в корзину
        cart.add_item("user123", item.product_id, item.variant_id, name=item.name, price=item.price)
        count = cart.get_cart_count("user123")
        if count == 1:
            print("✅ Товар добавлен в корзину")
        else:
            print(f"❌ Ошибка подсчета: {count}")
            return False

        return True
    except Exception as e:
        print(f"❌ Ошибка корзины: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Тест импортов"""
    print("\n📦 Тестирую импорты...")
    try:
        from engine.selector_schema import SKINCARE_CANONICAL_SLUGS, canon_slug
        print("✅ selector_schema импортирован")

        from bot.main import main
        print("✅ bot.main импортирован")

        return True
    except Exception as e:
        print(f"❌ Ошибка импортов: {e}")
        return False

def main():
    print("🚀 Быстрый тест исправлений")
    print("=" * 40)

    tests = [
        ("Конфигурация", test_config),
        ("Импорты", test_imports),
        ("Корзина", test_cart),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в {name}: {e}")
            results.append((name, False))

    print("\n" + "=" * 40)
    print("📊 РЕЗУЛЬТАТЫ:")

    all_passed = True
    for name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  {name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Бот готов к работе!")
    else:
        print("\n⚠️  Есть проблемы, требующие исправления!")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
