import pytest
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher
from app.webhook import create_app


@pytest.mark.asyncio
async def test_web_health_and_version():
    # Use syntactically valid dummy token to satisfy aiogram validation
    bot = Bot(token="123456:TEST")
    dp = Dispatcher()
    app = create_app(bot=bot, dp=dp, secret="testsecret", version="test")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]

    async with ClientSession() as s:
        r1 = await s.get(f"http://127.0.0.1:{port}/healthz")
        assert r1.status == 200
        assert (await r1.text()).lower().strip() in ("ok", "healthy")
        r2 = await s.get(f"http://127.0.0.1:{port}/version")
        assert r2.status == 200
        data = await r2.json()
        assert "version" in data and isinstance(data["version"], str)

    await runner.cleanup()
