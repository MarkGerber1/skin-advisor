#!/usr/bin/env python3
"""
Тест исправлений корзины
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cart_store():
    """Тест CartStore"""
    print("🛒 Тестирую CartStore...")

    try:
        from services.cart_store import CartStore, get_cart_store
        cart_store = get_cart_store()

        # Тест 1: get_cart вместо get
        user_id = 810311491
        cart_items = cart_store.get_cart(user_id)
        print(f"✅ get_cart работает: {len(cart_items)} товаров")

        # Тест 2: add_item
        cart_store.add_item(user_id, "test_product", name="Test Product", price=100.0)
        cart_items = cart_store.get_cart(user_id)
        print(f"✅ add_item работает: {len(cart_items)} товаров")

        # Тест 3: get_cart_count
        count = cart_store.get_cart_count(user_id)
        print(f"✅ get_cart_count работает: {count} товаров")

        # Тест 4: clear_cart
        cart_store.clear_cart(user_id)
        cart_items = cart_store.get_cart(user_id)
        print(f"✅ clear_cart работает: {len(cart_items)} товаров")

        return True

    except Exception as e:
        print(f"❌ Ошибка CartStore: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_catalog_store():
    """Тест CatalogStore"""
    print("\n📚 Тестирую CatalogStore...")

    try:
        from engine.catalog_store import CatalogStore
        catalog_store = CatalogStore.instance("assets/fixed_catalog.yaml")
        catalog = catalog_store.get()

        if catalog:
            print(f"✅ CatalogStore работает: {len(catalog)} товаров")
            return True
        else:
            print("❌ CatalogStore вернул None")
            return False

    except Exception as e:
        print(f"❌ Ошибка CatalogStore: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 Тест исправлений корзины")
    print("=" * 40)

    tests = [
        ("CartStore", test_cart_store),
        ("CatalogStore", test_catalog_store),
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
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Корзина должна работать!")
    else:
        print("\n⚠️  Есть проблемы, требующие исправления!")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
