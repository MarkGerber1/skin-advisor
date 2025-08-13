import asyncio
import logging
import os
import argparse

from aiogram import Bot, Dispatcher, Router
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.handlers import start, survey, results, recommend, admin
from app.infra.db import create_db_if_not_exists
from app.infra.settings import get_settings
from app.infra.middlewares import DBSessionMiddleware
from app.webhook import create_app, make_webhook_url


errors_router = Router()


@errors_router.errors()
async def on_error(event, exception):
	logging.exception("Unhandled error: %s", exception)
	return True


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("--mode", choices=["polling", "webhook"], default=os.getenv("MODE", "polling"))
	return parser.parse_args()


async def main():
	load_dotenv()
	os.makedirs("logs", exist_ok=True)
	logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
	file_handler = logging.FileHandler("logs/bot.log", encoding="utf-8")
	file_handler.setLevel(logging.INFO)
	file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
	logging.getLogger().addHandler(file_handler)

	args = parse_args()
	settings = get_settings()
	logger = logging.getLogger(__name__)

	logger.info("Инициализация базы данных...")
	await create_db_if_not_exists()

	bot = Bot(token=settings.bot.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
	storage = MemoryStorage()
	dp = Dispatcher(storage=storage)
	dp.update.middleware(DBSessionMiddleware())
	dp.include_router(errors_router)
	dp.include_router(start.router)
	dp.include_router(survey.router)
	dp.include_router(results.router)
	dp.include_router(recommend.router)
	dp.include_router(admin.router)

	main_commands = [
		BotCommand(command="/start", description="🚀 Запустить/перезапустить бота"),
		BotCommand(command="/reset", description="🔄 Начать анкету заново"),
		BotCommand(command="/results", description="📊 Показать последний результат"),
		BotCommand(command="/export", description="📄 Скачать отчет в PDF"),
		BotCommand(command="/help", description="❓ Помощь"),
		BotCommand(command="/privacy", description="🔐 Политика конфиденциальности"),
	]
	await bot.set_my_commands(main_commands)

	await bot.delete_webhook(drop_pending_updates=True)

	if args.mode == "webhook":
		logger.info("Запуск в режиме Webhook")
		secret = os.getenv("WEBHOOK_SECRET", "")
		base = os.getenv("WEBHOOK_BASE", "").strip()
		port = int(os.getenv("WEBAPP_PORT", "8080"))
		if not (secret and base):
			raise RuntimeError("WEBHOOK_BASE/WEBHOOK_SECRET не заданы в .env")
		app = create_app(bot, dp, secret, version=os.getenv("APP_VERSION", "dev"))
		runner = web.AppRunner(app)
		await runner.setup()
		site = web.TCPSite(runner, host="0.0.0.0", port=port)
		await site.start()
		url = make_webhook_url(base, secret)
		await bot.set_webhook(url=url)
		logger.info("Вебхук установлен: %s", url)
		await asyncio.Event().wait()
	else:
		logger.info("Запуск в режиме Polling")
		await dp.start_polling(bot)


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except (KeyboardInterrupt, SystemExit):
		logging.info("Бот остановлен.")
