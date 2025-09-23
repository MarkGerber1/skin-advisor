"""
Unit tests for CartStore
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from services.cart_store import CartStore


class TestCartStore(unittest.TestCase):
    """Test CartStore functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        CartStore._instance = None
        self.store = CartStore()
        self.store.data_dir = self.temp_dir / "carts"
        self.store.data_dir.mkdir(parents=True, exist_ok=True)
        self.store._carts.clear()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
        CartStore._instance = None

    def test_add_item_new_product(self):
        """Test adding a new product to cart"""
        user_id = 12345
        item, currency_conflict = self.store.add_item(
            user_id=user_id,
            product_id="test_product",
            variant_id="variant1",
            quantity=2,
            brand="Test Brand",
            name="Test Product",
            price=100.0,
        )

        self.assertEqual(item.product_id, "test_product")
        self.assertEqual(item.variant_id, "variant1")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.brand, "Test Brand")
        self.assertEqual(item.price, 100.0)

        # Check cart contents
        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0].quantity, 2)

    def test_add_item_existing_product(self):
        """Test adding quantity to existing product"""
        user_id = 12345

        # Add first item
        self.store.add_item(user_id, "test_product", "variant1", 2)

        # Add to existing item
        self.store.add_item(user_id, "test_product", "variant1", 3)

        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0].quantity, 5)  # 2 + 3

    def test_update_quantity(self):
        """Test updating item quantity"""
        user_id = 12345

        # Add item
        self.store.add_item(user_id, "test_product", "variant1", 5)

        # Update quantity
        success = self.store.update_quantity(user_id, "test_product", "variant1", 3)

        self.assertTrue(success)
        cart = self.store.get_cart(user_id)
        self.assertEqual(cart[0].quantity, 3)

    def test_update_quantity_remove_when_zero(self):
        """Test that item is removed when quantity set to 0"""
        user_id = 12345

        # Add item
        self.store.add_item(user_id, "test_product", "variant1", 5)

        # Set quantity to 0
        success = self.store.update_quantity(user_id, "test_product", "variant1", 0)

        self.assertTrue(success)
        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 0)

    def test_remove_item(self):
        """Test removing item from cart"""
        user_id = 12345

        # Add item
        self.store.add_item(user_id, "test_product", "variant1", 5)

        # Remove item
        success = self.store.remove_item(user_id, "test_product", "variant1")

        self.assertTrue(success)
        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 0)

    def test_clear_cart(self):
        """Test clearing entire cart"""
        user_id = 12345

        # Add multiple items
        self.store.add_item(user_id, "product1", "variant1", 2)
        self.store.add_item(user_id, "product2", "variant2", 3)

        # Clear cart
        self.store.clear_cart(user_id)

        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 0)

    def test_get_cart_total(self):
        """Test calculating cart total"""
        user_id = 12345

        # Add items with prices
        self.store.add_item(user_id, "product1", "variant1", 2, price=100.0)
        self.store.add_item(user_id, "product2", "variant2", 1, price=200.0)

        total_qty, total_price, currency = self.store.get_cart_total(user_id)

        self.assertEqual(total_qty, 3)  # 2 + 1
        self.assertEqual(total_price, 400.0)  # 2*100 + 1*200
        self.assertEqual(currency, "RUB")

    def test_persistence(self):
        """Test that cart data persists across store instances"""
        user_id = 12345

        # Add item to first store instance
        self.store.add_item(user_id, "test_product", "variant1", 5, price=100.0)

        # Create new store instance (simulating restart)
        new_store = CartStore()
        new_store.data_dir = self.temp_dir / "carts"

        # Check that data was loaded
        cart = new_store.get_cart(user_id)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0].quantity, 5)
        self.assertEqual(cart[0].price, 100.0)

    def test_currency_conflict_detection(self):
        """Test currency conflict detection"""
        user_id = 12345

        # Add first item with RUB
        item1, conflict1 = self.store.add_item(
            user_id=user_id,
            product_id="rub_product",
            name="RUB Product",
            price=100.0,
            currency="RUB",
        )
        self.assertFalse(conflict1)

        # Add second item with RUB (no conflict)
        item2, conflict2 = self.store.add_item(
            user_id=user_id,
            product_id="rub_product2",
            name="RUB Product 2",
            price=200.0,
            currency="RUB",
        )
        self.assertFalse(conflict2)

        # Add item with different currency (should conflict)
        item3, conflict3 = self.store.add_item(
            user_id=user_id,
            product_id="usd_product",
            name="USD Product",
            price=50.0,
            currency="USD",
        )
        self.assertTrue(conflict3)

    def test_add_same_product_twice(self):
        """Test adding the same product twice increases quantity"""
        user_id = 12345

        # Add first time
        item1, conflict1 = self.store.add_item(
            user_id=user_id,
            product_id="same_product",
            variant_id="variant1",
            quantity=2,
            name="Same Product",
            price=100.0,
        )
        self.assertEqual(item1.qty, 2)

        # Add same product again
        item2, conflict2 = self.store.add_item(
            user_id=user_id,
            product_id="same_product",
            variant_id="variant1",
            quantity=3,
            name="Same Product",
            price=100.0,
        )
        self.assertEqual(item2.qty, 5)  # 2 + 3

        # Check cart has only one item
        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 1)

    def test_cart_totals_calculation(self):
        """Test cart totals calculation"""
        user_id = 12345

        # Add items
        self.store.add_item(user_id, "p1", name="Product 1", price=100.0, quantity=2)
        self.store.add_item(user_id, "p2", name="Product 2", price=50.0, quantity=1)

        total_qty, total_price, currency = self.store.get_cart_total(user_id)
        self.assertEqual(total_qty, 3)  # 2 + 1
        self.assertEqual(total_price, 250.0)  # 100*2 + 50*1
        self.assertEqual(currency, "RUB")

    def test_dec_to_zero_removes_item(self):
        """Test that decreasing quantity to 0 removes item"""
        user_id = 12345

        # Add item
        self.store.add_item(user_id, "test_product", quantity=1, name="Test", price=100.0)

        # Decrease to 0 should remove
        success = self.store.update_quantity(user_id, "test_product", None, 0)
        self.assertTrue(success)

        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 0)


class TestCartIntegration(unittest.TestCase):
    """Integration tests for cart functionality"""

    def setUp(self):
        """Set up test fixtures"""
        CartStore._instance = None
        self.store = CartStore()
        # Clear all data for clean test state
        self.store._carts.clear()
        self.store._save_all_carts()

    def test_full_cart_flow(self):
        """Test complete cart flow: add -> modify -> checkout"""
        user_id = 99999

        # Step 1: Add first product
        item1, conflict1 = self.store.add_item(
            user_id=user_id,
            product_id="cleanser-001",
            name="Очищающий гель CeraVe",
            price=1590.0,
            currency="RUB",
            source="goldapple",
            ref_link="https://goldapple.ru/cleanser-001",
        )
        self.assertFalse(conflict1)
        self.assertEqual(item1.qty, 1)

        # Step 2: Add second product
        item2, conflict2 = self.store.add_item(
            user_id=user_id,
            product_id="toner-002",
            name="Тоник La Roche-Posay",
            price=2890.0,
            currency="RUB",
            source="goldapple",
            ref_link="https://goldapple.ru/toner-002",
        )
        self.assertFalse(conflict2)

        # Step 3: Increase quantity of first product
        success = self.store.update_quantity(user_id, "cleanser-001", None, 3)
        self.assertTrue(success)

        # Step 4: Add third product
        item3, conflict3 = self.store.add_item(
            user_id=user_id,
            product_id="serum-003",
            name="Сыворотка The Ordinary",
            price=1990.0,
            currency="RUB",
            source="goldapple",
            ref_link="https://goldapple.ru/serum-003",
        )
        self.assertFalse(conflict3)

        # Step 5: Decrease quantity of third product to 0 (should remove)
        success = self.store.update_quantity(user_id, "serum-003", None, 0)
        self.assertTrue(success)

        # Step 6: Check final cart state
        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 2)  # Two items left

        # Check quantities
        item1_final = next(i for i in cart if i.product_id == "cleanser-001")
        item2_final = next(i for i in cart if i.product_id == "toner-002")

        self.assertEqual(item1_final.qty, 3)
        self.assertEqual(item2_final.qty, 1)

        # Check totals
        total_qty, total_price, currency = self.store.get_cart_total(user_id)
        self.assertEqual(total_qty, 4)  # 3 + 1
        self.assertEqual(total_price, 1590 * 3 + 2890 * 1)  # 4770 + 2890 = 7660
        self.assertEqual(currency, "RUB")

        # Step 7: Clear cart
        removed_count = self.store.clear_cart(user_id)
        self.assertEqual(removed_count, 2)

        # Check cart is empty
        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 0)

    def test_cart_rendering(self):
        """Test cart text rendering"""
        from bot.handlers.cart_v2 import render_cart

        # Use unique user ID for this test
        user_id = 999980

        # Ensure clean state
        self.store.clear_cart(user_id)

        # Add products
        self.store.add_item(user_id, "test-1", name="Тестовый продукт 1", price=1000.0, quantity=2)
        self.store.add_item(user_id, "test-2", name="Тестовый продукт 2", price=500.0, quantity=1)

        cart_items = self.store.get_cart(user_id)
        text = render_cart(cart_items)

        # Check that text contains expected elements
        self.assertIn("🛒 Ваша корзина", text)
        self.assertIn("Тестовый продукт 1", text)
        self.assertIn("Тестовый продукт 2", text)
        self.assertIn("1 000", text)  # 1000 formatted
        self.assertIn("500", text)  # 500 formatted
        self.assertIn("2 000", text)  # 1000 * 2 result
        self.assertIn("Итого: 3 шт × 2 500", text)

        # Test empty cart
        self.store.clear_cart(user_id)
        cart_items = self.store.get_cart(user_id)
        text = render_cart(cart_items)
        self.assertIn("Пока пусто", text)

    def test_cart_after_test_flow(self):
        """Test cart functionality after completing a skincare test"""
        user_id = 77777

        # Simulate recommendations after test completion
        # This would normally come from SelectorV2, but we'll mock it
        recommendations = [
            {
                "id": "cleanser-cerave",
                "name": "Очищающий гель CeraVe",
                "price": 1590,
                "category": "cleanser",
                "source": "goldapple"
            },
            {
                "id": "toner-lrp",
                "name": "Успокаивающий тоник La Roche-Posay",
                "price": 2890,
                "category": "toner",
                "source": "goldapple"
            },
            {
                "id": "serum-ordinary",
                "name": "Сыворотка The Ordinary",
                "price": 1990,
                "category": "serum",
                "source": "goldapple"
            }
        ]

        # User adds first product to cart
        item1, conflict1 = self.store.add_item(
            user_id=user_id,
            product_id="cleanser-cerave",
            name="Очищающий гель CeraVe",
            price=1590.0,
            currency="RUB",
            source="goldapple",
            ref_link="https://goldapple.ru/cleanser-cerave"
        )
        self.assertFalse(conflict1)

        # User adds second product
        item2, conflict2 = self.store.add_item(
            user_id=user_id,
            product_id="toner-lrp",
            name="Успокаивающий тоник La Roche-Posay",
            price=2890.0,
            currency="RUB",
            source="goldapple",
            ref_link="https://goldapple.ru/toner-lrp"
        )
        self.assertFalse(conflict2)

        # User increases quantity of first product
        success = self.store.update_quantity(user_id, "cleanser-cerave", None, 2)
        self.assertTrue(success)

        # Check cart state
        cart = self.store.get_cart(user_id)
        self.assertEqual(len(cart), 2)

        total_qty, total_price, currency = self.store.get_cart_total(user_id)
        self.assertEqual(total_qty, 3)  # 2 + 1
        self.assertEqual(total_price, 1590*2 + 2890*1)  # 3180 + 2890 = 6070
        self.assertEqual(currency, "RUB")

        # User decides to checkout
        # Cart should contain all selected products with correct quantities
        self.assertEqual(len(cart), 2)
        cleanser = next(i for i in cart if i.product_id == "cleanser-cerave")
        toner = next(i for i in cart if i.product_id == "toner-lrp")

        self.assertEqual(cleanser.qty, 2)
        self.assertEqual(cleanser.price, 1590.0)
        self.assertEqual(toner.qty, 1)
        self.assertEqual(toner.price, 2890.0)

        # All products should have proper links for checkout
        self.assertTrue(cleanser.ref_link.startswith("https://"))
        self.assertTrue(toner.ref_link.startswith("https://"))

    def test_cart_buttons_callback_format(self):
        """Test that cart button callbacks are properly formatted"""
        from bot.handlers.cart_v2 import build_cart_keyboard

        user_id = 88888

        # Add products
        self.store.add_item(user_id, "test-p1", name="Product 1", price=1000.0, variant_id="v1")
        self.store.add_item(user_id, "test-p2", name="Product 2", price=2000.0, variant_id="v2")

        cart_items = self.store.get_cart(user_id)
        keyboard = build_cart_keyboard(cart_items)

        # Extract callback data from buttons
        callbacks = []
        for row in keyboard.inline_keyboard:
            for button in row:
                if hasattr(button, 'callback_data') and button.callback_data:
                    callbacks.append(button.callback_data)

        # Should have callbacks for inc, dec, rm operations
        inc_callbacks = [c for c in callbacks if c.startswith('cart:inc:')]
        dec_callbacks = [c for c in callbacks if c.startswith('cart:dec:')]
        rm_callbacks = [c for c in callbacks if c.startswith('cart:rm:')]

        self.assertEqual(len(inc_callbacks), 2)  # One for each product
        self.assertEqual(len(dec_callbacks), 2)
        self.assertEqual(len(rm_callbacks), 2)

        # Check format: cart:inc:product_id:variant_id
        for callback in inc_callbacks:
            parts = callback.split(':')
            self.assertEqual(len(parts), 4)
            self.assertEqual(parts[0], 'cart')
            self.assertEqual(parts[1], 'inc')
            self.assertTrue(parts[2].startswith('test-p'))
            self.assertTrue(parts[3] in ['v1', 'v2', 'none'])


if __name__ == "__main__":
    unittest.main()
