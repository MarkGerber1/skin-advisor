import os
import time
import uuid
import sqlite3
from typing import Optional
from app.infra.migrate import migrate, DEFAULT_DB

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _b62(n: int) -> str:
    if n == 0:
        return ALPHABET[0]
    s = []
    base = len(ALPHABET)
    while n:
        n, r = divmod(n, base)
        s.append(ALPHABET[r])
    return "".join(reversed(s))


def _db_path():
    return os.getenv("APP_DB", DEFAULT_DB)


def get_or_create_code(user_id: int) -> str:
    path = _db_path()
    migrate(path)
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT code FROM referral_links WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if row and row[0]:
            return row[0]
        code = f"{_b62(user_id)}{uuid.uuid4().hex[:6]}"
        cur.execute(
            "INSERT OR REPLACE INTO referral_links(user_id,code,created_at) VALUES(?,?,?)",
            (user_id, code, int(time.time())),
        )
        conn.commit()
        return code


def resolve_referrer(code: str) -> Optional[int]:
    path = _db_path()
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM referral_links WHERE code=?", (code,))
        row = cur.fetchone()
        return int(row[0]) if row else None

