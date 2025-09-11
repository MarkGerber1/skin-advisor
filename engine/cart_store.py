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
    currency: Optional[str] = None
    ref_link: Optional[str] = None
    explain: Optional[str] = None
    category: Optional[str] = None
    in_stock: bool = True
    added_at: Optional[str] = None

    # NEW: Support for product variants (shade, volume, size)
    variant_id: Optional[str] = None  # e.g., "shade-01-fair", "volume-30ml", "size-medium"
    variant_name: Optional[str] = None  # e.g., "Fair", "30ml", "Medium"
    variant_type: Optional[str] = None  # e.g., "shade", "volume", "size"

    def get_composite_key(self) -> str:
        """Returns composite key for idempotent operations: product_id:variant_id"""
        if self.variant_id:
            return f"{self.product_id}:{self.variant_id}"
        return f"{self.product_id}:default"


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
        for composite_key, payload in raw.items():
            # Handle legacy items without variant fields
            if "variant_id" not in payload:
                payload["variant_id"] = None
                payload["variant_name"] = None
                payload["variant_type"] = None
            out[composite_key] = CartItem(**payload)
        return out

    def _save(self, user_id: int, items: Dict[str, CartItem]) -> None:
        path = self._path(user_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {composite_key: asdict(ci) for composite_key, ci in items.items()},
                f,
                ensure_ascii=False,
                indent=2,
            )

    def add(self, user_id: int, item: CartItem) -> None:
        """Add item to cart with variant support and idempotency"""
        with self._lock:
            items = self._load(user_id)
            composite_key = item.get_composite_key()

            if composite_key in items:
                # Same product + variant = increase quantity
                items[composite_key].qty += item.qty
                print(f"🔄 Cart: Increased qty for {composite_key}: {items[composite_key].qty}")
            else:
                # New product or new variant = add new item
                items[composite_key] = item
                print(f"✅ Cart: Added new item {composite_key}: qty={item.qty}")

            self._save(user_id, items)

    def remove(self, user_id: int, product_id: str, variant_id: Optional[str] = None) -> None:
        """Remove item by product_id and optional variant_id"""
        with self._lock:
            items = self._load(user_id)

            if variant_id:
                composite_key = f"{product_id}:{variant_id}"
            else:
                # If no variant specified, find and remove the default or any variant
                composite_key = f"{product_id}:default"
                if composite_key not in items:
                    # Look for any variant of this product
                    for key in list(items.keys()):
                        if key.startswith(f"{product_id}:"):
                            composite_key = key
                            break

            if composite_key in items:
                del items[composite_key]
                self._save(user_id, items)
                print(f"🗑️ Cart: Removed item {composite_key}")

    def set_qty(
        self, user_id: int, product_id: str, qty: int, variant_id: Optional[str] = None
    ) -> None:
        """Set quantity for specific product variant"""
        if qty <= 0:
            self.remove(user_id, product_id, variant_id)
            return

        with self._lock:
            items = self._load(user_id)

            if variant_id:
                composite_key = f"{product_id}:{variant_id}"
            else:
                composite_key = f"{product_id}:default"
                if composite_key not in items:
                    # Look for any variant of this product
                    for key in list(items.keys()):
                        if key.startswith(f"{product_id}:"):
                            composite_key = key
                            break

            if composite_key in items:
                items[composite_key].qty = qty
                self._save(user_id, items)
                print(f"📊 Cart: Set qty for {composite_key}: {qty}")

    def update_item_variant(
        self,
        user_id: int,
        product_id: str,
        old_variant_id: Optional[str],
        new_variant_id: Optional[str],
    ) -> Optional[CartItem]:
        """Update variant for an existing cart item"""
        with self._lock:
            items = self._load(user_id)

            # Find the old item
            old_composite_key = (
                f"{product_id}:{old_variant_id}" if old_variant_id else f"{product_id}:default"
            )

            if old_composite_key not in items:
                print(f"⚠️ Cart: Item not found for update: {old_composite_key}")
                return None

            old_item = items[old_composite_key]
            qty = old_item.qty

            # Remove old item
            del items[old_composite_key]

            # Create new item with updated variant
            new_item = CartItem(
                product_id=product_id,
                qty=qty,
                brand=old_item.brand,
                name=old_item.name,
                price=old_item.price,
                currency=old_item.currency,
                ref_link=old_item.ref_link,
                explain=old_item.explain,
                category=old_item.category,
                in_stock=old_item.in_stock,
                variant_id=new_variant_id,
                variant_name=None,  # Will be set by caller if needed
                variant_type=None,  # Will be set by caller if needed
            )

            # Add new item
            new_composite_key = new_item.get_composite_key()
            items[new_composite_key] = new_item

            self._save(user_id, items)
            print(f"🔄 Cart: Updated variant {old_composite_key} -> {new_composite_key}")

            return new_item

    def clear(self, user_id: int) -> None:
        with self._lock:
            path = self._path(user_id)
            if os.path.exists(path):
                os.remove(path)

    def get(self, user_id: int) -> List[CartItem]:
        with self._lock:
            return list(self._load(user_id).values())

    def inc_quantity(self, user_id: int, product_id: str, variant_id: Optional[str] = None) -> bool:
        """Увеличить количество товара на 1"""
        with self._lock:
            items = self._load(user_id)

            if variant_id:
                composite_key = f"{product_id}:{variant_id}"
            else:
                composite_key = f"{product_id}:default"
                if composite_key not in items:
                    # Ищем любой вариант этого товара
                    for key in items.keys():
                        if key.startswith(f"{product_id}:"):
                            composite_key = key
                            break

            if composite_key in items:
                items[composite_key].qty += 1
                self._save(user_id, items)
                print(f"➕ Cart: Increased qty for {composite_key}: {items[composite_key].qty}")
                return True

            return False

    def dec_quantity(self, user_id: int, product_id: str, variant_id: Optional[str] = None) -> bool:
        """Уменьшить количество товара на 1 (если станет 0 - удалить)"""
        with self._lock:
            items = self._load(user_id)

            if variant_id:
                composite_key = f"{product_id}:{variant_id}"
            else:
                composite_key = f"{product_id}:default"
                if composite_key not in items:
                    # Ищем любой вариант этого товара
                    for key in items.keys():
                        if key.startswith(f"{product_id}:"):
                            composite_key = key
                            break

            if composite_key in items:
                items[composite_key].qty -= 1
                if items[composite_key].qty <= 0:
                    del items[composite_key]
                    print(f"🗑️ Cart: Removed item {composite_key} (qty became 0)")
                else:
                    print(f"➖ Cart: Decreased qty for {composite_key}: {items[composite_key].qty}")

                self._save(user_id, items)
                return True

            return False

    def get_cart_count(self, user_id: int) -> int:
        """Получить общее количество товаров в корзине"""
        with self._lock:
            items = self._load(user_id)
            return sum(item.qty for item in items.values())

    def get_cart_total(self, user_id: int) -> tuple[int, float]:
        """Получить количество позиций и общую сумму"""
        with self._lock:
            items = self._load(user_id)
            total_items = sum(item.qty for item in items.values())
            total_price = sum((item.price or 0) * item.qty for item in items.values())
            return total_items, total_price

    def has_item(self, user_id: int, product_id: str, variant_id: Optional[str] = None) -> bool:
        """Проверить наличие товара в корзине"""
        with self._lock:
            items = self._load(user_id)

            if variant_id:
                composite_key = f"{product_id}:{variant_id}"
            else:
                composite_key = f"{product_id}:default"

            return composite_key in items
