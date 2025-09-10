#!/usr/bin/env python3
"""
Исправленный скрипт запуска бота
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Запуск бота с исправлениями"""
    print("🚀 Запуск бота с исправлениями...")
    print("🔧 Исправлены:")
    print("   ✅ CartStore.get() → CartStore.get_cart()")
    print("   ✅ CatalogStore проверки на None")
    print("   ✅ InlineKeyboardButton конфликт импортов")
    print("   ✅ CartItem добавлено поле price_currency")
    print("")

    try:
        from bot.main import main as bot_main
        import asyncio

        # Запускаем бота
        asyncio.run(bot_main())

    except KeyboardInterrupt:
        print("\n⏹️  Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
