from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class CartItem:
    """Cart item with full product information"""

    product_id: str
    variant_id: Optional[str] = None
    name: str = ""
    price: int = 0  # в копейках/центах
    currency: str = "RUB"  # ISO 4217
    qty: int = 1
    source: str = ""  # goldapple|brand|marketplace
    link: str = ""  # прямая ссылка
    meta: Dict = field(default_factory=dict)  # finish/texture/shade etc.

    # Legacy fields for backward compatibility
    brand: Optional[str] = None
    ref_link: Optional[str] = None
    explain: Optional[str] = None
    category: Optional[str] = None
    in_stock: bool = True
    added_at: Optional[str] = None
    variant_name: Optional[str] = None
    variant_type: Optional[str] = None

    def get_composite_key(self) -> str:
        """Returns composite key for idempotent operations: product_id:variant_id"""
        variant = self.variant_id or ""
        return f"{self.product_id}:{variant}"


@dataclass
class Cart:
    """Shopping cart with full calculation logic"""

    user_id: int
    items: Dict[str, CartItem] = field(
        default_factory=dict
    )  # key = f"{product_id}:{variant_id or ''}"
    subtotal: int = 0  # в копейках
    currency: str = "RUB"  # единая валюта корзины
    updated_at: datetime = field(default_factory=datetime.now)
    needs_review: bool = False  # пометка при разных валютах

    def recalculate(self) -> None:
        """Recalculate subtotal and check currency consistency"""
        if not self.items:
            self.subtotal = 0
            self.currency = "RUB"
            self.needs_review = False
            return

        # Calculate subtotal
        self.subtotal = sum(item.price * item.qty for item in self.items.values())

        # Check currency consistency
        currencies = {item.currency for item in self.items.values()}
        if len(currencies) > 1:
            self.needs_review = True
            # Use the currency of the first item as primary
            self.currency = next(iter(currencies))
        else:
            self.needs_review = False
            self.currency = next(iter(currencies)) if currencies else "RUB"

        self.updated_at = datetime.now()

    def add_item(self, item: CartItem) -> None:
        """Add item with idempotency (merge quantities for same product+variant)"""
        key = item.get_composite_key()

        if key in self.items:
            # Merge quantities for same product+variant
            self.items[key].qty += item.qty
        else:
            # Add new item
            self.items[key] = item

        self.recalculate()

    def remove_item(self, key: str) -> bool:
        """Remove item by composite key"""
        if key in self.items:
            del self.items[key]
            self.recalculate()
            return True
        return False

    def set_quantity(self, key: str, qty: int) -> bool:
        """Set quantity for item (remove if qty <= 0)"""
        if qty <= 0:
            return self.remove_item(key)

        if key in self.items:
            self.items[key].qty = min(qty, 99)  # Max 99 items
            self.recalculate()
            return True
        return False

    def clear(self) -> None:
        """Clear all items"""
        self.items.clear()
        self.recalculate()


class CartStore:
    """Persist cart storage with Redis/SQLite fallback"""

    def __init__(self, base_dir: str = "data/carts"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, user_id: int) -> str:
        return os.path.join(self.base_dir, f"{user_id}.json")

    def _load_items(self, user_id: int) -> Dict[str, CartItem]:
        """Load cart items from storage"""
        path = self._path(user_id)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            raw: Dict[str, Dict] = json.load(f) or {}
        out: Dict[str, CartItem] = {}
        for composite_key, payload in raw.items():
            # Handle legacy items and ensure all fields exist
            if "variant_id" not in payload:
                payload["variant_id"] = None
            if "name" not in payload:
                payload["name"] = payload.get("brand", "Unknown Product")
            if "price" not in payload:
                payload["price"] = int((payload.get("price") or 0) * 100)  # Convert to cents
            if "currency" not in payload:
                payload["currency"] = "RUB"
            if "source" not in payload:
                payload["source"] = "marketplace"
            if "link" not in payload:
                payload["link"] = payload.get("ref_link", "")
            if "meta" not in payload:
                payload["meta"] = {}
            out[composite_key] = CartItem(**payload)
        return out

    def _save_items(self, user_id: int, items: Dict[str, CartItem]) -> None:
        """Save cart items to storage"""
        path = self._path(user_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {composite_key: asdict(ci) for composite_key, ci in items.items()},
                f,
                ensure_ascii=False,
                indent=2,
                default=str,  # Handle datetime serialization
            )

    # New interface methods
    async def get(self, user_id: int) -> Cart:
        """Get user's cart"""
        with self._lock:
            items = self._load_items(user_id)
            cart = Cart(user_id=user_id, items=items)
            cart.recalculate()  # Ensure calculations are up to date
            return cart

    async def add(self, user_id: int, item: CartItem) -> Cart:
        """Add item to cart with idempotency"""
        with self._lock:
            cart = await self.get(user_id)
            cart.add_item(item)
            self._save_items(user_id, cart.items)
            return cart

    async def remove(self, user_id: int, key: str) -> Cart:
        """Remove item from cart"""
        with self._lock:
            cart = await self.get(user_id)
            cart.remove_item(key)
            self._save_items(user_id, cart.items)
            return cart

    async def set_qty(self, user_id: int, key: str, qty: int) -> Cart:
        """Set quantity for cart item"""
        with self._lock:
            cart = await self.get(user_id)
            cart.set_quantity(key, qty)
            self._save_items(user_id, cart.items)
            return cart

    async def clear(self, user_id: int) -> None:
        """Clear user's cart"""
        with self._lock:
            path = self._path(user_id)
            if os.path.exists(path):
                os.remove(path)

    # Legacy sync methods for backward compatibility
    def get_cart_count(self, user_id: int) -> int:
        """Получить общее количество товаров в корзине"""
        with self._lock:
            items = self._load_items(user_id)
            return sum(item.qty for item in items.values())
