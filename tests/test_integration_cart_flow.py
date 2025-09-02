#!/usr/bin/env python3
"""
🧪 Интеграционные тесты полного потока корзины
Тестирует: тесты → рекомендации → добавление в корзину → оформление
"""

import pytest
import tempfile
import shutil
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Импорты из проекта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from engine.cart_store import CartStore, CartItem
from engine.source_prioritizer import SourcePrioritizer
from engine.models import UserProfile


class TestCartFlowIntegration:
    """Интеграционные тесты для полного потока корзины"""
    
    def setup_method(self):
        """Создаем временную директорию для тестов"""
        self.temp_dir = tempfile.mkdtemp()
        self.cart_store = CartStore(base_dir=self.temp_dir)
        self.prioritizer = SourcePrioritizer()
        self.user_id = 12345
    
    def teardown_method(self):
        """Очищаем временную директорию"""
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_cart_flow(self):
        """Тест полного потока: рекомендации → добавление → управление корзиной"""
        
        # 1. Симулируем рекомендации от селектора с приоритизацией источников
        mock_recommendations = [
            {
                "id": "lipstick-mac-001",
                "brand": "MAC",
                "name": "Ruby Woo",
                "category": "lipstick",
                "price": 2500.0,
                "price_currency": "₽",
                "link": "https://goldapple.ru/mac-ruby-woo",
                "ref_link": "https://goldapple.ru/mac-ruby-woo?ref=S1",
                "source_priority": 1,
                "source_name": "Золотое Яблоко",
                "source_category": "golden_apple"
            },
            {
                "id": "foundation-fenty-001", 
                "brand": "Fenty Beauty",
                "name": "Pro Filt'r Foundation",
                "category": "foundation",
                "price": 3200.0,
                "price_currency": "₽",
                "link": "https://sephora.ru/fenty-foundation",
                "ref_link": "https://sephora.ru/fenty-foundation?ref=S1",
                "source_priority": 2,
                "source_name": "Sephora Russia",
                "source_category": "ru_official"
            }
        ]
        
        # 2. Добавляем товары в корзину (имитируем user action)
        lipstick_item = CartItem(
            product_id="lipstick-mac-001",
            qty=2,
            brand="MAC",
            name="Ruby Woo",
            price=2500.0,
            price_currency="₽",
            ref_link="https://goldapple.ru/mac-ruby-woo?ref=S1",
            category="lipstick",
            variant_id="shade-ruby-woo",
            variant_name="Ruby Woo",
            variant_type="shade"
        )
        
        foundation_item = CartItem(
            product_id="foundation-fenty-001",
            qty=1,
            brand="Fenty Beauty", 
            name="Pro Filt'r Foundation",
            price=3200.0,
            price_currency="₽",
            ref_link="https://sephora.ru/fenty-foundation?ref=S1",
            category="foundation",
            variant_id="shade-150",
            variant_name="150",
            variant_type="shade"
        )
        
        self.cart_store.add(self.user_id, lipstick_item)
        self.cart_store.add(self.user_id, foundation_item)
        
        # 3. Проверяем корзину
        cart_items = self.cart_store.get(self.user_id)
        assert len(cart_items) == 2
        
        # 4. Проверяем идемпотентность - добавляем тот же оттенок помады
        lipstick_same_shade = CartItem(
            product_id="lipstick-mac-001",
            qty=1,
            variant_id="shade-ruby-woo",
            brand="MAC",
            name="Ruby Woo"
        )
        self.cart_store.add(self.user_id, lipstick_same_shade)
        
        cart_items = self.cart_store.get(self.user_id)
        assert len(cart_items) == 2  # Не дублируется
        
        # Находим помаду и проверяем что qty увеличилось
        lipstick_in_cart = next((item for item in cart_items 
                               if item.get_composite_key() == "lipstick-mac-001:shade-ruby-woo"), None)
        assert lipstick_in_cart is not None
        assert lipstick_in_cart.qty == 3  # 2 + 1
        
        # 5. Добавляем другой оттенок той же помады
        lipstick_different_shade = CartItem(
            product_id="lipstick-mac-001",
            qty=1,
            variant_id="shade-velvet-teddy",
            variant_name="Velvet Teddy",
            variant_type="shade",
            brand="MAC",
            name="Velvet Teddy"
        )
        self.cart_store.add(self.user_id, lipstick_different_shade)
        
        cart_items = self.cart_store.get(self.user_id)
        assert len(cart_items) == 3  # Добавился как отдельная позиция
        
        # 6. Тестируем управление количеством
        self.cart_store.set_qty(self.user_id, "lipstick-mac-001", 5, "shade-ruby-woo")
        
        cart_items = self.cart_store.get(self.user_id)
        lipstick_ruby = next((item for item in cart_items 
                            if item.get_composite_key() == "lipstick-mac-001:shade-ruby-woo"), None)
        assert lipstick_ruby.qty == 5
        
        # 7. Тестируем удаление конкретного варианта
        self.cart_store.remove(self.user_id, "lipstick-mac-001", "shade-velvet-teddy")
        
        cart_items = self.cart_store.get(self.user_id)
        assert len(cart_items) == 2  # Velvet Teddy удален
        
        # 8. Проверяем итоговую корзину
        composite_keys = [item.get_composite_key() for item in cart_items]
        assert "lipstick-mac-001:shade-ruby-woo" in composite_keys
        assert "foundation-fenty-001:shade-150" in composite_keys
        assert "lipstick-mac-001:shade-velvet-teddy" not in composite_keys
    
    def test_source_prioritization_in_recommendations(self):
        """Тест приоритизации источников в рекомендациях"""
        
        # Создаем товары с разными источниками
        products_mixed_sources = [
            {"name": "Product A", "link": "https://unknown-shop.com/a"},
            {"name": "Product B", "link": "https://goldapple.ru/b"},
            {"name": "Product C", "link": "https://wildberries.ru/c"}, 
            {"name": "Product D", "link": "https://sephora.ru/d"},
        ]
        
        # Сортируем по приоритету
        sorted_products = self.prioritizer.sort_products_by_source_priority(products_mixed_sources)
        
        # Проверяем что Золотое Яблоко на первом месте
        assert sorted_products[0]["name"] == "Product B"
        assert sorted_products[1]["name"] == "Product D"  # Sephora RU
        assert sorted_products[2]["name"] == "Product C"  # Wildberries
        assert sorted_products[3]["name"] == "Product A"  # Unknown
        
        # Проверяем получение лучшего источника
        best_product = self.prioritizer.get_best_source_product(products_mixed_sources)
        assert best_product["name"] == "Product B"  # Золотое Яблоко
    
    def test_cart_with_multiple_variants_persistence(self):
        """Тест сохранения корзины с множественными вариантами"""
        
        # Добавляем несколько вариантов разных товаров
        items = [
            CartItem(product_id="lipstick-001", variant_id="red-01", qty=1, brand="Brand A"),
            CartItem(product_id="lipstick-001", variant_id="pink-02", qty=2, brand="Brand A"),
            CartItem(product_id="foundation-001", variant_id="light-120", qty=1, brand="Brand B"),
            CartItem(product_id="mascara-001", qty=1, brand="Brand C"),  # Без варианта
        ]
        
        for item in items:
            self.cart_store.add(self.user_id, item)
        
        # Создаем новый экземпляр CartStore (симулируем перезапуск)
        new_cart_store = CartStore(base_dir=self.temp_dir)
        loaded_items = new_cart_store.get(self.user_id)
        
        assert len(loaded_items) == 4
        
        # Проверяем что все варианты загрузились корректно
        composite_keys = [item.get_composite_key() for item in loaded_items]
        
        assert "lipstick-001:red-01" in composite_keys
        assert "lipstick-001:pink-02" in composite_keys
        assert "foundation-001:light-120" in composite_keys
        assert "mascara-001:default" in composite_keys
        
        # Проверяем количества
        items_dict = {item.get_composite_key(): item for item in loaded_items}
        assert items_dict["lipstick-001:pink-02"].qty == 2
        assert items_dict["foundation-001:light-120"].qty == 1
    
    def test_legacy_cart_migration(self):
        """Тест автоматической миграции legacy корзины"""
        
        # Имитируем старую корзину без полей variant_*
        import json
        
        legacy_data = {
            "old-product-001": {
                "product_id": "old-product-001",
                "qty": 2,
                "brand": "Legacy Brand",
                "name": "Legacy Product",
                "price": 100.0,
                "price_currency": "₽",
                "ref_link": "https://goldapple.ru/legacy",
                "explain": "Legacy explanation",
                "category": "legacy",
                "in_stock": True,
                "added_at": "2024-01-01T12:00:00"
                # Отсутствуют: variant_id, variant_name, variant_type
            }
        }
        
        # Сохраняем legacy данные
        legacy_cart_path = self.cart_store._path(self.user_id)
        with open(legacy_cart_path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)
        
        # Загружаем через новую систему
        migrated_items = self.cart_store.get(self.user_id)
        
        assert len(migrated_items) == 1
        item = migrated_items[0]
        
        # Проверяем что variant поля автоматически добавились как None
        assert item.variant_id is None
        assert item.variant_name is None
        assert item.variant_type is None
        assert item.get_composite_key() == "old-product-001:default"
        
        # Проверяем что остальные данные сохранились
        assert item.product_id == "old-product-001"
        assert item.qty == 2
        assert item.brand == "Legacy Brand"
        
        # Тестируем что можем добавить новый вариант к legacy товару
        new_variant = CartItem(
            product_id="old-product-001",
            variant_id="new-variant",
            qty=1,
            brand="Legacy Brand"
        )
        self.cart_store.add(self.user_id, new_variant)
        
        all_items = self.cart_store.get(self.user_id)
        assert len(all_items) == 2  # Legacy + новый вариант


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

