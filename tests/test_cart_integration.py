"""Интеграционные тесты для корзины"""

import pytest
from services.cart_store import CartStore


class TestCartIntegration:
    """Интеграционные тесты для полной работы корзины"""

    def test_full_cart_workflow(self):
        """Тест полного workflow корзины"""
        store = CartStore()

        # Добавляем товары
        store.add_item(
            123,
            "product-1",
            quantity=1,
            brand="Brand1",
            name="Product 1",
            price=100.0,
            currency="RUB",
        )
        store.add_item(
            123,
            "product-2",
            quantity=2,
            brand="Brand2",
            name="Product 2",
            price=200.0,
            currency="RUB",
        )

        # Проверяем корзину
        cart = store.get_cart(123)
        assert len(cart) == 2

        # Проверяем данные товаров
        product1 = next(item for item in cart if item.product_id == "product-1")
        assert product1.quantity == 1
        assert product1.price == 100.0
        assert product1.currency == "RUB"

        product2 = next(item for item in cart if item.product_id == "product-2")
        assert product2.quantity == 2
        assert product2.price == 200.0
        assert product2.currency == "RUB"

        # Увеличиваем количество
        store.update_quantity(123, "product-1", None, 3)
        cart = store.get_cart(123)
        product1 = next(item for item in cart if item.product_id == "product-1")
        assert product1.quantity == 3

        # Уменьшаем количество
        store.update_quantity(123, "product-2", None, 1)
        cart = store.get_cart(123)
        product2 = next(item for item in cart if item.product_id == "product-2")
        assert product2.quantity == 1

        # Добавляем еще один товар того же типа
        store.add_item(
            123,
            "product-1",
            quantity=2,
            brand="Brand1",
            name="Product 1",
            price=100.0,
            currency="RUB",
        )
        cart = store.get_cart(123)
        product1 = next(item for item in cart if item.product_id == "product-1")
        assert product1.quantity == 5  # 3 + 2 = 5

        # Очищаем корзину
        store.clear_cart(123)
        cart = store.get_cart(123)
        assert len(cart) == 0

    def test_cart_with_different_variants(self):
        """Тест корзины с разными вариантами одного товара"""
        store = CartStore()

        # Добавляем разные варианты одного товара
        store.add_item(
            123,
            "product-1",
            variant_id="red",
            quantity=1,
            brand="Brand1",
            name="Product 1 Red",
            price=100.0,
            currency="RUB",
        )
        store.add_item(
            123,
            "product-1",
            variant_id="blue",
            quantity=2,
            brand="Brand1",
            name="Product 1 Blue",
            price=100.0,
            currency="RUB",
        )

        cart = store.get_cart(123)
        assert len(cart) == 2

        # Проверяем, что варианты разделены
        red_variant = next(item for item in cart if item.variant_id == "red")
        blue_variant = next(item for item in cart if item.variant_id == "blue")

        assert red_variant.quantity == 1
        assert blue_variant.quantity == 2

        # Добавляем еще к красному варианту
        store.add_item(
            123,
            "product-1",
            variant_id="red",
            quantity=3,
            brand="Brand1",
            name="Product 1 Red",
            price=100.0,
            currency="RUB",
        )
        cart = store.get_cart(123)
        red_variant = next(item for item in cart if item.variant_id == "red")
        assert red_variant.quantity == 4  # 1 + 3 = 4

    def test_cart_persistence(self):
        """Тест сохранения и загрузки корзины"""
        store = CartStore()

        # Добавляем товары
        store.add_item(
            123,
            "product-1",
            quantity=2,
            brand="Brand1",
            name="Product 1",
            price=100.0,
            currency="RUB",
        )
        store.add_item(
            123,
            "product-2",
            quantity=1,
            brand="Brand2",
            name="Product 2",
            price=200.0,
            currency="RUB",
        )

        # Проверяем сохранение
        cart1 = store.get_cart(123)
        assert len(cart1) == 2

        # Создаем новый экземпляр store (имитируем перезапуск)
        store2 = CartStore()
        cart2 = store2.get_cart(123)
        assert len(cart2) == 2

        # Проверяем данные
        product1 = next(item for item in cart2 if item.product_id == "product-1")
        assert product1.quantity == 2
        assert product1.price == 100.0
        assert product1.currency == "RUB"

    def test_cart_operations_idempotency(self):
        """Тест идемпотентности операций корзины"""
        store = CartStore()

        # Добавляем товар
        store.add_item(
            123,
            "product-1",
            quantity=1,
            brand="Brand1",
            name="Product 1",
            price=100.0,
            currency="RUB",
        )

        # Множественные обновления количества
        for _ in range(3):
            store.update_quantity(123, "product-1", None, 5)

        cart = store.get_cart(123)
        product1 = next(item for item in cart if item.product_id == "product-1")
        assert product1.quantity == 5  # Должно быть 5, не 15

    def test_cart_error_handling(self):
        """Тест обработки ошибок в корзине"""
        store = CartStore()

        # Попытка обновить несуществующий товар
        result = store.update_quantity(123, "nonexistent", None, 5)
        assert result is None  # Должно вернуть None для несуществующего товара

        # Попытка добавить товар с некорректными данными
        store.add_item(
            123, "", quantity=1, brand="Brand1", name="Product 1", price=100.0, currency="RUB"
        )
        cart = store.get_cart(123)
        # Товар с пустым ID не должен добавиться
        assert len(cart) == 0

    def test_cart_currency_consistency(self):
        """Тест一致ности валют в корзине"""
        store = CartStore()

        # Добавляем товары с разными валютами
        store.add_item(
            123,
            "product-1",
            quantity=1,
            brand="Brand1",
            name="Product 1",
            price=100.0,
            currency="RUB",
        )
        store.add_item(
            123,
            "product-2",
            quantity=1,
            brand="Brand2",
            name="Product 2",
            price=50.0,
            currency="USD",
        )

        cart = store.get_cart(123)
        assert len(cart) == 2

        # Проверяем валюты
        rub_product = next(item for item in cart if item.product_id == "product-1")
        usd_product = next(item for item in cart if item.product_id == "product-2")

        assert rub_product.currency == "RUB"
        assert usd_product.currency == "USD"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
