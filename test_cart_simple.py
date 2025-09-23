#!/usr/bin/env python3
"""
🛒 Simple Cart Tests (No Async)

Basic tests for Cart v2 models without pytest-asyncio
"""

from engine.cart_store import Cart, CartItem


def test_cart_item():
    """Test CartItem model"""
    print("Testing CartItem...")

    # Test composite key
    item1 = CartItem(product_id="prod1", variant_id="var1", name="Test")
    assert item1.get_composite_key() == "prod1:var1"

    item2 = CartItem(product_id="prod1", name="Test")
    assert item2.get_composite_key() == "prod1:"

    # Test initialization
    item = CartItem(product_id="test_prod", name="Test Product", price=1990, currency="RUB")
    assert item.product_id == "test_prod"
    assert item.price == 1990
    assert item.currency == "RUB"
    assert item.qty == 1

    print("✅ CartItem tests passed")


def test_cart_operations():
    """Test Cart operations"""
    print("Testing Cart operations...")

    cart = Cart(user_id=123)

    # Test empty cart
    cart.recalculate()
    assert cart.subtotal == 0
    assert len(cart.items) == 0

    # Test single item
    item = CartItem(product_id="prod1", name="Test Product", price=1990, currency="RUB", qty=2)
    cart.add_item(item)
    assert len(cart.items) == 1
    assert cart.subtotal == 3980  # 1990 * 2

    # Test idempotent add
    item2 = CartItem(product_id="prod1", variant_id="", name="Test Product", price=1990, qty=3)
    cart.add_item(item2)
    assert len(cart.items) == 1  # Still 1 item
    assert cart.items["prod1:"].qty == 5  # 2 + 3

    # Test quantity operations
    cart.set_quantity("prod1:", 3)
    assert cart.items["prod1:"].qty == 3
    assert cart.subtotal == 5970  # 1990 * 3

    # Test remove
    cart.set_quantity("prod1:", 0)
    assert len(cart.items) == 0

    print("✅ Cart operations tests passed")


def test_mixed_currencies():
    """Test mixed currencies handling"""
    print("Testing mixed currencies...")

    cart = Cart(user_id=123)

    item_rub = CartItem(product_id="prod1", name="RUB Product", price=1990, currency="RUB", qty=1)

    item_usd = CartItem(product_id="prod2", name="USD Product", price=2500, currency="USD", qty=1)

    cart.add_item(item_rub)
    cart.add_item(item_usd)

    assert len(cart.items) == 2
    assert cart.needs_review  # Mixed currencies
    assert cart.subtotal == 4490  # 1990 + 2500
    assert cart.currency == "RUB"  # First currency

    print("✅ Mixed currencies test passed")


if __name__ == "__main__":
    print("🛒 Running Simple Cart Tests")
    print("=" * 40)

    test_cart_item()
    test_cart_operations()
    test_mixed_currencies()

    print("=" * 40)
    print("🎉 ALL TESTS PASSED!")
