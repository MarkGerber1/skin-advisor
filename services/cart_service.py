#!/usr/bin/env python3
"""
🛒 Улучшенный сервис корзины с валидацией, идемпотентностью и защитой от дублей
Все операции thread-safe, персистентные, с полной валидацией данных
"""

import time
import asyncio
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import threading

from engine.cart_store import CartStore, CartItem
from engine.catalog import get_catalog_manager
from engine.models import Product


class CartErrorCode(Enum):
    """Коды ошибок корзины"""
    INVALID_PRODUCT_ID = "INVALID_PRODUCT_ID"
    INVALID_VARIANT_ID = "INVALID_VARIANT_ID"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    VARIANT_NOT_SUPPORTED = "VARIANT_NOT_SUPPORTED" 
    VARIANT_MISMATCH = "VARIANT_MISMATCH"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DUPLICATE_REQUEST = "DUPLICATE_REQUEST"
    CART_OPERATION_FAILED = "CART_OPERATION_FAILED"


class CartServiceError(Exception):
    """Базовое исключение сервиса корзины"""
    def __init__(self, code: CartErrorCode, message: str, details: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code.value}] {message}")


@dataclass
class CartValidationResult:
    """Результат валидации товара"""
    valid: bool
    product: Optional[Product] = None
    variant_supported: bool = False
    error_code: Optional[CartErrorCode] = None
    error_message: Optional[str] = None


class CartService:
    """Улучшенный сервис корзины с полной валидацией и защитой от дублей"""
    
    def __init__(self, cart_store: Optional[CartStore] = None):
        self.cart_store = cart_store or CartStore()
        self._request_debounce: Dict[str, float] = {}  # Защита от двойного клика
        self._debounce_window = 2.0  # секунды
        self._lock = threading.Lock()
    
    def _validate_parameters(self, product_id: str, variant_id: Optional[str] = None, qty: int = 1) -> None:
        """Валидация входных параметров"""
        if not product_id or not isinstance(product_id, str) or len(product_id.strip()) == 0:
            raise CartServiceError(
                CartErrorCode.INVALID_PRODUCT_ID,
                "Product ID is required and must be a non-empty string",
                {"product_id": product_id}
            )
        
        if variant_id is not None and (not isinstance(variant_id, str) or len(variant_id.strip()) == 0):
            raise CartServiceError(
                CartErrorCode.INVALID_VARIANT_ID,
                "Variant ID must be a non-empty string if provided",
                {"variant_id": variant_id}
            )
        
        if not isinstance(qty, int) or qty < 1:
            raise CartServiceError(
                CartErrorCode.INVALID_QUANTITY,
                "Quantity must be a positive integer",
                {"qty": qty}
            )
    
    async def _validate_product_and_variant(self, product_id: str, variant_id: Optional[str] = None) -> CartValidationResult:
        """Проверка существования товара и соответствия варианта"""
        try:
            # Получаем каталог
            catalog_manager = get_catalog_manager()
            catalog = catalog_manager.get_catalog()
            
            # Ищем товар в каталоге
            product = None
            for p in catalog:
                if str(p.id) == product_id or str(getattr(p, 'key', '')) == product_id:
                    product = p
                    break
            
            if not product:
                return CartValidationResult(
                    valid=False,
                    error_code=CartErrorCode.PRODUCT_NOT_FOUND,
                    error_message=f"Product {product_id} not found in catalog"
                )
            
            # Проверяем что товар в наличии
            if not product.in_stock:
                return CartValidationResult(
                    valid=False,
                    product=product,
                    error_code=CartErrorCode.OUT_OF_STOCK,
                    error_message=f"Product {product_id} is out of stock"
                )
            
            # Если variant_id не указан - валидация успешна
            if not variant_id:
                return CartValidationResult(
                    valid=True,
                    product=product,
                    variant_supported=False
                )
            
            # Проверяем поддержку вариантов для категории товара
            variant_supporting_categories = [
                "foundation", "lipstick", "eyeshadow", "mascara", "concealer", 
                "powder", "blush", "тональный", "помада", "тени", "тушь",
                "консилер", "пудра", "румяна"
            ]
            
            category_lower = str(product.category).lower()
            supports_variants = any(cat in category_lower for cat in variant_supporting_categories)
            
            if not supports_variants:
                return CartValidationResult(
                    valid=False,
                    product=product,
                    variant_supported=False,
                    error_code=CartErrorCode.VARIANT_NOT_SUPPORTED,
                    error_message=f"Product category '{product.category}' does not support variants"
                )
            
            # Проверяем формат variant_id (базовая валидация)
            if not self._is_valid_variant_format(variant_id, product):
                return CartValidationResult(
                    valid=False,
                    product=product,
                    variant_supported=True,
                    error_code=CartErrorCode.VARIANT_MISMATCH,
                    error_message=f"Variant ID '{variant_id}' has invalid format for product {product_id}"
                )
            
            return CartValidationResult(
                valid=True,
                product=product,
                variant_supported=True
            )
            
        except Exception as e:
            return CartValidationResult(
                valid=False,
                error_code=CartErrorCode.CART_OPERATION_FAILED,
                error_message=f"Validation failed: {str(e)}"
            )
    
    def _is_valid_variant_format(self, variant_id: str, product: Product) -> bool:
        """Базовая проверка формата variant_id"""
        # Проверяем что variant_id имеет валидный формат
        # Например: shade-01, shade-fair, volume-30ml, size-medium
        valid_prefixes = ["shade-", "volume-", "size-", "color-", "tone-"]
        
        # Если начинается с валидного префикса - ОК
        if any(variant_id.startswith(prefix) for prefix in valid_prefixes):
            return True
        
        # Если просто буквы/цифры без специальных символов - тоже ОК
        if variant_id.replace("-", "").replace("_", "").isalnum():
            return True
        
        return False
    
    def _check_duplicate_request(self, user_id: int, product_id: str, variant_id: Optional[str]) -> bool:
        """Проверка на дублирующий запрос (защита от двойного клика)"""
        current_time = time.time()
        request_key = f"{user_id}:{product_id}:{variant_id or 'default'}"
        
        with self._lock:
            last_request_time = self._request_debounce.get(request_key, 0)
            
            if current_time - last_request_time < self._debounce_window:
                return True  # Дубликат
            
            # Обновляем время последнего запроса
            self._request_debounce[request_key] = current_time
            
            # Очищаем старые записи (старше 5 минут)
            cutoff_time = current_time - 300
            expired_keys = [k for k, t in self._request_debounce.items() if t < cutoff_time]
            for key in expired_keys:
                del self._request_debounce[key]
        
        return False  # Не дубликат
    
    async def add_item(self, user_id: int, product_id: str, variant_id: Optional[str] = None, qty: int = 1) -> CartItem:
        """
        Добавить товар в корзину с полной валидацией и идемпотентностью
        
        Args:
            user_id: ID пользователя
            product_id: ID товара  
            variant_id: ID варианта (оттенок, размер, объем)
            qty: Количество (должно быть >= 1)
            
        Returns:
            CartItem: Добавленный/обновленный элемент корзины
            
        Raises:
            CartServiceError: При ошибках валидации или операции
        """
        # 1. Валидация входных параметров
        self._validate_parameters(product_id, variant_id, qty)
        
        # 2. Защита от двойного клика
        if self._check_duplicate_request(user_id, product_id, variant_id):
            raise CartServiceError(
                CartErrorCode.DUPLICATE_REQUEST,
                "Duplicate request detected. Please wait before trying again.",
                {"user_id": user_id, "product_id": product_id, "variant_id": variant_id}
            )
        
        # 3. Валидация товара и варианта
        validation_result = await self._validate_product_and_variant(product_id, variant_id)
        if not validation_result.valid:
            raise CartServiceError(
                validation_result.error_code,
                validation_result.error_message,
                {"product_id": product_id, "variant_id": variant_id}
            )
        
        product = validation_result.product
        
        # 4. Создание CartItem
        cart_item = CartItem(
            product_id=product_id,
            qty=qty,
            brand=product.brand,
            name=str(getattr(product, 'title', product.name)),
            price=float(product.price) if product.price else 0.0,
            price_currency=getattr(product, 'price_currency', 'RUB'),
            ref_link=getattr(product, 'buy_url', getattr(product, 'link', '')),
            explain="",  # Будет заполнено explain_generator при необходимости
            category=product.category,
            in_stock=product.in_stock,
            variant_id=variant_id,
            variant_name=self._get_variant_display_name(variant_id),
            variant_type=self._get_variant_type(variant_id),
            added_at=datetime.now().isoformat()
        )
        
        # 5. Добавление в хранилище (с идемпотентностью)
        try:
            self.cart_store.add(user_id, cart_item)
            print(f"✅ Cart service: Added {product_id}:{variant_id or 'default'} for user {user_id}")
            return cart_item
            
        except Exception as e:
            raise CartServiceError(
                CartErrorCode.CART_OPERATION_FAILED,
                f"Failed to add item to cart: {str(e)}",
                {"user_id": user_id, "product_id": product_id, "variant_id": variant_id}
            )
    
    def _get_variant_display_name(self, variant_id: Optional[str]) -> Optional[str]:
        """Получить отображаемое имя варианта"""
        if not variant_id:
            return None
        
        # Простое преобразование variant_id в читаемое название
        if variant_id.startswith("shade-"):
            return variant_id.replace("shade-", "").replace("-", " ").title()
        elif variant_id.startswith("volume-"):
            return variant_id.replace("volume-", "")
        elif variant_id.startswith("size-"):
            return variant_id.replace("size-", "").replace("-", " ").title()
        else:
            return variant_id.replace("-", " ").title()
    
    def _get_variant_type(self, variant_id: Optional[str]) -> Optional[str]:
        """Определить тип варианта"""
        if not variant_id:
            return None
        
        if variant_id.startswith("shade-") or variant_id.startswith("color-"):
            return "shade"
        elif variant_id.startswith("volume-"):
            return "volume" 
        elif variant_id.startswith("size-"):
            return "size"
        else:
            return "other"
    
    async def update_item_variant(self, user_id: int, product_id: str, old_variant_id: Optional[str], new_variant_id: Optional[str]) -> CartItem:
        """
        Обновить вариант товара в корзине
        
        Args:
            user_id: ID пользователя
            product_id: ID товара
            old_variant_id: Старый ID варианта  
            new_variant_id: Новый ID варианта
            
        Returns:
            CartItem: Обновленный элемент корзины
            
        Raises:
            CartServiceError: При ошибках валидации или операции
        """
        # Валидация нового варианта
        if new_variant_id:
            validation_result = await self._validate_product_and_variant(product_id, new_variant_id)
            if not validation_result.valid:
                raise CartServiceError(
                    validation_result.error_code,
                    validation_result.error_message,
                    {"product_id": product_id, "new_variant_id": new_variant_id}
                )
        
        # Получаем текущую корзину
        items = self.cart_store.get(user_id)
        items_dict = {item.get_composite_key(): item for item in items}
        
        old_key = f"{product_id}:{old_variant_id or 'default'}"
        new_key = f"{product_id}:{new_variant_id or 'default'}"
        
        if old_key not in items_dict:
            raise CartServiceError(
                CartErrorCode.PRODUCT_NOT_FOUND,
                f"Item with key {old_key} not found in cart",
                {"user_id": user_id, "old_key": old_key}
            )
        
        # Получаем старый элемент
        old_item = items_dict[old_key]
        
        # Удаляем старый элемент
        self.cart_store.remove(user_id, product_id, old_variant_id)
        
        # Создаем новый элемент с обновленным вариантом
        updated_item = CartItem(
            product_id=old_item.product_id,
            qty=old_item.qty,
            brand=old_item.brand,
            name=old_item.name,
            price=old_item.price,
            price_currency=old_item.price_currency,
            ref_link=old_item.ref_link,
            explain=old_item.explain,
            category=old_item.category,
            in_stock=old_item.in_stock,
            variant_id=new_variant_id,
            variant_name=self._get_variant_display_name(new_variant_id),
            variant_type=self._get_variant_type(new_variant_id),
            added_at=old_item.added_at
        )
        
        # Добавляем обновленный элемент
        self.cart_store.add(user_id, updated_item)
        
        print(f"✅ Cart service: Updated variant {old_key} → {new_key} for user {user_id}")
        return updated_item
    
    def remove_item(self, user_id: int, product_id: str, variant_id: Optional[str] = None) -> bool:
        """
        Удалить товар из корзины
        
        Args:
            user_id: ID пользователя
            product_id: ID товара
            variant_id: ID варианта (если None - удаляет любой вариант)
            
        Returns:
            bool: True если элемент был удален
            
        Raises:
            CartServiceError: При ошибках операции
        """
        try:
            self.cart_store.remove(user_id, product_id, variant_id)
            print(f"✅ Cart service: Removed {product_id}:{variant_id or 'any'} for user {user_id}")
            return True
            
        except Exception as e:
            raise CartServiceError(
                CartErrorCode.CART_OPERATION_FAILED,
                f"Failed to remove item from cart: {str(e)}",
                {"user_id": user_id, "product_id": product_id, "variant_id": variant_id}
            )
    
    def get_cart(self, user_id: int) -> List[CartItem]:
        """
        Получить содержимое корзины пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[CartItem]: Список элементов корзины
        """
        try:
            return self.cart_store.get(user_id)
        except Exception as e:
            raise CartServiceError(
                CartErrorCode.CART_OPERATION_FAILED,
                f"Failed to get cart: {str(e)}",
                {"user_id": user_id}
            )
    
    def clear_cart(self, user_id: int) -> None:
        """
        Очистить корзину пользователя
        
        Args:
            user_id: ID пользователя
            
        Raises:
            CartServiceError: При ошибках операции
        """
        try:
            self.cart_store.clear(user_id)
            print(f"✅ Cart service: Cleared cart for user {user_id}")
            
        except Exception as e:
            raise CartServiceError(
                CartErrorCode.CART_OPERATION_FAILED,
                f"Failed to clear cart: {str(e)}",
                {"user_id": user_id}
            )
    
    def set_item_quantity(self, user_id: int, product_id: str, variant_id: Optional[str], qty: int) -> Optional[CartItem]:
        """
        Установить количество товара в корзине
        
        Args:
            user_id: ID пользователя  
            product_id: ID товара
            variant_id: ID варианта
            qty: Новое количество (0 = удалить)
            
        Returns:
            CartItem или None: Обновленный элемент или None если удален
            
        Raises:
            CartServiceError: При ошибках валидации или операции
        """
        if qty < 0:
            raise CartServiceError(
                CartErrorCode.INVALID_QUANTITY,
                "Quantity cannot be negative",
                {"qty": qty}
            )
        
        try:
            if qty == 0:
                self.remove_item(user_id, product_id, variant_id)
                return None
            else:
                self.cart_store.set_qty(user_id, product_id, qty, variant_id)
                
                # Получаем обновленный элемент
                items = self.get_cart(user_id)
                composite_key = f"{product_id}:{variant_id or 'default'}"
                
                for item in items:
                    if item.get_composite_key() == composite_key:
                        return item
                        
                return None
                
        except Exception as e:
            raise CartServiceError(
                CartErrorCode.CART_OPERATION_FAILED,
                f"Failed to set item quantity: {str(e)}",
                {"user_id": user_id, "product_id": product_id, "variant_id": variant_id, "qty": qty}
            )


# Глобальный экземпляр сервиса
_cart_service = None

def get_cart_service() -> CartService:
    """Получить глобальный экземпляр сервиса корзины"""
    global _cart_service
    if _cart_service is None:
        _cart_service = CartService()
    return _cart_service
