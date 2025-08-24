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
    dp.include_router(start_router)
    dp.include_router(skincare_router)
    dp.include_router(palette_router)
    dp.include_router(cart_router)
    dp.include_router(report_router)

    print("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
