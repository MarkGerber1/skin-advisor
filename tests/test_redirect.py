from aiohttp import ClientSession, web
from app.tracking.redirect import create_app


async def _run_app(app):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    return runner, port


async def test_redirect_logs_and_302():
    app = create_app(db_path=":memory:")
    runner, port = await _run_app(app)
    try:
        async with ClientSession() as s:
            r = await s.get(
                f"http://127.0.0.1:{port}/r",
                params={
                    "url": "https://example.com",
                    "subid": "S1",
                    "uid": "123",
                    "pid": "P1",
                },
            )
            assert r.status in (301, 302)
    finally:
        await runner.cleanup()

