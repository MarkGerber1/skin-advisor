"""
Тесты улучшенной корзины с полной информацией о товарах
"""

import pytest
from datetime import datetime
from engine.cart_store import CartStore, CartItem


def test_cart_item_extended_fields():
    """Тест расширенных полей CartItem"""
    cart_item = CartItem(
        product_id="test_123",
        qty=2,
        brand="Test Brand",
        name="Test Product",
        price=1500.0,
        price_currency="₽",
        ref_link="https://example.com/product",
        explain="Подходит для вашего цветотипа",
        category="foundation",
        in_stock=True,
        added_at=datetime.now().isoformat()
    )
    
    assert cart_item.product_id == "test_123"
    assert cart_item.qty == 2
    assert cart_item.brand == "Test Brand"
    assert cart_item.name == "Test Product"
    assert cart_item.price == 1500.0
    assert cart_item.price_currency == "₽"
    assert cart_item.ref_link == "https://example.com/product"
    assert cart_item.explain == "Подходит для вашего цветотипа"
    assert cart_item.category == "foundation"
    assert cart_item.in_stock is True
    assert cart_item.added_at is not None


def test_cart_store_enhanced_functionality():
    """Тест расширенной функциональности CartStore"""
    store = CartStore(base_dir="test_carts")
    user_id = 12345
    
    # Очищаем корзину перед тестом
    store.clear(user_id)
    
    # Создаем полный CartItem
    cart_item = CartItem(
        product_id="prod_456",
        qty=1,
        brand="Beautiful Brand",
        name="Amazing Foundation",
        price=2200.0,
        price_currency="₽",
        ref_link="https://shop.example.com/prod_456?aff=S1",
        explain="Идеально подходит для теплого подтона",
        category="foundation",
        in_stock=True,
        added_at=datetime.now().isoformat()
    )
    
    # Добавляем в корзину
    store.add(user_id, cart_item)
    
    # Проверяем что товар добавился
    items = store.get(user_id)
    assert len(items) == 1
    
    saved_item = items[0]
    assert saved_item.product_id == "prod_456"
    assert saved_item.brand == "Beautiful Brand"
    assert saved_item.name == "Amazing Foundation"
    assert saved_item.price == 2200.0
    assert saved_item.ref_link == "https://shop.example.com/prod_456?aff=S1"
    assert saved_item.explain == "Идеально подходит для теплого подтона"
    assert saved_item.category == "foundation"
    assert saved_item.in_stock is True
    
    # Тест обновления количества
    store.set_qty(user_id, "prod_456", 3)
    items = store.get(user_id)
    assert items[0].qty == 3
    
    # Тест удаления
    store.remove(user_id, "prod_456")
    items = store.get(user_id)
    assert len(items) == 0
    
    # Очищаем после теста
    store.clear(user_id)


def test_cart_multiple_products():
    """Тест корзины с несколькими товарами"""
    store = CartStore(base_dir="test_carts")
    user_id = 54321
    
    store.clear(user_id)
    
    # Добавляем несколько товаров
    products = [
        CartItem(
            product_id="foundation_001",
            qty=1,
            brand="Brand A",
            name="Foundation Light",
            price=1800.0,
            category="foundation",
            in_stock=True,
            explain="Светлый тон для холодного подтона"
        ),
        CartItem(
            product_id="lipstick_002", 
            qty=2,
            brand="Brand B",
            name="Red Lipstick",
            price=1200.0,
            category="lipstick",
            in_stock=False,  # Недоступен
            explain="Яркий красный для контрастного типа"
        ),
        CartItem(
            product_id="mascara_003",
            qty=1,
            brand="Brand C", 
            name="Volume Mascara",
            price=950.0,
            category="mascara",
            in_stock=True,
            explain="Добавляет объем ресницам"
        )
    ]
    
    for product in products:
        store.add(user_id, product)
    
    # Проверяем что все товары добавились
    items = store.get(user_id)
    assert len(items) == 3
    
    # Проверяем товары по категориям
    foundations = [item for item in items if item.category == "foundation"]
    lipsticks = [item for item in items if item.category == "lipstick"]
    mascaras = [item for item in items if item.category == "mascara"]
    
    assert len(foundations) == 1
    assert len(lipsticks) == 1
    assert len(mascaras) == 1
    
    # Проверяем доступность
    available_items = [item for item in items if item.in_stock]
    unavailable_items = [item for item in items if not item.in_stock]
    
    assert len(available_items) == 2
    assert len(unavailable_items) == 1
    assert unavailable_items[0].product_id == "lipstick_002"
    
    # Подсчитываем общую стоимость доступных товаров
    total_price = sum(item.price * item.qty for item in available_items)
    assert total_price == 1800.0 + 950.0  # foundation + mascara
    
    store.clear(user_id)


def test_cart_affiliate_links():
    """Тест партнерских ссылок в корзине"""
    store = CartStore(base_dir="test_carts")
    user_id = 99999
    
    store.clear(user_id)
    
    cart_item = CartItem(
        product_id="test_affiliate",
        qty=1,
        brand="Test Brand",
        name="Test Product",
        price=1000.0,
        ref_link="https://goldapple.ru/product/123?aff=S1&utm_source=skinbot",
        in_stock=True
    )
    
    store.add(user_id, cart_item)
    items = store.get(user_id)
    
    assert len(items) == 1
    ref_link = items[0].ref_link
    
    # Проверяем что партнерская ссылка содержит нужные параметры
    assert "aff=S1" in ref_link
    assert "goldapple.ru" in ref_link
    
    store.clear(user_id)


if __name__ == "__main__":
    print("🧪 Запуск тестов улучшенной корзины...")
    
    test_cart_item_extended_fields()
    print("✅ test_cart_item_extended_fields - PASSED")
    
    test_cart_store_enhanced_functionality()
    print("✅ test_cart_store_enhanced_functionality - PASSED")
    
    test_cart_multiple_products()
    print("✅ test_cart_multiple_products - PASSED")
    
    test_cart_affiliate_links()
    print("✅ test_cart_affiliate_links - PASSED")
    
    print("\n🎉 Все тесты корзины прошли успешно!")

