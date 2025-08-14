import os
import hmac
import time
import sqlite3
from hashlib import sha256
from typing import Dict, Any
from aiohttp import web
from app.infra.migrate import migrate, DEFAULT_DB
from app.services.reward import accrue_loyalty


def _validate_signature(params: Dict[str, Any], secret: str) -> bool:
    if not secret:
        return True
    sig = params.get("signature")
    if not sig:
        return False
    # Build canonical string without signature
    items = [(k, v) for k, v in params.items() if k != "signature"]
    items.sort(key=lambda x: x[0])
    payload = "&".join(f"{k}={v}" for k, v in items)
    expected = hmac.new(secret.encode(), payload.encode(), sha256).hexdigest()
    return hmac.compare_digest(sig, expected)


async def handle_postback(request: web.Request) -> web.Response:
    if request.method == "POST":
        data = await request.post()
        params = {k: v for k, v in data.items()}
    else:
        params = dict(request.query)

    secret = os.getenv("POSTBACK_SECRET", "")
    if not _validate_signature(params, secret):
        return web.Response(status=403, text="bad signature")

    click_id = params.get("click_id") or params.get("subid")
    order_id = params.get("order_id")
    status = params.get("status", "pending")
    amount = float(params.get("amount", 0.0))
    user_id = None

    db_path = os.getenv("APP_DB", DEFAULT_DB)
    migrate(db_path)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        # try resolve user by click
        if click_id:
            cur.execute(
                "SELECT user_id FROM clicks WHERE click_id=? ORDER BY id DESC LIMIT 1",
                (click_id,),
            )
            row = cur.fetchone()
            if row and row[0]:
                user_id = int(row[0])
        # upsert order
        cur.execute(
            "INSERT INTO orders(order_id,click_id,user_id,amount,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET status=excluded.status, amount=excluded.amount, updated_at=excluded.updated_at",
            (
                order_id,
                click_id,
                user_id,
                amount,
                status,
                int(time.time()),
                int(time.time()),
            ),
        )
        conn.commit()

    # accrue loyalty for approved
    if status == "approved" and user_id:
        rate = float(os.getenv("LOYALTY_RATE", "0.05"))
        await accrue_loyalty(
            user_id=user_id, amount=amount, order_id=order_id, rate=rate
        )

    return web.Response(text="ok")


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/postback", handle_postback)
    app.router.add_post("/postback", handle_postback)
    return app


def main():
    from aiohttp import web
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8082)
    args = parser.parse_args()
    web.run_app(create_app(), host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()

