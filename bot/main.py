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
    CatalogStore.instance(CATALOG_PATH)

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(skincare_router)
    dp.include_router(palette_router)
    dp.include_router(cart_router)
    dp.include_router(report_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())





