#!/usr/bin/env python3
"""
Простой тест статуса бота
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Тестируем все основные импорты"""
    print("🔍 Тестируем импорты бота...")

    try:
        from config.env import get_settings
        print("✅ config.env - OK")
    except Exception as e:
        print(f"❌ config.env - ERROR: {e}")
        return False

    try:
        from services.cart_store import CartStore, get_cart_store
        print("✅ cart_store - OK")
    except Exception as e:
        print(f"❌ cart_store - ERROR: {e}")
        return False

    try:
        from bot.main import main
        print("✅ bot.main - OK")
    except Exception as e:
        print(f"❌ bot.main - ERROR: {e}")
        return False

    try:
        from bot.handlers.cart import router as cart_router
        print("✅ cart handlers - OK")
    except Exception as e:
        print(f"❌ cart handlers - ERROR: {e}")
        return False

    return True

def test_cart_functionality():
    """Тестируем функциональность корзины"""
    print("\n🛒 Тестируем корзину...")

    try:
        from services.cart_store import CartStore
        cart = CartStore()

        # Тестируем создание корзины
        cart.add_to_cart("123", "test_product", "variant1", "Test Product", 100.0)
        print("✅ Добавление товара - OK")

        # Проверяем количество
        count = cart.get_cart_count("123")
        if count == 1:
            print("✅ Подсчет товаров - OK")
        else:
            print(f"❌ Подсчет товаров - ERROR: ожидали 1, получили {count}")
            return False

        # Проверяем содержимое
        cart_items = cart.get_cart_items("123")
        if len(cart_items) == 1:
            print("✅ Получение товаров - OK")
        else:
            print(f"❌ Получение товаров - ERROR: ожидали 1, получили {len(cart_items)}")
            return False

        # Тестируем удаление
        cart.remove_from_cart("123", "test_product", "variant1")
        count = cart.get_cart_count("123")
        if count == 0:
            print("✅ Удаление товара - OK")
        else:
            print(f"❌ Удаление товара - ERROR: корзина не пуста, {count} товаров")
            return False

        return True

    except Exception as e:
        print(f"❌ Ошибка в корзине: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция теста"""
    print("🚀 Запуск комплексного теста бота")
    print("=" * 50)

    # Тест 1: Импорты
    imports_ok = test_imports()
    if not imports_ok:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Проблемы с импортами!")
        return False

    # Тест 2: Корзина
    cart_ok = test_cart_functionality()
    if not cart_ok:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Проблемы с корзиной!")
        return False

    print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    print("✅ Бот готов к работе!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
