from __future__ import annotations

import asyncio
import os
import sys

print("Python version:", sys.version)
print("Starting imports...")

try:
    from aiogram import Bot, Dispatcher

    print("✓ aiogram imported")
except ImportError as e:
    print(f"✗ Failed to import aiogram: {e}")
    raise

try:
    from engine.catalog_store import CatalogStore

    print("✓ CatalogStore imported")
except ImportError as e:
    print(f"✗ Failed to import CatalogStore: {e}")
    raise

# Routers
try:
    from bot.handlers.start import router as start_router

    print("✓ start router imported")
except ImportError as e:
    print(f"✗ Failed to import start router: {e}")
    raise

try:
    from bot.handlers.flow_skincare import router as skincare_router

    print("✓ skincare router imported")
except ImportError as e:
    print(f"✗ Failed to import skincare router: {e}")
    raise

try:
    from bot.handlers.flow_palette import router as palette_router

    print("✓ palette router imported")
except ImportError as e:
    print(f"✗ Failed to import palette router: {e}")
    raise

try:
    from bot.handlers.cart import router as cart_router

    print("✓ cart router imported")
except ImportError as e:
    print(f"✗ Failed to import cart router: {e}")
    raise

try:
    from bot.handlers.report import router as report_router

    print("✓ report router imported")
except ImportError as e:
    print(f"✗ Failed to import report router: {e}")
    raise

try:
    from bot.handlers.universal import router as universal_router

    print("✓ universal router imported")
except ImportError as e:
    print(f"✗ Failed to import universal router: {e}")
    raise

try:
    from bot.handlers.detailed_palette import router as detailed_palette_router

    print("✓ detailed palette router imported")
except ImportError as e:
    print(f"✗ Failed to import detailed palette router: {e}")
    raise

try:
    from bot.handlers.detailed_skincare import router as detailed_skincare_router

    print("✓ detailed skincare router imported")
except ImportError as e:
    print(f"✗ Failed to import detailed skincare router: {e}")
    raise


CATALOG_PATH = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")


async def main() -> None:
    # Preload catalog cache
    print(f"Loading catalog from: {CATALOG_PATH}")
    if not os.path.exists(CATALOG_PATH):
        print(f"WARNING: Catalog file not found at {CATALOG_PATH}")
        print(f"Current directory: {os.getcwd()}")
        print(
            f"Files in assets/: {os.listdir('assets/') if os.path.exists('assets/') else 'assets/ not found'}"
        )

    try:
        CatalogStore.instance(CATALOG_PATH)
        print("Catalog loaded successfully")
    except Exception as e:
        print(f"ERROR loading catalog: {e}")
        # Продолжаем работу даже без каталога

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    print(f"Starting bot with token: {token[:10]}...")
    bot = Bot(token)
    dp = Dispatcher()
    
    # Add global error handler
    @dp.error()
    async def error_handler(event, exception):
        import traceback
        print(f"❌ Global error: {exception}")
        print(f"📍 Traceback: {traceback.format_exc()}")
        
        # Log callback data for debugging
        if hasattr(event, 'callback_query') and event.callback_query:
            cb = event.callback_query
            print(f"🔗 Callback data: {cb.data}")
            print(f"👤 User: {cb.from_user.id if cb.from_user else 'Unknown'}")
            try:
                # Use emergency keyboard for better recovery
                from bot.ui.keyboards import emergency_keyboard
                if cb.message:
                    await cb.message.edit_text(
                        "⚠️ Произошла ошибка\n\n"
                        "Выберите действие для восстановления:",
                        reply_markup=emergency_keyboard()
                    )
                await cb.answer("⚠️ Ошибка исправлена")
            except Exception as e:
                print(f"❌ Could not handle callback error: {e}")
                try:
                    await cb.answer("⚠️ Ошибка. Нажмите /start")
                except:
                    pass
        elif hasattr(event, 'message') and event.message:
            msg = event.message
            print(f"💬 Message text: {msg.text}")
            print(f"👤 User: {msg.from_user.id if msg.from_user else 'Unknown'}")
            try:
                from bot.ui.keyboards import main_menu
                await msg.answer(
                    "⚠️ Произошла ошибка\n\n"
                    "Возврат в главное меню:",
                    reply_markup=main_menu()
                )
            except Exception as e:
                print(f"❌ Could not send error message: {e}")
                try:
                    await msg.answer("⚠️ Ошибка. Нажмите /start")
                except:
                    pass
        return True  # Mark as handled
    
    dp.include_router(universal_router)  # Universal handlers first (highest priority)
    dp.include_router(detailed_palette_router)  # Detailed palette test
    dp.include_router(detailed_skincare_router)  # Detailed skincare test  
    dp.include_router(start_router)
    dp.include_router(skincare_router)
    dp.include_router(palette_router)
    dp.include_router(cart_router)
    dp.include_router(report_router)

    # Fallback handler removed - was intercepting all callbacks before routers!
    
    print("Starting polling...")
    
    # Add graceful shutdown handler
    import signal
    import asyncio
    
    async def graceful_shutdown(bot: Bot):
        print("🛑 Graceful shutdown initiated...")
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook deleted and pending updates dropped")
        except Exception as e:
            print(f"⚠️ Error during shutdown: {e}")
        finally:
            await bot.session.close()
            print("✅ Bot session closed")
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"📡 Received signal {signum}")
        raise KeyboardInterrupt()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Clear any existing webhook first
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            print("🧹 Cleared existing webhook and pending updates")
        except Exception as e:
            print(f"⚠️ Could not clear webhook: {e}")
        
        # Start polling with proper error handling
        await dp.start_polling(
            bot,
            skip_updates=True,  # Skip pending updates to avoid conflicts
            handle_signals=False  # We handle signals manually
        )
    except KeyboardInterrupt:
        print("🛑 Received shutdown signal")
    except Exception as e:
        print(f"❌ Polling error: {e}")
    finally:
        await graceful_shutdown(bot)


if __name__ == "__main__":
    asyncio.run(main())
