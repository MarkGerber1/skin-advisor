import os
import time
import sqlite3
from urllib.parse import urlparse
from aiohttp import web
from app.infra.migrate import migrate, DEFAULT_DB


def _get_db(path: str):
    migrate(path)
    conn = sqlite3.connect(path)
    return conn


async def handle_redirect(request: web.Request) -> web.Response:
    url = request.query.get("url")
    if not url:
        return web.Response(status=400, text="missing url")
    # sanitize
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        return web.Response(status=400, text="bad url")
    subid = request.query.get("subid")
    uid = request.query.get("uid")
    pid = request.query.get("pid")
    click_id = request.query.get("click_id") or subid
    ua = request.headers.get("User-Agent", "")
    ip = request.headers.get("X-Forwarded-For") or request.remote

    db_path = os.getenv("APP_DB", DEFAULT_DB)
    with _get_db(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO clicks (click_id,user_id,product_id,subid,url,ua,ip,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                click_id,
                int(uid) if (uid and uid.isdigit()) else None,
                pid,
                subid,
                url,
                ua,
                ip,
                int(time.time()),
            ),
        )
        conn.commit()
    return web.HTTPFound(location=url)


def create_app(db_path: str | None = None) -> web.Application:
    if db_path:
        os.environ["APP_DB"] = db_path
    app = web.Application()
    app.router.add_get("/r", handle_redirect)
    return app


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
