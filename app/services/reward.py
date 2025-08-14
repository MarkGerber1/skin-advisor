import os
import time
import sqlite3
from app.infra.migrate import migrate, DEFAULT_DB


def _db_path() -> str:
    return os.getenv("APP_DB", DEFAULT_DB)


def _with_conn(fn):
    def wrapper(*args, **kwargs):
        path = _db_path()
        migrate(path)
        with sqlite3.connect(path) as conn:
            conn.isolation_level = None  # autocommit off via BEGIN
            cur = conn.cursor()
            try:
                cur.execute("BEGIN")
                res = fn(conn, cur, *args, **kwargs)
                cur.execute("COMMIT")
                return res
            except Exception:
                cur.execute("ROLLBACK")
                raise

    return wrapper


@_with_conn
def accrue_loyalty(
    conn, cur, user_id: int, amount: float, order_id: str, rate: float
) -> float:
    points = round(amount * rate, 2)
    # update balance
    cur.execute(
        "INSERT INTO loyalty_balances(user_id,points,updated_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET points = loyalty_balances.points + excluded.points, updated_at=excluded.updated_at",
        (user_id, points, int(time.time())),
    )
    # ledger
    cur.execute(
        "INSERT INTO loyalty_ledger(user_id,delta,reason,order_id,created_at) VALUES(?,?,?,?,?)",
        (user_id, points, "order_approved", order_id, int(time.time())),
    )
    return points


@_with_conn
def accrue_referral(
    conn, cur, referrer_id: int, amount: float, order_id: str, rate: float
) -> float:
    points = round(amount * rate, 2)
    cur.execute(
        "INSERT INTO loyalty_balances(user_id,points,updated_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET points = loyalty_balances.points + excluded.points, updated_at=excluded.updated_at",
        (referrer_id, points, int(time.time())),
    )
    cur.execute(
        "INSERT INTO loyalty_ledger(user_id,delta,reason,order_id,created_at) VALUES(?,?,?,?,?)",
        (referrer_id, points, "referral_bonus", order_id, int(time.time())),
    )
    return points


@_with_conn
def get_balance(conn, cur, user_id: int) -> float:
    cur.execute("SELECT points FROM loyalty_balances WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return float(row[0]) if row else 0.0

