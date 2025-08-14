import os
import logging
from typing import Optional
from aiohttp import web
from app.tracking.redirect import handle_redirect
from app.infra.migrate import migrate, DEFAULT_DB
from aiogram import Bot, Dispatcher
from aiogram.types import Update

logger = logging.getLogger(__name__)


def healthz_text() -> str:
    return "ok"


def make_webhook_url(base: str, secret: str) -> str:
    return f"{base.rstrip('/')}/tg/{secret}"


def create_app(
    bot: Bot, dp: Dispatcher, secret: str, version: Optional[str] = None
) -> web.Application:
    # Ensure DB migrations for click/order tables
    try:
        migrate(DEFAULT_DB)
    except Exception as e:
        logger.warning("migrate failed: %s", e)
    app = web.Application()

    async def handle_healthz(request: web.Request) -> web.Response:
        return web.Response(text=healthz_text())

    async def handle_root(request: web.Request) -> web.Response:
        return web.Response(text="ok")

    async def handle_favicon(request: web.Request) -> web.Response:
        return web.Response(status=204)

    async def handle_version(request: web.Request) -> web.Response:
        return web.json_response(
            {"version": version or os.getenv("APP_VERSION", "dev")}
        )

    async def handle_update(request: web.Request) -> web.Response:
        # Validate secret in path
        path_secret = request.match_info.get("secret")
        if path_secret != secret:
            return web.Response(status=403, text="forbidden")
        try:
            if request.can_read_body:
                payload = await request.json()
            else:
                payload = {}
            update = Update.model_validate(payload)
            await dp.feed_update(bot, update)
            # Basic log
            try:
                uid = getattr(update, "update_id", None)
                logger.info("webhook update accepted: %s", uid)
            except Exception:
                pass
            return web.Response(text="ok")
        except Exception as e:
            logger.exception("webhook error: %s", e)
            return web.Response(status=500, text="error")

    app.router.add_get("/healthz", handle_healthz)
    app.router.add_get("/", handle_root)
    app.router.add_get("/favicon.ico", handle_favicon)
    app.router.add_get("/version", handle_version)
    app.router.add_post("/tg/{secret}", handle_update)
    # Redirect tracker
    app.router.add_get("/r", handle_redirect)
    return app

