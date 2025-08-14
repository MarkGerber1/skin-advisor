import asyncio
import logging
import os
import argparse

from aiogram import Bot, Dispatcher, Router
from aiogram.types import BotCommand
from aiohttp import web
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.handlers import start, survey, results, recommend, admin
from app.handlers import menu as menu_handlers
from app.infra.db import create_db_if_not_exists
from app.infra.migrate import migrate, DEFAULT_DB
from app.infra.settings import get_settings
from app.infra.middlewares import DBSessionMiddleware
from app.webhook import create_app, make_webhook_url


errors_router = Router()


@errors_router.errors()
async def on_error(event, exception=None):
    # Log any unhandled error without breaking due to signature changes
    logging.exception("Unhandled error", exc_info=True)
    return True


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=["polling", "webhook"], default=os.getenv("MODE", "polling")
    )
    return parser.parse_args()


async def main():
    load_dotenv()
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    file_handler = logging.FileHandler("logs/bot.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logging.getLogger().addHandler(file_handler)

    args = parse_args()
    settings = get_settings()
    logger = logging.getLogger(__name__)

    logger.info("boot: init-db")
    await create_db_if_not_exists()
    # Ensure raw SQLite tables for tracking/loyalty exist
    migrate(DEFAULT_DB)

    bot = Bot(
        token=settings.bot.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.update.middleware(DBSessionMiddleware())
    dp.include_router(errors_router)
    dp.include_router(start.router)
    dp.include_router(survey.router)
    dp.include_router(results.router)
    dp.include_router(recommend.router)
    dp.include_router(admin.router)
    dp.include_router(menu_handlers.router)

    main_commands = [
        BotCommand(command="/start", description="🚀 Запустить/перезапустить бота"),
        BotCommand(command="/reset", description="🔄 Начать анкету заново"),
        BotCommand(command="/results", description="📊 Показать последний результат"),
        BotCommand(command="/export", description="📄 Скачать отчет в PDF"),
        BotCommand(command="/help", description="❓ Помощь"),
        BotCommand(command="/privacy", description="🔐 Политика конфиденциальности"),
    ]
    await bot.set_my_commands(main_commands)

    try:
        # Do not drop webhook in webhook mode to avoid race during restarts on PaaS
        if os.getenv("MODE", args.mode) != "webhook":
            await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass

    logger.info(
        "boot: mode=%s env=%s",
        args.mode,
        {
            "WEBAPP_PORT": os.getenv("WEBAPP_PORT"),
            "DEEPLINK_NETWORK": os.getenv("DEEPLINK_NETWORK"),
        },
    )
    if args.mode == "webhook":
        logger.info("Запуск в режиме Webhook")
        secret = os.getenv("WEBHOOK_SECRET", "").strip()
        # Respect Railway PORT, fallback to WEBAPP_PORT
        port = int(os.getenv("PORT", os.getenv("WEBAPP_PORT", "8080")))

        # Determine webhook base: prefer WEBHOOK_BASE; else try Railway domain
        base = os.getenv("WEBHOOK_BASE", "").strip()
        if not base:
            railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
            railway_static = os.getenv("RAILWAY_STATIC_URL", "").strip()
            if railway_domain:
                base = f"https://{railway_domain}"
            elif railway_static:
                base = railway_static if railway_static.startswith("http") else f"https://{railway_static}"

        # Fallback redirect base: if empty and we know the base
        redirect_base = os.getenv("REDIRECT_BASE", "").strip()
        if not redirect_base and base:
            redirect_base = f"{base.rstrip('/')}/r"
            os.environ["REDIRECT_BASE"] = redirect_base

        logger.info(
            "boot: mode=webhook port=%s webhook_base=%s redirect_base=%s",
            port,
            base or "",
            redirect_base or "",
        )

        if not (secret and base):
            raise RuntimeError("WEBHOOK_BASE/WEBHOOK_SECRET не заданы и Railway-домен не найден")
        app = create_app(bot, dp, secret, version=os.getenv("APP_VERSION", "dev"))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=port)
        await site.start()
        url = make_webhook_url(base, secret)
        try:
            await bot.set_webhook(url=url)
            logger.info("webhook: set ok url=%s", url)
        except Exception as e:
            logger.warning("webhook: set failed err=%s url=%s", e, url)
        await asyncio.Event().wait()
    else:
        logger.info("Запуск в режиме Polling")
        await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
