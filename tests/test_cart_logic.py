#!/usr/bin/env python3
"""
🧪 Автотесты для логики корзины
Покрывает: идемпотентность, варианты, альтернативы, приоритизацию источников
"""

import pytest
import tempfile
import shutil
import os
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock

# Импорты из проекта
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from engine.cart_store import CartStore, CartItem
from bot.handlers.cart import _find_product_in_recommendations


class TestCartStore:
    """Тесты для основной логики корзины"""
    
    def setup_method(self):
        """Создаем временную директорию для тестов"""
        self.temp_dir = tempfile.mkdtemp()
        self.cart_store = CartStore(base_dir=self.temp_dir)
        self.user_id = 12345
    
    def teardown_method(self):
        """Очищаем временную директорию"""
        shutil.rmtree(self.temp_dir)
    
    def test_add_new_item(self):
        """Тест добавления нового товара"""
        item = CartItem(
            product_id="test_product_1",
            qty=2,
            brand="Test Brand",
            name="Test Product",
            price=100.0,
            price_currency="₽"
        )
        
        self.cart_store.add(self.user_id, item)
        items = self.cart_store.get(self.user_id)
        
        assert len(items) == 1
        assert "test_product_1" in items
        assert items["test_product_1"].qty == 2
        assert items["test_product_1"].brand == "Test Brand"
    
    def test_idempotency_same_product(self):
        """Тест идемпотентности: повторное добавление того же товара увеличивает qty"""
        item1 = CartItem(product_id="test_product_1", qty=1, brand="Brand", name="Product")
        item2 = CartItem(product_id="test_product_1", qty=3, brand="Brand", name="Product")
        
        self.cart_store.add(self.user_id, item1)
        self.cart_store.add(self.user_id, item2)
        
        items = self.cart_store.get(self.user_id)
        
        assert len(items) == 1  # Не дублируется
        assert items["test_product_1"].qty == 4  # 1 + 3
    
    def test_different_products(self):
        """Тест добавления разных товаров"""
        item1 = CartItem(product_id="product_1", qty=1, brand="Brand A", name="Product A")
        item2 = CartItem(product_id="product_2", qty=2, brand="Brand B", name="Product B")
        
        self.cart_store.add(self.user_id, item1)
        self.cart_store.add(self.user_id, item2)
        
        items = self.cart_store.get(self.user_id)
        
        assert len(items) == 2
        assert items["product_1"].qty == 1
        assert items["product_2"].qty == 2
    
    def test_remove_item(self):
        """Тест удаления товара"""
        item = CartItem(product_id="test_product", qty=5, brand="Brand", name="Product")
        
        self.cart_store.add(self.user_id, item)
        assert len(self.cart_store.get(self.user_id)) == 1
        
        self.cart_store.remove(self.user_id, "test_product")
        assert len(self.cart_store.get(self.user_id)) == 0
    
    def test_set_quantity(self):
        """Тест изменения количества"""
        item = CartItem(product_id="test_product", qty=2, brand="Brand", name="Product")
        
        self.cart_store.add(self.user_id, item)
        self.cart_store.set_qty(self.user_id, "test_product", 10)
        
        items = self.cart_store.get(self.user_id)
        assert items["test_product"].qty == 10
    
    def test_set_quantity_zero_removes_item(self):
        """Тест что установка qty=0 удаляет товар"""
        item = CartItem(product_id="test_product", qty=5, brand="Brand", name="Product")
        
        self.cart_store.add(self.user_id, item)
        self.cart_store.set_qty(self.user_id, "test_product", 0)
        
        items = self.cart_store.get(self.user_id)
        assert len(items) == 0
    
    def test_clear_cart(self):
        """Тест очистки корзины"""
        item1 = CartItem(product_id="product_1", qty=1, brand="Brand", name="Product 1")
        item2 = CartItem(product_id="product_2", qty=2, brand="Brand", name="Product 2")
        
        self.cart_store.add(self.user_id, item1)
        self.cart_store.add(self.user_id, item2)
        assert len(self.cart_store.get(self.user_id)) == 2
        
        self.cart_store.clear(self.user_id)
        assert len(self.cart_store.get(self.user_id)) == 0
    
    def test_persistence(self):
        """Тест сохранения в файл и загрузки"""
        item = CartItem(product_id="persistent_item", qty=3, brand="Brand", name="Persistent")
        
        # Добавляем через один экземпляр
        self.cart_store.add(self.user_id, item)
        
        # Создаем новый экземпляр с той же директорией
        new_store = CartStore(base_dir=self.temp_dir)
        items = new_store.get(self.user_id)
        
        assert len(items) == 1
        assert items["persistent_item"].qty == 3
        assert items["persistent_item"].brand == "Brand"
    
    def test_thread_safety(self):
        """Базовый тест thread safety (проверяем что lock существует)"""
        assert hasattr(self.cart_store, '_lock')
        assert self.cart_store._lock is not None


class TestSourcePrioritization:
    """Тесты для приоритизации источников (будущая функциональность)"""
    
    def test_golden_apple_priority(self):
        """Золотое Яблоко должно иметь наивысший приоритет"""
        sources = [
            {"domain": "sephora.com", "ref_link": "https://sephora.com/product/123"},
            {"domain": "goldenappletree.ru", "ref_link": "https://goldenappletree.ru/product/123"},
            {"domain": "wildberries.ru", "ref_link": "https://wildberries.ru/catalog/123"},
        ]
        
        # TODO: Реализовать SourcePrioritizer
        # prioritizer = SourcePrioritizer()
        # sorted_sources = prioritizer.sort_by_priority(sources)
        # assert sorted_sources[0]["domain"] == "goldenappletree.ru"
        
        # Пока что пропускаем - будет реализовано в следующем этапе
        pytest.skip("SourcePrioritizer not implemented yet")
    
    def test_russian_official_priority(self):
        """Российские официальные должны быть выше маркетплейсов"""
        sources = [
            {"domain": "wildberries.ru", "ref_link": "https://wildberries.ru/catalog/123"},
            {"domain": "sephora.ru", "ref_link": "https://sephora.ru/product/123"},
            {"domain": "ozon.ru", "ref_link": "https://ozon.ru/product/123"},
        ]
        
        # TODO: Реализовать приоритизацию
        pytest.skip("SourcePrioritizer not implemented yet")


class TestProductVariants:
    """Тесты для вариантов товаров (будущая функциональность)"""
    
    def test_different_shades_separate_items(self):
        """Разные оттенки одного товара должны быть отдельными позициями"""
        # TODO: Добавить поддержку variant_id в CartItem
        pytest.skip("Variant support not implemented yet")
    
    def test_same_variant_idempotency(self):
        """Повторное добавление того же варианта должно увеличивать qty"""
        # TODO: Реализовать составной ключ product_id:variant_id
        pytest.skip("Variant support not implemented yet")


class TestProductRecommendationSearch:
    """Тесты для поиска товаров в рекомендациях"""
    
    @pytest.mark.asyncio
    async def test_find_existing_product(self):
        """Тест поиска существующего товара в рекомендациях"""
        # TODO: Мокнуть FSM coordinator и selector
        pytest.skip("Requires FSM coordinator mocking")
    
    @pytest.mark.asyncio
    async def test_product_not_found(self):
        """Тест когда товар не найден в рекомендациях"""
        # TODO: Мокнуть пустой результат селектора
        pytest.skip("Requires FSM coordinator mocking")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



