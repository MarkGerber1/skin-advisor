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
_handlers_registered = False


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


def _ensure_routers_registered() -> None:
    """Include all routers into dispatcher once."""
    global _handlers_registered, dp
    if dp is None or _handlers_registered:
        return
    dp.include_router(anti_pin_guard_router)
    dp.include_router(admin_router)
    dp.include_router(cart_v2_router)
    dp.include_router(recommendations_router)
    dp.include_router(start_router)
    dp.include_router(detailed_palette_router)
    dp.include_router(detailed_skincare_router)
    dp.include_router(skincare_picker_router)
    dp.include_router(makeup_picker_router)
    dp.include_router(skincare_router)
    dp.include_router(palette_router)
    dp.include_router(report_router)
    dp.include_router(universal_router)
    _handlers_registered = True


def get_bot_and_dispatcher():
    """Get bot and dispatcher instances for webhook handling"""
    global bot, dp
    if bot is None or dp is None:
        print("🔄 Initializing bot and dispatcher...")
        try:
            token = os.getenv("BOT_TOKEN")
            if not token:
                from config.env import get_settings

                settings = get_settings()
                token = settings.bot_token

            if not token:
                raise RuntimeError("BOT_TOKEN not found")

            from aiogram import Bot, Dispatcher

            bot = Bot(token)
            dp = Dispatcher()
            print("✅ Bot and dispatcher initialized for webhook handling")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize bot and dispatcher: {e}")

    # Ensure routers are registered for webhook mode
    _ensure_routers_registered()
    return bot, dp


async def main() -> None:
    print("🤖 Bot main() started")
    print(f"📊 BOT_TOKEN: {os.getenv('BOT_TOKEN', 'NOT_SET')[:15]}...")
    print(f"📊 USE_WEBHOOK: {os.getenv('USE_WEBHOOK', 'NOT_SET')}")
    print(f"📊 PORT: {os.getenv('PORT', 'NOT_SET')}")

    import logging

    log_level = "INFO"
    log_file = "logs/bot.log"

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

    if not log_level:
        log_level = "INFO"
    if not log_file:
        log_file = "logs/bot.log"

    print(f"🔧 Final config: log_level={log_level}, log_file={log_file}")

    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )

    from aiogram import Bot, Dispatcher

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

    global bot, dp
    if bot is None:
        bot = Bot(token)
        print("✅ Bot instance created")
    if dp is None:
        dp = Dispatcher()
        print("✅ Dispatcher created")

    # Register routers (order preserved)
    _ensure_routers_registered()

    # Webhook disabled by default; enable only if explicitly set
    use_webhook = os.getenv("USE_WEBHOOK", "0").lower() in ("1", "true", "yes")
    if use_webhook:
        print("🌐 Webhook mode active - do not start polling")
        return

    # Ensure webhook is removed before polling to avoid conflicts
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("🧹 Webhook deleted, pending updates dropped")
    except Exception as e:
        print(f"⚠️ delete_webhook failed: {e}")

    # Start polling for production
    print("📡 Starting polling (Render)")
    await dp.start_polling(
        bot,
        skip_updates=True,
        handle_signals=False,
        timeout=20,
        retry_after=3,
    )


if __name__ == "__main__":
    asyncio.run(main())
