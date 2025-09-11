"""
Тесты для CartStore - системы управления корзиной
"""

import pytest
import tempfile
from engine.cart_store import CartStore, CartItem


class TestCartItem:
    """Тесты для CartItem"""

    def test_cart_item_creation(self):
        """Тест создания CartItem"""
        item = CartItem(
            product_id="test_123",
            qty=2,
            brand="Test Brand",
            name="Test Product",
            price=1000.0,
            currency="RUB",
        )

        assert item.product_id == "test_123"
        assert item.qty == 2
        assert item.brand == "Test Brand"
        assert item.price == 1000.0

    def test_composite_key_generation(self):
        """Тест генерации композитных ключей"""
        # Без variant_id
        item1 = CartItem(product_id="prod1", qty=1)
        assert item1.get_composite_key() == "prod1:default"

        # С variant_id
        item2 = CartItem(product_id="prod1", variant_id="size-m", qty=1)
        assert item2.get_composite_key() == "prod1:size-m"


class TestCartStore:
    """Тесты для CartStore"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.cart_store = CartStore(base_dir=self.temp_dir)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_item_new(self):
        """Тест добавления нового товара"""
        item = CartItem(product_id="prod1", qty=1, brand="Test", name="Product", price=100.0)

        self.cart_store.add(123, item)
        items = self.cart_store.get(123)

        assert len(items) == 1
        assert items[0].product_id == "prod1"
        assert items[0].qty == 1

    def test_add_item_duplicate(self):
        """Тест добавления существующего товара (идемпотентность)"""
        item1 = CartItem(product_id="prod1", qty=1, price=100.0)
        item2 = CartItem(product_id="prod1", qty=2, price=100.0)

        self.cart_store.add(123, item1)
        self.cart_store.add(123, item2)

        items = self.cart_store.get(123)
        assert len(items) == 1
        assert items[0].qty == 3  # 1 + 2

    def test_inc_quantity(self):
        """Тест увеличения количества"""
        item = CartItem(product_id="prod1", qty=1)
        self.cart_store.add(123, item)

        success = self.cart_store.inc_quantity(123, "prod1")
        assert success == True

        items = self.cart_store.get(123)
        assert items[0].qty == 2

    def test_dec_quantity(self):
        """Тест уменьшения количества"""
        item = CartItem(product_id="prod1", qty=3)
        self.cart_store.add(123, item)

        success = self.cart_store.dec_quantity(123, "prod1")
        assert success == True

        items = self.cart_store.get(123)
        assert items[0].qty == 2

    def test_dec_quantity_to_zero(self):
        """Тест уменьшения количества до 0 (удаление товара)"""
        item = CartItem(product_id="prod1", qty=1)
        self.cart_store.add(123, item)

        success = self.cart_store.dec_quantity(123, "prod1")
        assert success == True

        items = self.cart_store.get(123)
        assert len(items) == 0  # Товар удален

    def test_remove_item(self):
        """Тест удаления товара"""
        item = CartItem(product_id="prod1", qty=1)
        self.cart_store.add(123, item)

        self.cart_store.remove(123, "prod1")
        items = self.cart_store.get(123)
        assert len(items) == 0

    def test_clear_cart(self):
        """Тест очистки корзины"""
        self.cart_store.add(123, CartItem(product_id="prod1", qty=1))
        self.cart_store.add(123, CartItem(product_id="prod2", qty=2))

        self.cart_store.clear(123)
        items = self.cart_store.get(123)
        assert len(items) == 0

    def test_get_cart_count(self):
        """Тест подсчета общего количества товаров"""
        self.cart_store.add(123, CartItem(product_id="prod1", qty=2))
        self.cart_store.add(123, CartItem(product_id="prod2", qty=3))

        count = self.cart_store.get_cart_count(123)
        assert count == 5

    def test_get_cart_total(self):
        """Тест подсчета общей суммы"""
        self.cart_store.add(123, CartItem(product_id="prod1", qty=2, price=100.0))
        self.cart_store.add(123, CartItem(product_id="prod2", qty=1, price=200.0))

        item_count, total_price = self.cart_store.get_cart_total(123)
        assert item_count == 3
        assert total_price == 400.0  # 2*100 + 1*200

    def test_has_item(self):
        """Тест проверки наличия товара"""
        self.cart_store.add(123, CartItem(product_id="prod1", qty=1))

        assert self.cart_store.has_item(123, "prod1") == True
        assert self.cart_store.has_item(123, "prod2") == False


if __name__ == "__main__":
    pytest.main([__file__])
