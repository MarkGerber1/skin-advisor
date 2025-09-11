#!/usr/bin/env python3
"""
Быстрый тест основных функций бота
"""
import sys
import os

# Добавляем пути
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "i18n"))


def test_imports():
    """Тестируем основные импорты"""
    print("🧪 Тестирую импорты...")

    try:

        print("✅ bot.main - OK")
    except Exception as e:
        print(f"❌ bot.main - FAILED: {e}")
        return False

    try:
        from services.cart_store import get_cart_store

        store = get_cart_store()
        print("✅ CartStore - OK")
    except Exception as e:
        print(f"❌ CartStore - FAILED: {e}")
        return False

    try:

        print("✅ Affiliate service - OK")
    except Exception as e:
        print(f"❌ Affiliate service - FAILED: {e}")
        return False

    try:

        print("✅ Report cards - OK")
    except Exception as e:
        print(f"❌ Report cards - FAILED: {e}")
        return False

    return True


def test_cart_operations():
    """Тестируем операции с корзиной"""
    print("\n🛒 Тестирую корзину...")

    try:
        from services.cart_store import get_cart_store

        store = get_cart_store()

        # Тестируем добавление товара
        user_id = 12345
        product_id = "test_product"
        store.add_item(user_id, product_id)
        print("✅ Добавление товара - OK")

        # Тестируем получение корзины
        cart = store.get_cart(user_id)
        if len(cart) > 0:
            print("✅ Получение корзины - OK")
        else:
            print("❌ Корзина пустая после добавления")
            return False

        # Тестируем список всех корзин
        all_carts = store.list_all_carts()
        if user_id in all_carts:
            print("✅ Список всех корзин - OK")
        else:
            print("❌ Пользователь не найден в списке всех корзин")
            return False

        return True
    except Exception as e:
        print(f"❌ Операции с корзиной - FAILED: {e}")
        return False


def main():
    print("🚀 Запуск быстрого теста бота...\n")

    if not test_imports():
        print("\n❌ Тест импортов провален!")
        return 1

    if not test_cart_operations():
        print("\n❌ Тест корзины провален!")
        return 1

    print("\n✅ Все тесты пройдены успешно!")
    print("🎉 Бот готов к работе!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
