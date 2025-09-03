#!/usr/bin/env python3
"""
Отладка проблем с корзиной и покупками
"""

import os
import sys
import traceback

def test_imports():
    """Тестируем импорты"""
    print("🔍 Тестируем импорты...")

    try:
        from engine.catalog_store import CatalogStore
        print("✅ CatalogStore imported")
    except ImportError as e:
        print(f"❌ CatalogStore import failed: {e}")
        return False

    try:
        from engine.models import UserProfile
        print("✅ UserProfile imported")
    except ImportError as e:
        print(f"❌ UserProfile import failed: {e}")
        return False

    try:
        from engine.selector import SelectorV2
        print("✅ SelectorV2 imported")
    except ImportError as e:
        print(f"❌ SelectorV2 import failed: {e}")
        return False

    try:
        from engine.cart_store import CartStore
        print("✅ CartStore imported")
    except ImportError as e:
        print(f"❌ CartStore import failed: {e}")
        return False

    return True

def test_catalog():
    """Тестируем каталог"""
    print("\n🔍 Тестируем каталог...")

    catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
    print(f"📁 Catalog path: {catalog_path}")
    print(f"📄 File exists: {os.path.exists(catalog_path)}")

    if not os.path.exists(catalog_path):
        print("❌ Catalog file not found!")
        return False

    try:
        from engine.catalog_store import CatalogStore
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()

        print(f"📊 Catalog loaded: {len(catalog)} products")

        # Count by type
        skincare = [p for p in catalog if p.get('type') == 'skincare']
        makeup = [p for p in catalog if p.get('type') == 'makeup']

        print(f"🧴 Skincare: {len(skincare)} products")
        print(f"💄 Makeup: {len(makeup)} products")

        # Show sample
        if catalog:
            sample = catalog[0]
            print(f"🔍 Sample: {sample.get('name', 'Unknown')} (ID: {sample.get('id', 'No ID')})")

        return True

    except Exception as e:
        print(f"❌ Catalog test failed: {e}")
        traceback.print_exc()
        return False

def test_selector():
    """Тестируем селектор"""
    print("\n🔍 Тестируем селектор...")

    try:
        from engine.models import UserProfile
        from engine.selector import SelectorV2
        from engine.catalog_store import CatalogStore

        # Create test profile
        profile = UserProfile(
            user_id=12345,
            skin_type="normal",
            concerns=["dryness"],
            season="spring",
            undertone="neutral",
            contrast="medium"
        )

        # Load catalog
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()

        # Test selector
        selector = SelectorV2()
        result = selector.select_products_v2(profile, catalog, partner_code="S1")

        print("📦 Selector result keys:"        if result:
            print(f"  {list(result.keys())}")

            if result.get("skincare"):
                for category, products in result["skincare"].items():
                    print(f"  🧴 {category}: {len(products)} products")

            if result.get("makeup"):
                for category, products in result["makeup"].items():
                    print(f"  💄 {category}: {len(products)} products")

        return result is not None

    except Exception as e:
        print(f"❌ Selector test failed: {e}")
        traceback.print_exc()
        return False

def test_cart_operations():
    """Тестируем операции с корзиной"""
    print("\n🔍 Тестируем корзину...")

    try:
        from engine.cart_store import CartStore, CartItem

        store = CartStore()
        user_id = 12345

        # Test add item
        item = CartItem(
            product_id="test_product_001",
            qty=1,
            name="Test Product",
            brand="Test Brand",
            price=1000.0
        )

        store.add_item(user_id, item)
        print("✅ Item added to cart")

        # Test get cart
        cart = store.get_cart(user_id)
        print(f"📦 Cart items: {len(cart)}")

        if cart:
            for key, cart_item in cart.items():
                print(f"  🛒 {cart_item.name} (x{cart_item.qty}) - {cart_item.price}₽")

        # Test clear cart
        store.clear_cart(user_id)
        print("🗑️ Cart cleared")

        return True

    except Exception as e:
        print(f"❌ Cart test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("🔧 ОТЛАДКА ПРОБЛЕМ С КОРЗИНОЙ И ПОКУПКАМИ")
    print("=" * 50)

    tests = [
        ("Импорты", test_imports),
        ("Каталог", test_catalog),
        ("Селектор", test_selector),
        ("Корзина", test_cart_operations)
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'='*20} {name.upper()} {'='*20}")
        try:
            result = test_func()
            results.append(result)
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"\n{status}")
        except Exception as e:
            print(f"\n❌ ТЕСТ ВЫЗВАЛ ОШИБКУ: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ:"    passed = sum(results)
    total = len(results)

    for i, (name, _) in enumerate(tests):
        status = "✅" if results[i] else "❌"
        print(f"  {status} {name}")

    print(f"\n📈 ИТОГО: {passed}/{total} тестов пройдено")

    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
        print("   Проверьте логи выше для диагностики проблем.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
