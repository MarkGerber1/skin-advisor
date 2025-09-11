"""
Интеграционные тесты для проверки полного потока работы бота
"""

import pytest
import tempfile
from engine.cart_store import CartStore, CartItem
from engine.selector_schema import canon_slug, safe_get_skincare_data
from services.affiliates import AffiliateService
from services.text_sanitizer import TextSanitizer


class TestIntegrationFlow:
    """Интеграционные тесты"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.cart_store = CartStore(base_dir=self.temp_dir)
        self.affiliate_service = AffiliateService()
        self.text_sanitizer = TextSanitizer()

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_cart_workflow(self):
        """Тест полного workflow корзины"""
        user_id = 12345

        # Добавляем товары
        products = [
            CartItem(product_id="cleanser1", qty=1, price=500.0, brand="CeraVe"),
            CartItem(product_id="toner1", qty=2, price=800.0, brand="Klairs"),
            CartItem(product_id="serum1", qty=1, price=1500.0, brand="The Ordinary"),
        ]

        for product in products:
            self.cart_store.add(user_id, product)

        # Проверяем корзину
        cart_items = self.cart_store.get(user_id)
        assert len(cart_items) == 3

        cart_count = self.cart_store.get_cart_count(user_id)
        assert cart_count == 4  # 1 + 2 + 1

        item_count, total_price = self.cart_store.get_cart_total(user_id)
        assert item_count == 4
        assert total_price == 3600.0  # 500 + 2*800 + 1500

        # Тестируем изменение количества
        self.cart_store.inc_quantity(user_id, "toner1")
        cart_count = self.cart_store.get_cart_count(user_id)
        assert cart_count == 5  # 1 + 3 + 1

        # Тестируем удаление
        self.cart_store.dec_quantity(user_id, "cleanser1")
        cart_items = self.cart_store.get(user_id)
        assert len(cart_items) == 2  # cleanser удален

    def test_affiliate_link_generation(self):
        """Тест генерации партнерских ссылок"""
        # Тестовый продукт с goldapple ссылкой
        product_goldapple = {
            "id": "test_goldapple",
            "link": "https://goldapple.ru/product123",
            "brand": "Test Brand",
        }

        link = self.affiliate_service.build_ref_link(product_goldapple)
        assert link is not None
        assert "partner=skincare_bot" in link

        # Тестовый продукт с wildberries ссылкой
        product_wb = {
            "id": "test_wb",
            "link": "https://wildberries.ru/product456",
            "brand": "Test Brand",
        }

        link = self.affiliate_service.build_ref_link(product_wb)
        assert link is not None

    def test_selector_schema_integration(self):
        """Тест интеграции selector_schema"""
        # Тестовые данные селектора
        selector_data = {
            "skincare": {
                "cleanser": [{"id": "clean1", "brand": "CeraVe"}],
                "toner": [{"id": "toner1", "brand": "Klairs"}],
                "очищающее средство": [{"id": "clean2", "brand": "Bioderma"}],
            }
        }

        # Проверяем канонизацию
        assert canon_slug("очищающее средство") == "cleanser"
        assert canon_slug("cleanser") == "cleanser"

        # Проверяем безопасное извлечение
        cleansers = safe_get_skincare_data(selector_data["skincare"], "очищающее средство")
        assert len(cleansers) == 1
        assert cleansers[0]["brand"] == "CeraVe"

    def test_text_sanitization_workflow(self):
        """Тест workflow очистки текста"""
        # Текст с markdown и лишними символами
        dirty_text = """
        **Рекомендация по уходу**

        * Очищение: **CeraVe** гель
        * Тоник: [Klairs] Supple Preparation
        * Сыворотка: > The Ordinary

        ```Важно: использовать ежедневно```
        """

        clean_text = self.text_sanitizer.sanitize(dirty_text)

        # Проверяем удаление markdown
        assert "**" not in clean_text
        assert "*" not in clean_text
        assert "[" not in clean_text
        assert "]" not in clean_text
        assert ">" not in clean_text
        assert "`" not in clean_text

        # Проверяем наличие полезного контента
        assert "Рекомендация по уходу" in clean_text
        assert "CeraVe" in clean_text
        assert "Klairs" in clean_text

    def test_cart_with_affiliates(self):
        """Тест интеграции корзины с affiliate ссылками"""
        user_id = 12345

        # Создаем товар с affiliate ссылкой
        product = CartItem(
            product_id="aff_test",
            qty=1,
            price=1000.0,
            brand="Test Brand",
            ref_link="https://example.com/product?partner=test",
        )

        self.cart_store.add(user_id, product)

        # Проверяем сохранение
        items = self.cart_store.get(user_id)
        assert len(items) == 1
        assert items[0].ref_link == "https://example.com/product?partner=test"

    def test_error_handling(self):
        """Тест обработки ошибок"""
        # Тест пустых данных
        empty_result = safe_get_skincare_data(None, "cleanser")
        assert empty_result == []

        # Тест несуществующего товара в корзине
        success = self.cart_store.inc_quantity(12345, "nonexistent")
        assert success == False


if __name__ == "__main__":
    pytest.main([__file__])
