from __future__ import annotations

import asyncio
import os
import sys

print("Python version:", sys.version)
print("Starting imports...")

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

try:
    from bot.handlers.cart import router as cart_router

    print("OK cart router imported")
except ImportError as e:
    print(f"ERROR Failed to import cart router: {e}")
    raise

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


CATALOG_PATH = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")


async def main() -> None:
    # Настройка логирования
    import logging
    import os

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
    bot = Bot(token)
    dp = Dispatcher()

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
    dp.include_router(start_router)  # Side menu handlers - HIGHEST PRIORITY
    dp.include_router(detailed_palette_router)  # Detailed palette test - BEFORE universal
    dp.include_router(detailed_skincare_router)  # Detailed skincare test - BEFORE universal
    dp.include_router(skincare_picker_router)  # Skincare product picker - AFTER tests
    dp.include_router(makeup_picker_router)  # Makeup product picker - AFTER tests
    dp.include_router(skincare_router)
    dp.include_router(palette_router)
    dp.include_router(cart_router)
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

    # Определяем режим работы: webhook или polling
    use_webhook = os.getenv("USE_WEBHOOK", "0").lower() in ("1", "true", "yes")
    webhook_url = os.getenv("WEBHOOK_URL")
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")

    if use_webhook and webhook_url:
        print("🌐 Starting in WEBHOOK mode...")
    else:
        print("📡 Starting in POLLING mode...")

        # Проверяем lock-файл для предотвращения конфликта polling
        lock_file = "/tmp/skin-advisor.lock"

        if os.path.exists(lock_file):
            try:
                with open(lock_file, "r") as f:
                    old_pid = f.read().strip()

                # Проверяем, работает ли еще процесс с этим PID
                if old_pid and os.path.exists(f"/proc/{old_pid}"):
                    print("❌ Другой инстанс бота уже запущен!")
                    print(f"   Running PID: {old_pid}")
                    print(f"   Lock file: {lock_file}")
                    print("💡 Решение: остановите другой процесс или удалите lock-файл")
                    return
                else:
                    print(f"⚠️ Найден устаревший lock-файл от PID {old_pid}, удаляем...")
                    os.remove(lock_file)
            except Exception as e:
                print(f"⚠️ Ошибка при проверке lock-файла: {e}")
                # Пытаемся удалить поврежденный файл
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
            print("🚨 ВНИМАНИЕ: Возможны конфликты при одновременном запуске нескольких инстансов!")

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

    try:
        # Clear any existing webhook first and wait for conflicts to resolve
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            print("🧹 Cleared existing webhook and pending updates")

            # Wait for Telegram to process webhook deletion
            import asyncio

            await asyncio.sleep(2)

            # Test connection before starting polling
            me = await bot.get_me()
            print(f"✅ Bot connection verified: @{me.username} (ID: {me.id})")

        except Exception as e:
            print(f"⚠️ Could not clear webhook: {e}")

        if use_webhook and webhook_url:
            # WEBHOOK MODE
            print("🌐 Setting up webhook...")
            webhook_full_url = f"{webhook_url.rstrip('/')}{webhook_path}"

            # Set webhook
            await bot.set_webhook(
                url=webhook_full_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query", "inline_query"],
            )
            print(f"✅ Webhook set to: {webhook_full_url}")

            # Start webhook server (simple aiohttp)
            from aiohttp import web
            from aiohttp.web import Request

            app = web.Application()

            async def telegram_webhook(request: Request):
                """Handle Telegram webhook"""
                try:
                    update_data = await request.json()
                    update = types.Update(**update_data)
                    await dp.feed_update(bot, update)
                    return web.Response(text="OK")
                except Exception as e:
                    print(f"❌ Webhook error: {e}")
                    return web.Response(text="ERROR", status=500)

            app.router.add_post(webhook_path, telegram_webhook)

            # Start server
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
            await site.start()
            print("🌐 Webhook server started")

            # Wait for shutdown
            await shutdown_event.wait()

        else:
            # POLLING MODE
            # Start polling with conflict resolution
            print("🚀 Starting polling...")
            await dp.start_polling(
                bot,
                skip_updates=True,  # Skip pending updates to avoid conflicts
                handle_signals=False,  # We handle signals manually
                timeout=20,  # Shorter timeout to detect conflicts faster
                retry_after=3,  # Shorter retry delay
            )
    except KeyboardInterrupt:
        print("🛑 Received shutdown signal")
    except Exception as e:
        error_msg = str(e).lower()
        if "conflict" in error_msg or "getUpdates" in str(e):
            print(f"🚫 BOT CONFLICT DETECTED: {e}")
            print("🔍 Possible causes:")
            print("  • Another bot instance is running (Railway + Local)")
            print("  • Previous bot didn't shutdown cleanly")
            print("  • Webhook still active somewhere")
            print("💡 Solutions:")
            print("  • Stop other bot instances")
            print("  • Wait 2-3 minutes for Telegram timeout")
            print("  • Check Railway logs for duplicate deployments")
        else:
            print(f"❌ Polling error: {e}")
    finally:
        await graceful_shutdown(bot)


if __name__ == "__main__":
    asyncio.run(main())
