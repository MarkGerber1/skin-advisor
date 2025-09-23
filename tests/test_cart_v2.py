#!/usr/bin/env python3
"""
🛒 Cart v2 Unit Tests

Tests for CartStore, Cart, and CartItem models
"""

import tempfile
import os
import asyncio
from engine.cart_store import CartStore, Cart, CartItem


class TestCartItem:
    """Test CartItem model"""

    def test_get_composite_key(self):
        """Test composite key generation"""
        # With variant
        item = CartItem(product_id="prod1", variant_id="var1", name="Test")
        assert item.get_composite_key() == "prod1:var1"

        # Without variant
        item = CartItem(product_id="prod1", name="Test")
        assert item.get_composite_key() == "prod1:"

    def test_initialization(self):
        """Test CartItem initialization with defaults"""
        item = CartItem(
            product_id="test_prod", name="Test Product", price=1990, currency="RUB"  # 19.90 RUB
        )

        assert item.product_id == "test_prod"
        assert item.variant_id is None
        assert item.name == "Test Product"
        assert item.price == 1990
        assert item.currency == "RUB"
        assert item.qty == 1
        assert item.source == ""
        assert item.link == ""
        assert isinstance(item.meta, dict)


class TestCart:
    """Test Cart model"""

    def test_empty_cart(self):
        """Test empty cart behavior"""
        cart = Cart(user_id=123)
        cart.recalculate()

        assert cart.subtotal == 0
        assert cart.currency == "RUB"
        assert not cart.needs_review
        assert len(cart.items) == 0

    def test_single_item_cart(self):
        """Test cart with one item"""
        cart = Cart(user_id=123)
        item = CartItem(product_id="prod1", name="Test Product", price=1990, currency="RUB", qty=2)

        cart.add_item(item)
        assert len(cart.items) == 1
        assert cart.subtotal == 3980  # 1990 * 2
        assert cart.currency == "RUB"
        assert not cart.needs_review

    def test_multiple_currencies(self):
        """Test cart with mixed currencies"""
        cart = Cart(user_id=123)

        item_rub = CartItem(
            product_id="prod1", name="RUB Product", price=1990, currency="RUB", qty=1
        )

        item_usd = CartItem(
            product_id="prod2",
            name="USD Product",
            price=2500,  # 25.00 USD in cents
            currency="USD",
            qty=1,
        )

        cart.add_item(item_rub)
        cart.add_item(item_usd)

        assert len(cart.items) == 2
        assert cart.needs_review  # Mixed currencies
        assert cart.subtotal == 4490  # 1990 + 2500
        assert cart.currency == "RUB"  # First currency used as primary

    def test_idempotent_add(self):
        """Test that adding same product+variant increases quantity"""
        cart = Cart(user_id=123)

        item1 = CartItem(
            product_id="prod1", variant_id="size-m", name="Test Product", price=1990, qty=2
        )

        item2 = CartItem(
            product_id="prod1", variant_id="size-m", name="Test Product", price=1990, qty=3
        )

        cart.add_item(item1)
        cart.add_item(item2)

        assert len(cart.items) == 1
        key = "prod1:size-m"
        assert cart.items[key].qty == 5  # 2 + 3
        assert cart.subtotal == 9950  # 1990 * 5

    def test_quantity_operations(self):
        """Test quantity modification operations"""
        cart = Cart(user_id=123)
        item = CartItem(product_id="prod1", name="Test", price=1000, qty=1)
        cart.add_item(item)

        # Set quantity
        cart.set_quantity("prod1:", 5)
        assert cart.items["prod1:"].qty == 5

        # Set to 0 (should remove)
        cart.set_quantity("prod1:", 0)
        assert "prod1:" not in cart.items

    def test_clear_cart(self):
        """Test cart clearing"""
        cart = Cart(user_id=123)
        item = CartItem(product_id="prod1", name="Test", price=1000)
        cart.add_item(item)

        assert len(cart.items) == 1
        cart.clear()
        assert len(cart.items) == 0
        assert cart.subtotal == 0


class TestCartStore:
    """Test CartStore persistence"""

    def setup_method(self):
        """Setup temporary directory for tests"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup temporary files"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_idempotent_merge(self):
        """Test idempotent add with quantity merging"""
        store = CartStore(self.temp_dir)

        # Create test item
        item = CartItem(
            product_id="test_prod",
            variant_id="variant_1",
            name="Test Product",
            price=1990,
            currency="RUB",
            source="goldapple",
            link="https://example.com",
            qty=2,
        )

        async def test():
            # First add
            cart1 = await store.add(123, item)
            assert len(cart1.items) == 1
            assert cart1.items["test_prod:variant_1"].qty == 2

            # Second add of same item should merge quantities
            cart2 = await store.add(123, item)
            assert len(cart2.items) == 1
            assert cart2.items["test_prod:variant_1"].qty == 4  # 2 + 2

        import asyncio

        asyncio.run(test())

    def test_set_qty_operations(self):
        """Test quantity setting operations"""
        store = CartStore(self.temp_dir)

        async def test():
            # Add item
            item = CartItem(product_id="prod1", name="Test", price=1000, qty=1)
            cart = await store.add(123, item)

            # Increase quantity
            cart = await store.set_qty(123, "prod1:", 5)
            assert cart.items["prod1:"].qty == 5

            # Set to 0 (should remove)
            cart = await store.set_qty(123, "prod1:", 0)
            assert "prod1:" not in cart.items

        import asyncio

        asyncio.run(test())

    def test_remove_item(self):
        """Test item removal"""
        store = CartStore(self.temp_dir)

        async def test():
            # Add items
            item1 = CartItem(product_id="prod1", name="Test 1", price=1000)
            item2 = CartItem(product_id="prod2", name="Test 2", price=2000)

            await store.add(123, item1)
            await store.add(123, item2)

            cart = await store.get(123)
            assert len(cart.items) == 2

            # Remove one item
            cart = await store.remove(123, "prod1:")
            assert len(cart.items) == 1
            assert "prod2:" in cart.items

        import asyncio

        asyncio.run(test())

    def test_clear_cart(self):
        """Test cart clearing"""
        store = CartStore(self.temp_dir)

        async def test():
            # Add item
            item = CartItem(product_id="prod1", name="Test", price=1000)
            await store.add(123, item)

            cart = await store.get(123)
            assert len(cart.items) == 1

            # Clear cart
            await store.clear(123)
            cart = await store.get(123)
            assert len(cart.items) == 0

        import asyncio

        asyncio.run(test())

    def test_persistence(self):
        """Test data persistence across store instances"""
        # First store instance
        store1 = CartStore(self.temp_dir)

        async def test():
            item = CartItem(product_id="persistent", name="Persistent Item", price=1500)
            await store1.add(456, item)

            # Second store instance (simulates app restart)
            store2 = CartStore(self.temp_dir)
            cart = await store2.get(456)

            assert len(cart.items) == 1
            assert cart.items["persistent:"].name == "Persistent Item"
            assert cart.items["persistent:"].price == 1500

        import asyncio

        asyncio.run(test())


if __name__ == "__main__":
    pytest.main([__file__])
