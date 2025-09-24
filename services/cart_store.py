"""
Unified Cart Store Service
Handles cart persistence and quantity operations.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time


@dataclass
class CartItem:
    """Single cart item representation."""

    product_id: str
    variant_id: Optional[str] = None
    name: str = ""
    variant_name: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    currency: str = "RUB"
    ref_link: Optional[str] = None
    image_url: Optional[str] = None
    in_stock: bool = True
    source: Optional[str] = None
    quantity: int = 1
    meta: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            self.quantity = max(int(self.quantity), 0)
        except (TypeError, ValueError):
            self.quantity = 0

        if self.price is not None:
            try:
                self.price = float(self.price)
            except (TypeError, ValueError):
                self.price = None

    @property
    def key(self) -> str:
        variant = self.variant_id or "default"
        return f"{self.product_id}:{variant}"

    @property
    def qty(self) -> int:
        """Alias for quantity - always synchronized"""
        return self.quantity

    @qty.setter
    def qty(self, value: int) -> None:
        """Setter for qty - synchronizes with quantity"""
        self.quantity = max(int(value), 0)

    def increase(self, step: int = 1, *, max_quantity: int = 99) -> int:
        self.quantity = min(self.quantity + step, max_quantity)
        return self.quantity

    def decrease(self, step: int = 1) -> int:
        self.quantity = max(self.quantity - step, 0)
        return self.quantity

    def subtotal(self) -> float:
        if self.price is None:
            return 0.0
        return float(self.price) * self.quantity


class CartStore:
    """Thread-safe cart storage with JSON persistence."""

    _instance: Optional["CartStore"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CartStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.data_dir = Path("data/carts")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._carts: Dict[int, List[CartItem]] = {}
        self._load_all_carts()

        # Undo storage: last removed item per user with timestamp
        self._last_removed: Dict[int, Tuple[CartItem, float]] = {}
        self._undo_ttl_seconds: int = 15

    # ---------------------------------------------------------------------
    # Persistence helpers
    # ---------------------------------------------------------------------

    def _cart_file(self, user_id: int) -> Path:
        return self.data_dir / f"cart_{user_id}.json"

    def _load_cart(self, user_id: int) -> List[CartItem]:
        cart_file = self._cart_file(user_id)
        if not cart_file.exists():
            return []

        try:
            with cart_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:  # pragma: no cover - diagnostics only
            print(f"Error loading cart for user {user_id}: {exc}")
            return []

        items: List[CartItem] = []
        for payload in data.get("items", []):
            try:
                items.append(CartItem(**payload))
            except TypeError as exc:  # pragma: no cover - malformed payload
                print(f"Malformed cart item for user {user_id}: {exc}")
        return items

    def _save_cart(self, user_id: int, items: List[CartItem]) -> None:
        cart_file = self._cart_file(user_id)
        try:
            data = {"user_id": user_id, "items": [asdict(item) for item in items]}
            with cart_file.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        except Exception as exc:  # pragma: no cover - diagnostics only
            print(f"Error saving cart for user {user_id}: {exc}")

    def _load_all_carts(self) -> None:
        if not self.data_dir.exists():
            return
        for cart_file in self.data_dir.glob("cart_*.json"):
            try:
                user_id = int(cart_file.stem.split("_")[1])
            except (ValueError, IndexError):
                # Ignore unexpected filenames e.g. cart_user123.json
                continue
            self._carts[user_id] = self._load_cart(user_id)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def get_cart(self, user_id: int) -> List[CartItem]:
        if user_id not in self._carts:
            self._carts[user_id] = self._load_cart(user_id)
        return self._carts[user_id]

    def _find_item(
        self, cart: List[CartItem], product_id: str, variant_id: Optional[str]
    ) -> Optional[CartItem]:
        for item in cart:
            if item.product_id == product_id and item.variant_id == (variant_id or None):
                return item
        return None

    def add_item(
        self,
        user_id: int,
        product_id: str,
        variant_id: Optional[str] = None,
        quantity: int = 1,
        **kwargs,
    ) -> Tuple[CartItem, bool]:
        """Add item to cart. Returns (item, currency_conflict)"""
        cart = self.get_cart(user_id)
        item = self._find_item(cart, product_id, variant_id)

        # Check for currency conflict
        new_currency = kwargs.get("currency", "RUB")
        existing_currencies = {item.currency for item in cart if item.currency}
        currency_conflict = bool(existing_currencies and new_currency not in existing_currencies)

        if item:
            item.increase(max(quantity, 0) or 1)
        else:
            item = CartItem(
                product_id=product_id,
                variant_id=variant_id,
                quantity=max(quantity, 0) or 1,
                **kwargs,
            )
            cart.append(item)

        self._save_cart(user_id, cart)
        return item, currency_conflict

    def update_quantity(
        self, user_id: int, product_id: str, variant_id: Optional[str], quantity: int
    ) -> bool:
        cart = self.get_cart(user_id)
        item = self._find_item(cart, product_id, variant_id)
        if not item:
            return False

        if quantity <= 0:
            cart.remove(item)
            # track last removed on quantity -> 0
            self._last_removed[user_id] = (item, time.time())
        else:
            item.quantity = quantity
        self._save_cart(user_id, cart)
        return True

    def remove_item(self, user_id: int, product_id: str, variant_id: Optional[str]) -> bool:
        cart = self.get_cart(user_id)
        item = self._find_item(cart, product_id, variant_id)
        if not item:
            return False

        # store last removed before deletion
        self._last_removed[user_id] = (item, time.time())

        cart.remove(item)
        self._save_cart(user_id, cart)
        return True

    def inc_quantity(
        self, user_id: int, product_id: str, variant_id: Optional[str], step: int = 1
    ) -> Tuple[bool, int]:
        cart = self.get_cart(user_id)
        item = self._find_item(cart, product_id, variant_id)
        if not item:
            return False, 0
        new_qty = item.increase(step)
        self._save_cart(user_id, cart)
        return True, new_qty

    def dec_quantity(
        self, user_id: int, product_id: str, variant_id: Optional[str], step: int = 1
    ) -> Tuple[bool, int]:
        cart = self.get_cart(user_id)
        item = self._find_item(cart, product_id, variant_id)
        if not item:
            return False, 0
        new_qty = item.decrease(step)
        if new_qty <= 0:
            cart.remove(item)
            self._last_removed[user_id] = (item, time.time())
        self._save_cart(user_id, cart)
        return True, max(new_qty, 0)

    def clear_cart(self, user_id: int) -> int:
        cart = self.get_cart(user_id)
        removed = len(cart)
        if removed:
            cart.clear()
            self._save_cart(user_id, cart)
        return removed

    def get_cart_count(self, user_id: int) -> int:
        return sum(item.quantity for item in self.get_cart(user_id))

    def get_cart_total(self, user_id: int) -> Tuple[int, float, str]:
        cart = self.get_cart(user_id)
        total_qty = sum(item.quantity for item in cart)
        total_price = sum(item.subtotal() for item in cart)
        currency = next((item.currency for item in cart if item.currency), "RUB")
        return total_qty, total_price, currency

    def get_cart_summary(self, user_id: int) -> Dict:
        total_qty, total_price, currency = self.get_cart_total(user_id)
        cart = self.get_cart(user_id)
        return {
            "user_id": user_id,
            "items_count": len(cart),
            "total_quantity": total_qty,
            "total_price": total_price,
            "currency": currency,
            "items": [asdict(item) for item in cart],
        }

    # ---------------------------------------------------------------------
    # Undo API
    # ---------------------------------------------------------------------

    def restore_last_removed(self, user_id: int) -> Optional[CartItem]:
        """Restore last removed item if TTL not expired."""
        payload = self._last_removed.get(user_id)
        if not payload:
            return None
        item, ts = payload
        if time.time() - ts > self._undo_ttl_seconds:
            # TTL expired
            self._last_removed.pop(user_id, None)
            return None
        cart = self.get_cart(user_id)
        # merge back (idempotent): if exists, increase qty
        existing = self._find_item(cart, item.product_id, item.variant_id)
        if existing:
            existing.quantity += max(item.quantity, 1)
        else:
            cart.append(item)
        self._save_cart(user_id, cart)
        # clear stored last removed
        self._last_removed.pop(user_id, None)
        return item


_cart_store_instance: Optional[CartStore] = None


def get_cart_store() -> CartStore:
    global _cart_store_instance
    if _cart_store_instance is None:
        _cart_store_instance = CartStore()
    return _cart_store_instance
