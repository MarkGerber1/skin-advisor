import os
import sqlite3
from typing import Optional


DEFAULT_DB = os.path.join("data", "app.db")


DDL = [
    """
	CREATE TABLE IF NOT EXISTS clicks (
		id INTEGER PRIMARY KEY,
		click_id TEXT,
		user_id INTEGER,
		product_id TEXT,
		subid TEXT,
		url TEXT,
		ua TEXT,
		ip TEXT,
		created_at INTEGER
	);
	""",
    """
	CREATE TABLE IF NOT EXISTS orders (
		id INTEGER PRIMARY KEY,
		order_id TEXT UNIQUE,
		click_id TEXT,
		user_id INTEGER,
		amount REAL,
		status TEXT,
		created_at INTEGER,
		updated_at INTEGER
	);
	""",
    """
	CREATE TABLE IF NOT EXISTS referral_links (
		user_id INTEGER PRIMARY KEY,
		code TEXT UNIQUE,
		created_at INTEGER
	);
	""",
    """
	CREATE TABLE IF NOT EXISTS referral_events (
		id INTEGER PRIMARY KEY,
		referrer_id INTEGER,
		referred_id INTEGER,
		click_id TEXT,
		created_at INTEGER
	);
	""",
    """
	CREATE TABLE IF NOT EXISTS loyalty_balances (
		user_id INTEGER PRIMARY KEY,
		points REAL DEFAULT 0.0,
		updated_at INTEGER
	);
	""",
    """
	CREATE TABLE IF NOT EXISTS loyalty_ledger (
		id INTEGER PRIMARY KEY,
		user_id INTEGER,
		delta REAL,
		reason TEXT,
		order_id TEXT,
		created_at INTEGER
	);
	""",
]


def migrate(db_path: Optional[str] = None) -> str:
    path = db_path or DEFAULT_DB
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        for stmt in DDL:
            cur.execute(stmt)
        conn.commit()
    return path

