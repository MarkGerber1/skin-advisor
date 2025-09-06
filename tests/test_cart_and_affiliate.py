"""Тесты для корзины и партнерских ссылок"""

import pytest
from unittest.mock import Mock, patch
from services.cart_store import CartItem, CartStore
from services.affiliates import AffiliateService


class TestCartItem:
    """Тесты для модели CartItem"""

    def test_cart_item_creation(self):
        """Тест создания CartItem с дефолтными значениями"""
        item = CartItem(
            product_id="test-123",
            quantity=2,
            brand="Test Brand",
            name="Test Product"
        )

        assert item.product_id == "test-123"
        assert item.quantity == 2
        assert item.qty == 2  # алиас
        assert item.brand == "Test Brand"
        assert item.name == "Test Product"
        assert item.variant_name is None
        assert item.in_stock is True
        assert item.ref_link is None
        assert item.image_url is None

    def test_cart_item_with_optional_fields(self):
        """Тест CartItem с опциональными полями"""
        item = CartItem(
            product_id="test-123",
            variant_name="Variant A",
            in_stock=False,
            ref_link="https://example.com/affiliate",
            image_url="https://example.com/image.jpg"
        )

        assert item.variant_name == "Variant A"
        assert item.in_stock is False
        assert item.ref_link == "https://example.com/affiliate"
        assert item.image_url == "https://example.com/image.jpg"


class TestCartStore:
    """Тесты для CartStore"""

    def test_add_item_creates_new(self):
        """Тест добавления нового товара"""
        store = CartStore()
        item = store.add_item(
            user_id=123,
            product_id="test-123",
            quantity=1,
            brand="Test Brand",
            name="Test Product"
        )

        assert item.product_id == "test-123"
        assert item.quantity == 1
        assert len(store.get_cart(123)) == 1

    def test_add_item_increments_existing(self):
        """Тест инкремента количества существующего товара"""
        store = CartStore()

        # Добавляем первый раз
        store.add_item(user_id=123, product_id="test-123", quantity=1)

        # Добавляем второй раз тот же товар
        store.add_item(user_id=123, product_id="test-123", quantity=2)

        cart = store.get_cart(123)
        assert len(cart) == 1
        assert cart[0].quantity == 3

    def test_update_quantity(self):
        """Тест обновления количества"""
        store = CartStore()
        store.add_item(user_id=123, product_id="test-123", quantity=1)

        store.update_quantity(123, "test-123", None, 5)

        cart = store.get_cart(123)
        assert cart[0].quantity == 5


class TestAffiliateService:
    """Тесты для AffiliateService"""

    @patch('services.affiliates.get_settings')
    def test_build_ref_link_goldapple(self, mock_settings):
        """Тест генерации ссылки для Gold Apple"""
        mock_settings.return_value = Mock()
        service = AffiliateService()

        product = {
            'id': 'goldapple-123',
            'link': 'https://goldapple.ru/product/123',
            'brand': 'Gold Apple'
        }

        result = service.build_ref_link(product)
        assert result is not None
        assert 'partner=' in result
        assert 'goldapple.ru' in result

    @patch('services.affiliates.get_settings')
    def test_build_ref_link_no_config(self, mock_settings):
        """Тест генерации ссылки при отсутствии конфигурации"""
        mock_settings.return_value = None
        service = AffiliateService()

        product = {
            'id': 'test-123',
            'link': 'https://example.com/product/123'
        }

        result = service.build_ref_link(product)
        assert result == 'https://example.com/product/123'  # Возвращает оригинальную ссылку

    @patch('services.affiliates.get_settings')
    def test_build_ref_link_unknown_source(self, mock_settings):
        """Тест генерации ссылки для неизвестного источника"""
        mock_settings.return_value = Mock()
        service = AffiliateService()

        product = {
            'id': 'unknown-123',
            'link': 'https://unknown-shop.com/product/123'
        }

        result = service.build_ref_link(product)
        assert result == 'https://unknown-shop.com/product/123'  # Возвращает оригинальную ссылку

    @patch('services.affiliates.get_settings')
    def test_build_ref_link_existing_ref_link(self, mock_settings):
        """Тест, что существующая ref_link не перезаписывается"""
        mock_settings.return_value = Mock()
        service = AffiliateService()

        product = {
            'id': 'test-123',
            'link': 'https://example.com/product/123',
            'ref_link': 'https://existing-affiliate-link.com'
        }

        result = service.build_ref_link(product)
        assert result == 'https://existing-affiliate-link.com'

    def test_detect_source_goldapple(self):
        """Тест определения источника Gold Apple"""
        service = AffiliateService()

        product = {'link': 'https://goldapple.ru/product/123'}
        source = service._detect_source(product)
        assert source == 'goldapple'

    def test_detect_source_ru_marketplace(self):
        """Тест определения источника Wildberries"""
        service = AffiliateService()

        product = {'link': 'https://wildberries.ru/product/123'}
        source = service._detect_source(product)
        assert source == 'ru_marketplace'

    def test_detect_source_unknown(self):
        """Тест определения неизвестного источника"""
        service = AffiliateService()

        product = {'link': 'https://unknown-shop.com/product/123'}
        source = service._detect_source(product)
        assert source is None


class TestIntegration:
    """Интеграционные тесты"""

    @patch('services.affiliates.get_settings')
    def test_full_cart_workflow(self, mock_settings):
        """Тест полного workflow корзины"""
        mock_settings.return_value = Mock()
        store = CartStore()

        # Добавляем товары
        store.add_item(123, "product-1", quantity=1, brand="Brand1", name="Product 1")
        store.add_item(123, "product-2", quantity=2, brand="Brand2", name="Product 2")

        # Проверяем корзину
        cart = store.get_cart(123)
        assert len(cart) == 2

        # Обновляем количество
        store.update_quantity(123, "product-1", None, 3)
        cart = store.get_cart(123)
        product1 = next(item for item in cart if item.product_id == "product-1")
        assert product1.quantity == 3

        # Очищаем корзину
        store.clear_cart(123)
        cart = store.get_cart(123)
        assert len(cart) == 0

    @patch('services.affiliates.get_settings')
    def test_affiliate_integration(self, mock_settings):
        """Тест интеграции affiliate ссылок"""
        mock_settings.return_value = Mock()
        service = AffiliateService()

        products = [
            {'id': 'goldapple-1', 'link': 'https://goldapple.ru/p1', 'brand': 'Gold Apple'},
            {'id': 'wb-1', 'link': 'https://wildberries.ru/p1', 'brand': 'Wildberries'},
            {'id': 'unknown-1', 'link': 'https://unknown.com/p1', 'brand': 'Unknown'}
        ]

        for product in products:
            result = service.build_ref_link(product)
            assert result is not None
            assert isinstance(result, str)

            # Для известных источников должна добавиться партнерская информация
            if 'goldapple' in product['link']:
                assert 'partner=' in result
            elif 'wildberries' in product['link']:
                assert 'partner=' in result
            else:
                # Для неизвестных - возвращается оригинальная ссылка
                assert result == product['link']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
