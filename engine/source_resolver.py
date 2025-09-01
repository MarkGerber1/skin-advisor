#!/usr/bin/env python3
"""
🔗 Приоритизация источников и поиск альтернатив для блока "Что купить"
Обеспечивает: Gold Apple → RU Official → RU Marketplace → Intl Authorized
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import re

from engine.source_prioritizer import get_source_prioritizer, SourceInfo
from engine.catalog import get_catalog_manager
from engine.models import Product, UserProfile


@dataclass
class ResolvedProduct:
    """Товар с разрешенным источником и альтернативами"""
    original: Dict[str, Any]  # Исходный товар из рекомендаций
    source_info: SourceInfo   # Информация об источнике
    is_available: bool        # Доступность основного источника
    alternative: Optional[Dict[str, Any]] = None  # Альтернативный товар
    alternative_reason: Optional[str] = None      # Причина замены
    checked_at: str = ""      # Дата последней проверки
    currency_verified: bool = False  # Проверка валюты


class SourceResolver:
    """Разрешение источников с приоритизацией и поиском альтернатив"""
    
    def __init__(self):
        self.source_prioritizer = get_source_prioritizer()
        self.catalog_manager = get_catalog_manager()
    
    def resolve_source(self, product: Dict[str, Any]) -> ResolvedProduct:
        """
        Разрешить источник для товара с проверкой доступности
        
        Args:
            product: Товар из рекомендаций
            
        Returns:
            ResolvedProduct: Товар с разрешенным источником
        """
        # Получаем информацию об источнике
        original_link = product.get("ref_link") or product.get("link", "")
        source_info = self.source_prioritizer.get_source_info(original_link)
        
        # Проверяем доступность основного источника
        is_available = self._check_availability(product)
        
        # Если недоступен - ищем альтернативу
        alternative = None
        alternative_reason = None
        
        if not is_available:
            alternative, alternative_reason = self._find_alternative(product)
        
        # Проверяем валюту
        currency_verified = self._verify_currency(product)
        
        return ResolvedProduct(
            original=product,
            source_info=source_info,
            is_available=is_available,
            alternative=alternative,
            alternative_reason=alternative_reason,
            checked_at=datetime.now().isoformat(),
            currency_verified=currency_verified
        )
    
    def _check_availability(self, product: Dict[str, Any]) -> bool:
        """Быстрая проверка наличия товара"""
        # Проверяем флаг in_stock
        if not product.get("in_stock", True):
            return False
        
        # Проверяем что есть ссылка на покупку
        if not (product.get("ref_link") or product.get("link")):
            return False
        
        # Проверяем что есть цена
        if not product.get("price"):
            return False
        
        return True
    
    def _find_alternative(self, product: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Найти альтернативу для недоступного товара
        
        Стратегия поиска:
        1. Другой вариант того же продукта (другой оттенок/поставщик)
        2. Товар той же категории и ценовой группы
        3. Учет цветотипа для оттенков
        
        Returns:
            (alternative_product, reason): Альтернативный товар и причина замены
        """
        try:
            catalog = self.catalog_manager.get_catalog()
            original_category = product.get("category", "")
            original_price = float(product.get("price", 0))
            
            # 1. Поиск другого варианта того же продукта
            same_product_alternatives = self._find_same_product_variants(
                product, catalog, original_category, original_price
            )
            
            if same_product_alternatives:
                best_alt = self._pick_best_by_source_priority(same_product_alternatives)
                return best_alt, "другой_вариант_товара"
            
            # 2. Поиск в той же категории и ценовой группе
            category_alternatives = self._find_category_alternatives(
                product, catalog, original_category, original_price
            )
            
            if category_alternatives:
                best_alt = self._pick_best_by_source_priority(category_alternatives)
                return best_alt, "аналог_категории"
            
            # 3. Универсальные варианты для сезона (если применимо)
            universal_alternatives = self._find_universal_alternatives(
                product, catalog, original_category
            )
            
            if universal_alternatives:
                best_alt = self._pick_best_by_source_priority(universal_alternatives)
                return best_alt, "универсальный_вариант"
            
            return None, None
            
        except Exception as e:
            print(f"❌ Error finding alternative for {product.get('id', 'unknown')}: {e}")
            return None, None
    
    def _find_same_product_variants(self, product: Dict[str, Any], catalog: List[Product], 
                                   category: str, price: float) -> List[Dict[str, Any]]:
        """Найти другие варианты того же продукта"""
        alternatives = []
        product_brand = product.get("brand", "").lower()
        product_name_base = self._extract_base_name(product.get("name", ""))
        
        # Ценовой диапазон ±20%
        price_min = price * 0.8
        price_max = price * 1.2
        
        for catalog_product in catalog:
            if not catalog_product.in_stock:
                continue
            
            # Проверяем бренд
            if catalog_product.brand.lower() != product_brand:
                continue
            
            # Проверяем базовое название (без оттенка)
            catalog_name_base = self._extract_base_name(catalog_product.name)
            if catalog_name_base != product_name_base:
                continue
            
            # Проверяем ценовой диапазон
            catalog_price = float(catalog_product.price) if catalog_product.price else 0
            if not (price_min <= catalog_price <= price_max):
                continue
            
            # Конвертируем в dict формат
            alt_dict = self._product_to_dict(catalog_product)
            if alt_dict:
                alternatives.append(alt_dict)
        
        return alternatives[:3]  # Максимум 3 варианта
    
    def _find_category_alternatives(self, product: Dict[str, Any], catalog: List[Product],
                                   category: str, price: float) -> List[Dict[str, Any]]:
        """Найти альтернативы в той же категории"""
        alternatives = []
        
        # Ценовой диапазон ±30% для категорийных аналогов
        price_min = price * 0.7
        price_max = price * 1.3
        
        for catalog_product in catalog:
            if not catalog_product.in_stock:
                continue
            
            # Проверяем категорию (нечеткое совпадение)
            if not self._categories_match(category, catalog_product.category):
                continue
            
            # Проверяем ценовой диапазон
            catalog_price = float(catalog_product.price) if catalog_product.price else 0
            if not (price_min <= catalog_price <= price_max):
                continue
            
            # Исключаем тот же товар
            if (catalog_product.brand.lower() == product.get("brand", "").lower() and
                catalog_product.name.lower() == product.get("name", "").lower()):
                continue
            
            alt_dict = self._product_to_dict(catalog_product)
            if alt_dict:
                alternatives.append(alt_dict)
        
        return alternatives[:5]  # Максимум 5 вариантов
    
    def _find_universal_alternatives(self, product: Dict[str, Any], catalog: List[Product],
                                    category: str) -> List[Dict[str, Any]]:
        """Найти универсальные альтернативы"""
        alternatives = []
        
        # Универсальные категории-заменители
        universal_mappings = {
            "foundation": ["bb_cream", "tinted_moisturizer", "concealer"],
            "lipstick": ["lip_tint", "lip_balm_tinted"],
            "mascara": ["lash_serum"],
            "cleanser": ["micellar_water", "cleansing_oil"],
            "moisturizer": ["day_cream", "night_cream", "face_oil"]
        }
        
        category_lower = category.lower()
        universal_categories = []
        
        for main_cat, alternatives_cats in universal_mappings.items():
            if main_cat in category_lower:
                universal_categories.extend(alternatives_cats)
        
        if not universal_categories:
            return []
        
        for catalog_product in catalog:
            if not catalog_product.in_stock:
                continue
            
            catalog_category = catalog_product.category.lower()
            if any(univ_cat in catalog_category for univ_cat in universal_categories):
                alt_dict = self._product_to_dict(catalog_product)
                if alt_dict:
                    alternatives.append(alt_dict)
        
        return alternatives[:3]
    
    def _extract_base_name(self, name: str) -> str:
        """Извлечь базовое название товара без оттенка"""
        # Удаляем распространенные обозначения оттенков
        shade_patterns = [
            r'\s*-\s*\d+.*$',  # - 01 Fair, - 02 Light
            r'\s*\(\w+.*\)$',  # (Fair), (Light Beige)
            r'\s+\d+\w*$',     # 01, 02L, 1N1
            r'\s+(Fair|Light|Medium|Dark|Deep).*$',
            r'\s+(Светлый|Средний|Темный).*$'
        ]
        
        base_name = name
        for pattern in shade_patterns:
            base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
        
        return base_name.strip()
    
    def _categories_match(self, cat1: str, cat2: str) -> bool:
        """Проверить совпадение категорий (нечеткое)"""
        if not cat1 or not cat2:
            return False
        
        cat1_lower = cat1.lower()
        cat2_lower = cat2.lower()
        
        # Точное совпадение
        if cat1_lower == cat2_lower:
            return True
        
        # Синонимы категорий
        synonyms = {
            "foundation": ["тональный", "основа", "тональная"],
            "concealer": ["консилер", "корректор"],
            "powder": ["пудра"],
            "blush": ["румяна"],
            "lipstick": ["помада"],
            "mascara": ["тушь"],
            "cleanser": ["очищающее", "гель", "пенка"],
            "toner": ["тоник"],
            "serum": ["сыворотка"],
            "moisturizer": ["увлажняющее", "крем"]
        }
        
        for eng_category, rus_alternatives in synonyms.items():
            if eng_category in cat1_lower or any(alt in cat1_lower for alt in rus_alternatives):
                if eng_category in cat2_lower or any(alt in cat2_lower for alt in rus_alternatives):
                    return True
        
        return False
    
    def _pick_best_by_source_priority(self, alternatives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Выбрать лучшую альтернативу по приоритету источника"""
        if not alternatives:
            return None
        
        # Применяем приоритизацию источников
        prioritized = self.source_prioritizer.sort_products_by_source_priority(alternatives)
        return prioritized[0] if prioritized else alternatives[0]
    
    def _product_to_dict(self, product: Product) -> Optional[Dict[str, Any]]:
        """Конвертировать Product в dict формат"""
        try:
            from engine.selector import _with_affiliate, _as_dict
            
            # Используем существующую логику из селектора
            partner_code = "S1"
            redirect_base = None
            
            return {
                "id": getattr(product, 'key', getattr(product, 'id', '')),
                "brand": product.brand,
                "name": getattr(product, 'title', product.name),
                "category": product.category,
                "price": float(product.price) if product.price else 0.0,
                "price_currency": getattr(product, 'price_currency', 'RUB'),
                "link": getattr(product, 'buy_url', getattr(product, 'link', '')),
                "ref_link": _with_affiliate(
                    getattr(product, 'buy_url', getattr(product, 'link', '')), 
                    partner_code, 
                    redirect_base
                ),
                "in_stock": product.in_stock,
                "explain": "",  # Будет заполнено позже
            }
        except Exception as e:
            print(f"❌ Error converting product {product.id} to dict: {e}")
            return None
    
    def _verify_currency(self, product: Dict[str, Any]) -> bool:
        """Проверить корректность валюты"""
        currency = product.get("price_currency", "")
        price = product.get("price", 0)
        
        # Базовая проверка
        if not currency or not price:
            return False
        
        # Проверяем поддерживаемые валюты
        supported_currencies = ["RUB", "₽", "USD", "$", "EUR", "€"]
        return currency in supported_currencies


def resolve_products_with_alternatives(products: List[Dict[str, Any]]) -> List[ResolvedProduct]:
    """
    Разрешить источники для списка товаров с поиском альтернатив
    
    Args:
        products: Список товаров из рекомендаций
        
    Returns:
        List[ResolvedProduct]: Товары с разрешенными источниками
    """
    resolver = SourceResolver()
    resolved_products = []
    
    for product in products:
        resolved = resolver.resolve_source(product)
        resolved_products.append(resolved)
    
    return resolved_products


def enhance_product_with_source_info(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Дополнить товар информацией об источнике
    
    Args:
        product: Исходный товар
        
    Returns:
        Dict: Товар с дополненной информацией об источнике
    """
    resolver = SourceResolver()
    resolved = resolver.resolve_source(product)
    
    # Создаем копию товара с дополнительной информацией
    enhanced = product.copy()
    enhanced.update({
        "source_name": resolved.source_info.name,
        "source_priority": resolved.source_info.priority,
        "source_category": resolved.source_info.category,
        "is_available": resolved.is_available,
        "checked_at": resolved.checked_at,
        "currency_verified": resolved.currency_verified
    })
    
    # Если есть альтернатива - заменяем основной товар
    if resolved.alternative:
        enhanced.update({
            "original_id": product.get("id"),
            "original_name": product.get("name"),
            "alternative_reason": resolved.alternative_reason,
            **resolved.alternative  # Заменяем данные товара на альтернативу
        })
    
    return enhanced


# Глобальный экземпляр
_source_resolver = None

def get_source_resolver() -> SourceResolver:
    """Получить глобальный экземпляр source resolver"""
    global _source_resolver
    if _source_resolver is None:
        _source_resolver = SourceResolver()
    return _source_resolver
