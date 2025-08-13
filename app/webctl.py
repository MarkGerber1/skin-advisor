import os
import asyncio
from aiogram import Bot
from app.webhook import make_webhook_url


async def _set():
	token = os.getenv("BOT_TOKEN")
	base = os.getenv("WEBHOOK_BASE", "").strip()
	secret = os.getenv("WEBHOOK_SECRET", "")
	if not token or not base or not secret:
		print("Missing BOT_TOKEN/WEBHOOK_BASE/WEBHOOK_SECRET")
		return
	bot = Bot(token=token)
	url = make_webhook_url(base, secret)
	await bot.set_webhook(url=url)
	print(f"setWebhook: {url}")


async def _info():
	bot = Bot(token=os.getenv("BOT_TOKEN"))
	info = await bot.get_webhook_info()
	print(info.model_dump_json(indent=2))


async def _delete():
	bot = Bot(token=os.getenv("BOT_TOKEN"))
	ok = await bot.delete_webhook(drop_pending_updates=True)
	print(f"deleteWebhook: {ok}")


def main():
	import sys
	cmd = sys.argv[1] if len(sys.argv) > 1 else ""
	if cmd == "set":
		asyncio.run(_set())
	elif cmd == "info":
		asyncio.run(_info())
	elif cmd == "delete":
		asyncio.run(_delete())
	else:
		print("Usage: python -m app.webctl [set|info|delete]")


if __name__ == "__main__":
	main()
