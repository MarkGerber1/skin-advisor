"""
Unified Cart Store Service
Обновлённый слой данных корзины: qty/quantity синхронизированы,
поддержка источников, undo и аналитики.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CartItem:
    """Позиция в корзине."""

    product_id: str
    variant_id: Optional[str] = None
    qty: int = 1
    brand: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    currency: str = "RUB"
    price_currency: str = "RUB"
    ref_link: Optional[str] = None
    category: Optional[str] = None
    variant_name: Optional[str] = None
    in_stock: bool = True
    image_url: Optional[str] = None
    source: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    quantity: Optional[int] = None  # legacy alias

    def __post_init__(self) -> None:
        canonical_qty = self.quantity if self.quantity is not None else self.qty
        try:
            canonical_qty = max(0, int(canonical_qty))
        except (TypeError, ValueError):
            canonical_qty = 0
        self.set_qty(canonical_qty)

        if self.price is not None:
            try:
                self.price = float(self.price)
            except (TypeError, ValueError):
                self.price = None

        if not isinstance(self.meta, dict):
            self.meta = {}

    def set_qty(self, value: int, *, max_qty: int = 99) -> None:
        value = max(0, min(int(value), max_qty))
        self.qty = value
        self.quantity = value

    def increase(self, delta: int = 1, *, max_qty: int = 99) -> int:
        self.set_qty(self.qty + delta, max_qty=max_qty)
        return self.qty

    def decrease(self, delta: int = 1) -> int:
        self.set_qty(self.qty - delta)
        return self.qty

    def get_key(self) -> str:
        variant_part = self.variant_id or "default"
        return f"{self.product_id}:{variant_part}"


class CartStore:
    """Потокобезопасное файловое хранилище корзины."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "CartStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self.data_dir = Path("data/carts")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._carts: Dict[int, List[CartItem]] = {}
        self._load_all_carts()

    def _get_cart_file(self, user_id: int) -> Path:
        return self.data_dir / f"cart_{user_id}.json"

    def _load_cart(self, user_id: int) -> List[CartItem]:
        cart_file = self._get_cart_file(user_id)
        if not cart_file.exists():
            return []

        try:
            with cart_file.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except Exception as exc:  # pragma: no cover
            print(f"Error loading cart for user {user_id}: {exc}")
            return []

        items: List[CartItem] = []
        for payload in raw.get("items", []):
            try:
                items.append(CartItem(**payload))
            except TypeError as exc:
                print(f"Error constructing CartItem for user {user_id}: {exc}")
        return items

    def _save_cart(self, user_id: int, items: List[CartItem]) -> None:
        cart_file = self._get_cart_file(user_id)
        for item in items:
            item.set_qty(item.qty)
        try:
            data = {"user_id": user_id, "items": [asdict(item) for item in items]}
            with cart_file.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2, default=str)
        except Exception as exc:  # pragma: no cover
            print(f"Error saving cart for user {user_id}: {exc}")

    def _load_all_carts(self) -> None:
        if not self.data_dir.exists():
            return

        for cart_file in self.data_dir.glob("cart_*.json"):
            try:
                user_id = int(cart_file.stem.split("_")[1])
            except (IndexError, ValueError):
                continue
            self._carts[user_id] = self._load_cart(user_id)

    def get_cart(self, user_id: int) -> List[CartItem]:
        if user_id not in self._carts:
            self._carts[user_id] = self._load_cart(user_id)
        return self._carts[user_id]

    def add_item(
        self,
        user_id: int,
        product_id: str,
        variant_id: Optional[str] = None,
        quantity: int = 1,
        **kwargs: Any,
    ) -> CartItem:
        cart = self.get_cart(user_id)
        quantity = int(quantity or 0) if quantity is not None else 0
        if quantity <= 0:
            quantity = 1

        for item in cart:
            if item.product_id == product_id and item.variant_id == (variant_id or None):
                item.increase(quantity)
                self._save_cart(user_id, cart)
                return item

        new_item = CartItem(
            product_id=product_id,
            variant_id=variant_id,
            qty=quantity,
            quantity=quantity,
            **kwargs,
        )
        cart.append(new_item)
        self._save_cart(user_id, cart)
        return new_item

    def update_quantity(
        self, user_id: int, product_id: str, variant_id: Optional[str], new_quantity: int
    ) -> bool:
        cart = self.get_cart(user_id)
        for item in cart:
            if item.product_id == product_id and item.variant_id == variant_id:
                if new_quantity <= 0:
                    cart.remove(item)
                else:
                    item.set_qty(new_quantity)
                self._save_cart(user_id, cart)
                return True
        return False

    def remove_item(self, user_id: int, product_id: str, variant_id: Optional[str]) -> Optional[CartItem]:
        cart = self.get_cart(user_id)
        for item in list(cart):
            if item.product_id == product_id and item.variant_id == variant_id:
                cart.remove(item)
                self._save_cart(user_id, cart)
                return item
        return None

    def inc_quantity(
        self, user_id: int, product_id: str, variant_id: Optional[str], max_qty: int = 10
    ) -> Tuple[bool, int]:
        cart = self.get_cart(user_id)
        for item in cart:
            if item.product_id == product_id and item.variant_id == variant_id:
                old_qty = item.qty
                new_qty = item.increase(1, max_qty=max_qty)
                if new_qty != old_qty:
                    self._save_cart(user_id, cart)
                return True, new_qty
        return False, 0

    def dec_quantity(
        self, user_id: int, product_id: str, variant_id: Optional[str]
    ) -> Tuple[bool, int, Optional[CartItem]]:
        cart = self.get_cart(user_id)
        for item in list(cart):
            if item.product_id == product_id and item.variant_id == variant_id:
                if item.qty <= 1:
                    cart.remove(item)
                    self._save_cart(user_id, cart)
                    return True, 0, item
                new_qty = item.decrease(1)
                self._save_cart(user_id, cart)
                return True, new_qty, None
        return False, 0, None

    def clear_cart(self, user_id: int) -> int:
        if user_id in self._carts:
            removed = len(self._carts[user_id])
            self._carts[user_id] = []
            self._save_cart(user_id, [])
            return removed
        return 0

    def get_cart_count(self, user_id: int) -> int:
        cart = self.get_cart(user_id)
        return sum(item.qty for item in cart)

    def get_cart_total(self, user_id: int) -> Tuple[int, float, str]:
        cart = self.get_cart(user_id)
        total_qty = 0
        total_price = 0.0
        currency = "RUB"
        for item in cart:
            total_qty += item.qty
            if item.price is not None:
                total_price += item.price * item.qty
                currency = item.currency or currency
        return total_qty, total_price, currency

    def list_all_carts(self) -> Dict[int, List[CartItem]]:
        self._load_all_carts()
        return {user_id: items.copy() for user_id, items in self._carts.items()}

    def get_cart_summary(self, user_id: int) -> Dict[str, Any]:
        cart = self.get_cart(user_id)
        total_qty, total_price, currency = self.get_cart_total(user_id)
        return {
            "user_id": user_id,
            "items_count": len(cart),
            "total_quantity": total_qty,
            "total_price": total_price,
            "currency": currency,
            "items": [asdict(item) for item in cart],
        }


_cart_store_instance: Optional[CartStore] = None


def get_cart_store() -> CartStore:
    global _cart_store_instance
    if _cart_store_instance is None:
        _cart_store_instance = CartStore()
    return _cart_store_instance
