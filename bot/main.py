from __future__ import annotations

import asyncio
import os
import sys

print("Python version:", sys.version)
print("Starting imports...")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")

try:
    from aiogram import Bot, Dispatcher, F

    print("OK aiogram imported")
except ImportError as e:
    print(f"ERROR Failed to import aiogram: {e}")
    raise

try:
    from engine.catalog_store import CatalogStore

    print("OK CatalogStore imported")
except ImportError as e:
    print(f"ERROR Failed to import CatalogStore: {e}")
    raise

# Global bot and dispatcher instances for webhook handling
bot = None
dp = None


def get_bot_and_dispatcher():
    """Get bot and dispatcher instances for webhook handling"""
    global bot, dp
    if bot is None or dp is None:
        raise RuntimeError("Bot and dispatcher not initialized. Call main() first.")
    return bot, dp


# Routers
try:
    from bot.handlers.start import router as start_router

    print("OK start router imported")
except ImportError as e:
    print(f"ERROR Failed to import start router: {e}")
    raise

try:
    from bot.handlers.flow_skincare import router as skincare_router

    print("OK skincare router imported")
except ImportError as e:
    print(f"ERROR Failed to import skincare router: {e}")
    raise

try:
    from bot.handlers.flow_palette import router as palette_router

    print("OK palette router imported")
except ImportError as e:
    print(f"ERROR Failed to import palette router: {e}")
    raise

try:
    from bot.handlers.skincare_picker import router as skincare_picker_router

    print("OK skincare picker router imported")
except ImportError as e:
    print(f"ERROR Failed to import skincare picker router: {e}")
    raise

try:
    from bot.handlers.makeup_picker import router as makeup_picker_router

    print("OK makeup picker router imported")
except ImportError as e:
    print(f"ERROR Failed to import makeup picker router: {e}")
    raise

# LEGACY CART DISABLED - using cart_v2 only
# try:
#     from bot.handlers.cart import router as cart_router
#     print("OK cart router imported")
# except ImportError as e:
#     print(f"ERROR Failed to import cart router: {e}")
#     raise

try:
    from bot.handlers.report import router as report_router

    print("OK report router imported")
except ImportError as e:
    print(f"ERROR Failed to import report router: {e}")
    raise

try:
    from bot.handlers.universal import router as universal_router

    print("OK universal router imported")
except ImportError as e:
    print(f"ERROR Failed to import universal router: {e}")
    raise

try:
    from bot.handlers.detailed_palette import router as detailed_palette_router

    print("OK detailed palette router imported")
except ImportError as e:
    print(f"ERROR Failed to import detailed palette router: {e}")
    raise

try:
    from bot.handlers.detailed_skincare import router as detailed_skincare_router

    print("OK detailed skincare router imported")
except ImportError as e:
    print(f"ERROR Failed to import detailed skincare router: {e}")
    raise

try:
    from bot.handlers.anti_pin_guard import router as anti_pin_guard_router

    print("OK anti-pin guard router imported")
except ImportError as e:
    print(f"ERROR Failed to import anti-pin guard router: {e}")
    raise

try:
    from bot.handlers.admin import router as admin_router

    print("OK admin router imported")
except ImportError as e:
    print(f"ERROR Failed to import admin router: {e}")
    raise

try:
    from bot.handlers.cart_v2 import router as cart_v2_router

    print("OK cart v2 router imported")
except ImportError as e:
    print(f"ERROR Failed to import cart v2 router: {e}")
    raise

try:
    from bot.handlers.recommendations import router as recommendations_router

    print("OK recommendations router imported")
except ImportError as e:
    print(f"ERROR Failed to import recommendations router: {e}")
    raise


CATALOG_PATH = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")


async def main() -> None:
    print("🤖 Bot main() started")
    print(f"📊 BOT_TOKEN: {os.getenv('BOT_TOKEN', 'NOT_SET')[:15]}...")
    print(f"📊 USE_WEBHOOK: {os.getenv('USE_WEBHOOK', 'NOT_SET')}")
    print(f"📊 PORT: {os.getenv('PORT', 'NOT_SET')}")

    # Настройка логирования
    import logging

    # Дефолтные значения - всегда определены
    log_level = "INFO"
    log_file = "logs/bot.log"

    # Пытаемся загрузить настройки из config.env
    try:
        from config.env import get_settings

        settings = get_settings()
        if settings:
            log_level = getattr(settings, "log_level", log_level)
            log_file = getattr(settings, "log_file", log_file)
        print(f"✅ Settings loaded from config.env, log_level: {log_level}")
    except ImportError:
        print("⚠️ Config module not available, using defaults")
    except Exception as e:
        print(f"⚠️ Could not load settings: {e}, using defaults")

    # Гарантируем, что переменные определены
    if not log_level:
        log_level = "INFO"
    if not log_file:
        log_file = "logs/bot.log"

    print(f"🔧 Final config: log_level={log_level}, log_file={log_file}")

    # Создаем папку для логов, если не существует
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Настраиваем основной логгер
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(),  # Вывод в stdout
            logging.FileHandler(log_file, encoding="utf-8"),  # Файловый вывод
        ],
    )

    # Отдельный логгер для ошибок (stderr)
    error_logger = logging.getLogger("errors")
    error_handler = logging.StreamHandler()
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter("%(asctime)s | ERROR | %(name)s | %(message)s")
    error_handler.setFormatter(error_formatter)
    error_logger.addHandler(error_handler)

    print(f"📝 Logging configured: level={log_level}, file={log_file}")

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

    # Загружаем конфигурацию с fallback для Railway
    token = None
    try:
        from config.env import get_settings

        settings = get_settings()
        token = settings.bot_token
        print("✅ Config loaded from config.env")
    except (ImportError, ModuleNotFoundError) as e:
        print(f"⚠️ Config module not found: {e}")
        print("🔄 Falling back to os.getenv...")
        token = os.getenv("BOT_TOKEN")
        if token:
            print("✅ BOT_TOKEN loaded from environment")

    if not token:
        raise RuntimeError("BOT_TOKEN is not set - check environment variables")

    print(f"Starting bot with token: {token[:10]}...")
    print("🤖 Creating Bot instance...")
    global bot
    bot = Bot(token)
    print("✅ Bot instance created")

    print("📡 Creating Dispatcher...")
    global dp
    dp = Dispatcher()
    print("✅ Dispatcher created")

    # Add security middleware for chat filtering
    @dp.message.middleware()
    async def chat_filter_middleware(handler, event, data):
        """Middleware to filter messages based on chat whitelist"""
        from bot.utils.security import chat_filter

        chat_id = event.chat.id

        # Allow all messages if whitelist is empty (backward compatibility)
        if not chat_filter.is_chat_allowed(chat_id):
            print(f"🚫 MESSAGE BLOCKED: Chat {chat_id} not in whitelist")
            # Don't call handler - message is blocked
            return

        # Continue with normal processing
        return await handler(event, data)

    # Add global error handler
    @dp.error()
    async def error_handler(event):
        import traceback

        exception = event.exception
        print(f"❌ Global error: {exception}")
        print(f"📍 Traceback: {traceback.format_exc()}")

        # Log callback data for debugging
        if hasattr(event, "callback_query") and event.callback_query:
            cb = event.callback_query
            print(f"🔗 Callback data: {cb.data}")
            print(f"👤 User: {cb.from_user.id if cb.from_user else 'Unknown'}")
            try:
                # Use inline menu for better recovery (emergency_keyboard may cause same issue)
                from bot.ui.keyboards import main_menu_inline

                if cb.message:
                    await cb.message.edit_text(
                        "⚠️ Произошла ошибка\n\n" "Выберите действие для восстановления:",
                        reply_markup=main_menu_inline(),
                    )
                await cb.answer("⚠️ Ошибка исправлена")
            except Exception as e:
                print(f"❌ Could not handle callback error: {e}")
                try:
                    await cb.answer("⚠️ Ошибка. Нажмите /start")
                except:
                    pass
        elif hasattr(event, "message") and event.message:
            msg = event.message
            print(f"💬 Message text: {msg.text}")
            print(f"👤 User: {msg.from_user.id if msg.from_user else 'Unknown'}")
            try:
                from bot.ui.keyboards import main_menu

                await msg.answer(
                    "⚠️ Произошла ошибка\n\n" "Возврат в главное меню:", reply_markup=main_menu()
                )
            except Exception as e:
                print(f"❌ Could not send error message: {e}")
                try:
                    await msg.answer("⚠️ Ошибка. Нажмите /start")
                except:
                    pass
        return True  # Mark as handled

    # ROUTER PRIORITY ORDER (CRITICAL!)
    dp.include_router(anti_pin_guard_router)  # Security guard - HIGHEST PRIORITY
    dp.include_router(admin_router)  # Admin commands - HIGH PRIORITY
    dp.include_router(cart_v2_router)  # New cart system - HIGH PRIORITY
    dp.include_router(recommendations_router)  # Recommendations - HIGH PRIORITY
    dp.include_router(start_router)  # Side menu handlers - HIGH PRIORITY
    dp.include_router(detailed_palette_router)  # Detailed palette test - BEFORE universal
    dp.include_router(detailed_skincare_router)  # Detailed skincare test - BEFORE universal
    dp.include_router(skincare_picker_router)  # Skincare product picker - AFTER tests
    dp.include_router(makeup_picker_router)  # Makeup product picker - AFTER tests
    dp.include_router(skincare_router)
    dp.include_router(palette_router)
    # LEGACY CART DISABLED
    # dp.include_router(cart_router)
    dp.include_router(report_router)
    dp.include_router(universal_router)  # Universal catch-all - LOWEST PRIORITY

    # Общий обработчик для back:main
    @dp.callback_query(F.data == "back:main")
    async def handle_back_main(cb: CallbackQuery, state: FSMContext):
        """Обработчик возврата в главное меню"""
        from bot.ui.keyboards import main_menu_inline

        # Очищаем состояние
        await state.clear()

        # Показываем главное меню
        await cb.message.edit_text(
            "🏠 **Главное меню**\n\nВыберите действие:",
            reply_markup=main_menu_inline(),
            parse_mode="Markdown",
        )

        await cb.answer()

    # Fallback handler removed - was intercepting all callbacks before routers!

    return  # DISABLED FOR DEBUGGING
    use_webhook = os.getenv("USE_WEBHOOK", "0").lower() in ("1", "true", "yes")
    webhook_url = os.getenv("WEBHOOK_URL")
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")

    if use_webhook and webhook_url:
        print("🌐 Starting in WEBHOOK mode...")
    else:
        print("📡 Starting in POLLING mode...")

        # Проверяем lock-файл для предотвращения конфликта polling
        lock_file = "/tmp/skin-advisor.lock"

        # ULTRA FORCE cleanup for container environments
        print("🧹 ULTRA FORCE cleanup for container environment...")

        # Remove any existing lock files (multiple possible)
        for possible_lock in ["/tmp/skin-advisor.lock", "/tmp/bot.lock", "/tmp/telegram-bot.lock"]:
            if os.path.exists(possible_lock):
                try:
                    os.remove(possible_lock)
                    print(f"🧹 Removed old lock file: {possible_lock}")
                except Exception as e:
                    print(f"⚠️ Could not remove {possible_lock}: {e}")

        # Kill any existing python processes that might be bots (multiple attempts)
        import subprocess
        import time

        for attempt in range(3):
            try:
                # Kill processes by name pattern - more aggressive
                patterns = ["python.*bot.main", "python.*main", "skin-advisor", "telegram.*bot"]

                killed_any = False
                for pattern in patterns:
                    try:
                        result = subprocess.run(
                            ["pkill", "-9", "-f", pattern], timeout=3, capture_output=True
                        )
                        if result.returncode == 0:
                            print(f"🛑 Killed processes matching: {pattern}")
                            killed_any = True
                    except:
                        pass

                if killed_any:
                    print(f"🛑 Killed existing processes (attempt {attempt + 1}/3)")
                    time.sleep(3)  # Longer wait
                else:
                    print("ℹ️ No existing bot processes found")
                    break

            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                print(f"⚠️ Could not check for existing processes (attempt {attempt + 1}): {e}")
                time.sleep(1)

        # Final check - if lock file still exists, it's an error
        if os.path.exists(lock_file):
            print("❌ CRITICAL: Lock file still exists after cleanup!")
            print("💡 This indicates another bot instance is running")
            print("💡 Force removing and continuing...")
            try:
                os.remove(lock_file)
            except:
                pass

        # Создаем новый lock-файл
        try:
            with open(lock_file, "w") as f:
                f.write(str(os.getpid()))
            print(f"✅ Lock file created: {lock_file} (PID: {os.getpid()})")
        except Exception as e:
            print(f"⚠️ Could not create lock file: {e}")
            print("🚨 ВНИМАНИЕ: Продолжаем без lock-файла - возможны конфликты!")

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

            # Удаляем lock-файл
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                    print(f"✅ Lock file removed: {lock_file}")
            except Exception as e:
                print(f"⚠️ Could not remove lock file: {e}")

    # Setup graceful shutdown signal handlers
    shutdown_event = asyncio.Event()

    def signal_handler(signum, frame):
        print(f"📡 Received signal {signum}")
        print("🛑 Starting graceful shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    if use_webhook and webhook_url:
        # WEBHOOK MODE
        print("🌐 Setting up webhook...")
        # Temporarily disabled webhook setup for debugging
        # webhook_full_url = f"{webhook_url.rstrip('/')}{webhook_path}"
        # await bot.set_webhook(
        #     url=webhook_full_url,
        #     drop_pending_updates=True,
        #     allowed_updates=["message", "callback_query", "inline_query"],
        # )
        print("✅ Webhook mode active - Flask will handle HTTP requests")

        # In webhook mode, we don't start our own server
        # Flask handles the /webhook endpoint and feeds updates to the dispatcher
        # Just wait for shutdown signal
        # await shutdown_event.wait()
        pass

    else:
        # POLLING MODE - DISABLED for Render deployment
        print("🚫 Polling mode disabled - webhook only for production")
        print("💡 Use polling only for local development")
        # Polling code removed to avoid syntax errors in production
        pass

    return


if __name__ == "__main__":
    asyncio.run(main())
