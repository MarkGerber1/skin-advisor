"""Tests for services.cart_store and cart handlers."""

import importlib
import pytest

import services.cart_store as cart_store_module


class _DummySecurity:
    spam_keywords = []
    allow_pin = True
    pin_whitelist = []


class _DummySettings:
    security = _DummySecurity()


@pytest.fixture
def store(tmp_path):
    """Provide isolated CartStore instance per test."""
    cart_store_module._cart_store_instance = None
    store = cart_store_module.CartStore()
    store.data_dir = tmp_path / "carts"
    store.data_dir.mkdir(parents=True, exist_ok=True)
    store._carts.clear()
    return store


@pytest.fixture
def cart_module(store, monkeypatch):
    """Bind cart handler module to the isolated store."""
    monkeypatch.setattr("config.env.get_settings", lambda: _DummySettings())
    cart_module = importlib.reload(importlib.import_module("bot.handlers.cart"))
    cart_module.store = store
    cart_module._last_operations.clear()
    return cart_module


def test_add_idempotent_merge(store):
    user_id = 100
    store.add_item(user_id, "prod-1", quantity=1, price=100.0, currency="RUB")
    store.add_item(user_id, "prod-1", quantity=2, price=100.0, currency="RUB")

    cart = store.get_cart(user_id)
    assert len(cart) == 1
    assert cart[0].qty == 3


def test_inc_dec_delete(store):
    user_id = 101
    store.add_item(user_id, "prod-2", quantity=1)

    success, qty = store.inc_quantity(user_id, "prod-2", None)
    assert success and qty == 2

    success, qty = store.dec_quantity(user_id, "prod-2", None)
    assert success and qty == 1

    success, qty = store.dec_quantity(user_id, "prod-2", None)
    assert success and qty == 0
    assert store.get_cart(user_id) == []


def test_totals_quantity_price_tuple(store):
    user_id = 102
    store.add_item(user_id, "prod-a", quantity=2, price=150.0, currency="RUB")
    store.add_item(user_id, "prod-b", quantity=1, price=200.0, currency="RUB")

    total_qty, total_price, currency = store.get_cart_total(user_id)

    assert total_qty == 3
    assert total_price == pytest.approx(500.0)
    assert currency == "RUB"


def test_variant_validation(store):
    user_id = 103
    store.add_item(user_id, "prod-v", variant_id="shade-1", quantity=1)
    store.add_item(user_id, "prod-v", variant_id="shade-2", quantity=1)

    cart = store.get_cart(user_id)
    assert len(cart) == 2
    assert {item.variant_id for item in cart} == {"shade-1", "shade-2"}


def test_currency_conflict_flag(store, cart_module):
    user_id = 104
    store.add_item(user_id, "prod-rub", quantity=1, price=100.0, currency="RUB")
    store.add_item(user_id, "prod-usd", quantity=1, price=10.0, currency="USD")

    text, _, _, summary = cart_module._compose_cart_view(user_id)

    assert summary["currency_warning"] is True
    assert "⚠" in text

