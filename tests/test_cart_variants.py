#!/usr/bin/env python3
"""
🧪 Автотесты для поддержки вариантов товаров в корзине
Тестирует: variant_id, идемпотентность для вариантов, составной ключ
"""

import pytest
import tempfile
import shutil
import os
import sys

# Импорты из проекта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from engine.cart_store import CartStore, CartItem


class TestCartVariants:
    """Тесты для вариантов товаров"""
    
    def setup_method(self):
        """Создаем временную директорию для тестов"""
        self.temp_dir = tempfile.mkdtemp()
        self.cart_store = CartStore(base_dir=self.temp_dir)
        self.user_id = 12345
    
    def teardown_method(self):
        """Очищаем временную директорию"""
        shutil.rmtree(self.temp_dir)
    
    def test_composite_key_generation(self):
        """Тест генерации составного ключа"""
        # Товар без варианта
        item_no_variant = CartItem(product_id="lipstick-001")
        assert item_no_variant.get_composite_key() == "lipstick-001:default"
        
        # Товар с вариантом
        item_with_variant = CartItem(
            product_id="lipstick-001",
            variant_id="shade-red-01",
            variant_name="Classic Red",
            variant_type="shade"
        )
        assert item_with_variant.get_composite_key() == "lipstick-001:shade-red-01"
    
    def test_different_variants_separate_items(self):
        """Разные варианты одного товара должны быть отдельными позициями"""
        lipstick_red = CartItem(
            product_id="lipstick-001",
            qty=1,
            brand="MAC",
            name="Ruby Woo",
            variant_id="shade-red-01",
            variant_name="Ruby Woo",
            variant_type="shade"
        )
        
        lipstick_pink = CartItem(
            product_id="lipstick-001",
            qty=2,
            brand="MAC", 
            name="Velvet Teddy",
            variant_id="shade-pink-02",
            variant_name="Velvet Teddy",
            variant_type="shade"
        )
        
        self.cart_store.add(self.user_id, lipstick_red)
        self.cart_store.add(self.user_id, lipstick_pink)
        
        items = self.cart_store.get(self.user_id)
        
        # Должно быть 2 отдельные позиции
        assert len(items) == 2
        
        # Проверяем что каждый вариант сохранился отдельно
        items_dict = {item.get_composite_key(): item for item in items}
        assert "lipstick-001:shade-red-01" in items_dict
        assert "lipstick-001:shade-pink-02" in items_dict
        assert items_dict["lipstick-001:shade-red-01"].qty == 1
        assert items_dict["lipstick-001:shade-pink-02"].qty == 2
    
    def test_same_variant_idempotency(self):
        """Повторное добавление того же варианта должно увеличивать qty"""
        lipstick_red = CartItem(
            product_id="lipstick-001",
            qty=2,
            brand="MAC",
            name="Ruby Woo",
            variant_id="shade-red-01",
            variant_name="Ruby Woo",
            variant_type="shade"
        )
        
        # Добавляем первый раз
        self.cart_store.add(self.user_id, lipstick_red)
        
        # Добавляем тот же вариант повторно
        lipstick_red_again = CartItem(
            product_id="lipstick-001",
            qty=3,
            brand="MAC",
            name="Ruby Woo",
            variant_id="shade-red-01",
            variant_name="Ruby Woo", 
            variant_type="shade"
        )
        self.cart_store.add(self.user_id, lipstick_red_again)
        
        items = self.cart_store.get(self.user_id)
        
        # Должна быть только 1 позиция
        assert len(items) == 1
        assert items[0].qty == 5  # 2 + 3
        assert items[0].get_composite_key() == "lipstick-001:shade-red-01"
    
    def test_product_without_variant_vs_with_variant(self):
        """Товар без варианта и с вариантом должны быть разными позициями"""
        # Товар без варианта (default)
        foundation_default = CartItem(
            product_id="foundation-001",
            qty=1,
            brand="Fenty",
            name="Pro Filt'r"
        )
        
        # Тот же товар с конкретным оттенком
        foundation_shade = CartItem(
            product_id="foundation-001",
            qty=1,
            brand="Fenty",
            name="Pro Filt'r",
            variant_id="shade-120",
            variant_name="120",
            variant_type="shade"
        )
        
        self.cart_store.add(self.user_id, foundation_default)
        self.cart_store.add(self.user_id, foundation_shade)
        
        items = self.cart_store.get(self.user_id)
        
        # Должно быть 2 позиции
        assert len(items) == 2
        
        items_dict = {item.get_composite_key(): item for item in items}
        assert "foundation-001:default" in items_dict
        assert "foundation-001:shade-120" in items_dict
    
    def test_remove_specific_variant(self):
        """Тест удаления конкретного варианта"""
        # Добавляем два варианта
        lipstick_red = CartItem(
            product_id="lipstick-001",
            variant_id="shade-red-01",
            qty=1
        )
        lipstick_pink = CartItem(
            product_id="lipstick-001", 
            variant_id="shade-pink-02",
            qty=2
        )
        
        self.cart_store.add(self.user_id, lipstick_red)
        self.cart_store.add(self.user_id, lipstick_pink)
        assert len(self.cart_store.get(self.user_id)) == 2
        
        # Удаляем конкретный вариант
        self.cart_store.remove(self.user_id, "lipstick-001", "shade-red-01")
        
        items = self.cart_store.get(self.user_id)
        assert len(items) == 1
        assert items[0].get_composite_key() == "lipstick-001:shade-pink-02"
    
    def test_set_qty_specific_variant(self):
        """Тест установки количества для конкретного варианта"""
        # Добавляем два варианта
        lipstick_red = CartItem(product_id="lipstick-001", variant_id="shade-red-01", qty=1)
        lipstick_pink = CartItem(product_id="lipstick-001", variant_id="shade-pink-02", qty=2)
        
        self.cart_store.add(self.user_id, lipstick_red)
        self.cart_store.add(self.user_id, lipstick_pink)
        
        # Изменяем количество красной помады
        self.cart_store.set_qty(self.user_id, "lipstick-001", 10, "shade-red-01")
        
        items = self.cart_store.get(self.user_id)
        items_dict = {item.get_composite_key(): item for item in items}
        
        assert items_dict["lipstick-001:shade-red-01"].qty == 10
        assert items_dict["lipstick-001:shade-pink-02"].qty == 2  # Не изменилось
    
    def test_legacy_data_compatibility(self):
        """Тест совместимости с существующими данными без вариантов"""
        # Имитируем старые данные без полей variant_*
        import json
        legacy_data = {
            "old-product-001": {
                "product_id": "old-product-001",
                "qty": 3,
                "brand": "Legacy Brand",
                "name": "Legacy Product",
                "price": 100.0,
                "price_currency": "₽",
                "ref_link": "",
                "explain": "",
                "category": "test",
                "in_stock": True,
                "added_at": "2024-01-01T12:00:00"
                # Нет полей variant_id, variant_name, variant_type
            }
        }
        
        # Сохраняем legacy данные
        path = self.cart_store._path(self.user_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)
        
        # Загружаем через новую систему
        items = self.cart_store.get(self.user_id)
        
        assert len(items) == 1
        item = items[0]
        assert item.product_id == "old-product-001"
        assert item.qty == 3
        assert item.variant_id is None
        assert item.variant_name is None
        assert item.variant_type is None
        assert item.get_composite_key() == "old-product-001:default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



