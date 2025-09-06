"""
Unified Cart Store Service
Единое хранилище корзин для всех хендлеров
"""

import json
import os
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class CartItem:
    """Элемент корзины"""
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    brand: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    price_currency: str = "RUB"
    ref_link: Optional[str] = None
    category: Optional[str] = None

    def get_key(self) -> str:
        """Уникальный ключ товара в корзине"""
        return f"{self.product_id}:{self.variant_id or 'default'}"

class CartStore:
    """Единое хранилище корзин"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.data_dir = Path("data/carts")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._carts: Dict[int, List[CartItem]] = {}
        self._load_all_carts()

    def _get_cart_file(self, user_id: int) -> Path:
        """Получить путь к файлу корзины пользователя"""
        return self.data_dir / f"cart_{user_id}.json"

    def _load_cart(self, user_id: int) -> List[CartItem]:
        """Загрузить корзину пользователя"""
        cart_file = self._get_cart_file(user_id)
        if not cart_file.exists():
            return []

        try:
            with open(cart_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [CartItem(**item) for item in data.get('items', [])]
        except Exception as e:
            print(f"Error loading cart for user {user_id}: {e}")
            return []

    def _save_cart(self, user_id: int, items: List[CartItem]):
        """Сохранить корзину пользователя"""
        cart_file = self._get_cart_file(user_id)
        try:
            data = {'user_id': user_id, 'items': [asdict(item) for item in items]}
            with open(cart_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving cart for user {user_id}: {e}")

    def _load_all_carts(self):
        """Загрузить все корзины"""
        if not self.data_dir.exists():
            return

        for cart_file in self.data_dir.glob("cart_*.json"):
            try:
                user_id = int(cart_file.stem.split('_')[1])
                self._carts[user_id] = self._load_cart(user_id)
            except Exception as e:
                print(f"Error loading cart file {cart_file}: {e}")

    def get_cart(self, user_id: int) -> List[CartItem]:
        """Получить корзину пользователя"""
        if user_id not in self._carts:
            self._carts[user_id] = self._load_cart(user_id)
        return self._carts[user_id]

    def add_item(self, user_id: int, product_id: str, variant_id: Optional[str] = None,
                 quantity: int = 1, **kwargs) -> CartItem:
        """Добавить товар в корзину"""
        cart = self.get_cart(user_id)

        # Найти существующий товар
        existing_item = None
        for item in cart:
            if item.product_id == product_id and item.variant_id == (variant_id or None):
                existing_item = item
                break

        if existing_item:
            # Увеличить количество
            existing_item.quantity += quantity
            item = existing_item
        else:
            # Создать новый элемент
            item = CartItem(
                product_id=product_id,
                variant_id=variant_id,
                quantity=quantity,
                **kwargs
            )
            cart.append(item)

        self._save_cart(user_id, cart)
        return item

    def update_quantity(self, user_id: int, product_id: str, variant_id: Optional[str],
                       new_quantity: int) -> bool:
        """Обновить количество товара"""
        cart = self.get_cart(user_id)

        for item in cart:
            if item.product_id == product_id and item.variant_id == variant_id:
                if new_quantity <= 0:
                    cart.remove(item)
                else:
                    item.quantity = new_quantity
                self._save_cart(user_id, cart)
                return True

        return False

    def remove_item(self, user_id: int, product_id: str, variant_id: Optional[str]) -> bool:
        """Удалить товар из корзины"""
        cart = self.get_cart(user_id)

        for item in cart:
            if item.product_id == product_id and item.variant_id == variant_id:
                cart.remove(item)
                self._save_cart(user_id, cart)
                return True

        return False

    def clear_cart(self, user_id: int):
        """Очистить корзину"""
        self._carts[user_id] = []
        cart_file = self._get_cart_file(user_id)
        if cart_file.exists():
            cart_file.unlink()

    def get_cart_total(self, user_id: int) -> Tuple[int, float]:
        """Получить общее количество товаров и сумму"""
        cart = self.get_cart(user_id)
        total_quantity = sum(item.quantity for item in cart)
        total_price = sum((item.price or 0) * item.quantity for item in cart)
        return total_quantity, total_price

    def list_all_carts(self) -> Dict[int, List[CartItem]]:
        """Получить все корзины (для диагностики)"""
        # Перезагрузить все корзины
        self._load_all_carts()
        return self._carts.copy()

    def get_cart_summary(self, user_id: int) -> Dict:
        """Получить сводку по корзине"""
        cart = self.get_cart(user_id)
        total_quantity, total_price = self.get_cart_total(user_id)

        return {
            'user_id': user_id,
            'items_count': len(cart),
            'total_quantity': total_quantity,
            'total_price': total_price,
            'items': [asdict(item) for item in cart]
        }


# Глобальный экземпляр
_cart_store_instance = None

def get_cart_store() -> CartStore:
    """Получить глобальный экземпляр CartStore"""
    global _cart_store_instance
    if _cart_store_instance is None:
        _cart_store_instance = CartStore()
    return _cart_store_instance

