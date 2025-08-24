from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class CartItem:
    product_id: str
    qty: int = 1
    brand: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    price_currency: Optional[str] = None


class CartStore:
    """Персистентная корзина на файлах JSON (изолирована по user_id)."""

    def __init__(self, base_dir: str = "data/carts"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, user_id: int) -> str:
        return os.path.join(self.base_dir, f"{user_id}.json")

    def _load(self, user_id: int) -> Dict[str, CartItem]:
        path = self._path(user_id)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            raw: Dict[str, Dict] = json.load(f) or {}
        out: Dict[str, CartItem] = {}
        for pid, payload in raw.items():
            out[pid] = CartItem(**payload)
        return out

    def _save(self, user_id: int, items: Dict[str, CartItem]) -> None:
        path = self._path(user_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {pid: asdict(ci) for pid, ci in items.items()}, f, ensure_ascii=False, indent=2
            )

    def add(self, user_id: int, item: CartItem) -> None:
        with self._lock:
            items = self._load(user_id)
            if item.product_id in items:
                items[item.product_id].qty += item.qty
            else:
                items[item.product_id] = item
            self._save(user_id, items)

    def remove(self, user_id: int, product_id: str) -> None:
        with self._lock:
            items = self._load(user_id)
            if product_id in items:
                del items[product_id]
                self._save(user_id, items)

    def set_qty(self, user_id: int, product_id: str, qty: int) -> None:
        if qty <= 0:
            self.remove(user_id, product_id)
            return
        with self._lock:
            items = self._load(user_id)
            if product_id in items:
                items[product_id].qty = qty
                self._save(user_id, items)

    def clear(self, user_id: int) -> None:
        with self._lock:
            path = self._path(user_id)
            if os.path.exists(path):
                os.remove(path)

    def get(self, user_id: int) -> List[CartItem]:
        with self._lock:
            return list(self._load(user_id).values())
