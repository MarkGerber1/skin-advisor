from __future__ import annotations

import asyncio
import os
from aiogram import Bot, Dispatcher

from engine.catalog_store import CatalogStore

# Routers
from bot.handlers.start import router as start_router
from bot.handlers.flow_skincare import router as skincare_router
from bot.handlers.flow_palette import router as palette_router
from bot.handlers.cart import router as cart_router
from bot.handlers.report import router as report_router


CATALOG_PATH = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")


async def main() -> None:
    # Preload catalog cache
    print(f"Loading catalog from: {CATALOG_PATH}")
    if not os.path.exists(CATALOG_PATH):
        print(f"WARNING: Catalog file not found at {CATALOG_PATH}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Files in assets/: {os.listdir('assets/') if os.path.exists('assets/') else 'assets/ not found'}")
    
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





