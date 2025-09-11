"""Интеграционный тест полного сценария использования бота"""

import pytest
from unittest.mock import Mock, patch
from services.cart_store import CartStore
from services.affiliates import AffiliateService


class TestFullBotScenario:
    """Интеграционный тест полного сценария использования"""

    @patch("services.affiliates.get_settings")
    def test_makeup_recommendation_scenario(self, mock_settings):
        """Тест сценария: Портрет лица → подбор makeup → корзина → checkout"""
        mock_settings.return_value = Mock()

        # Шаг 1: Имитируем данные теста "Портрет лица"

        # Шаг 2: Имитируем результат подбора продуктов
        makeup_result = {
            "base": [
                {
                    "id": "goldapple-001",
                    "brand": "Maybelline",
                    "name": "Fit Me Matte + Poreless Foundation",
                    "price": 749.0,
                    "currency": "RUB",
                    "link": "https://goldapple.ru/product/foundation",
                    "category": "Тональный крем",
                },
                {
                    "id": "loreal-001",
                    "brand": "L'Oreal Paris",
                    "name": "True Match Foundation",
                    "price": 899.0,
                    "currency": "RUB",
                    "link": "https://goldapple.ru/product/loreal-foundation",
                    "category": "Тональный крем",
                },
            ]
        }

        # Шаг 3: Тестируем генерацию affiliate ссылок
        affiliate_service = AffiliateService()

        for category_products in makeup_result.values():
            for product in category_products:
                original_link = product.get("link")
                affiliate_link = affiliate_service.build_ref_link(product, "makeup_test")

                print(f"Product: {product['id']}")
                print(f"Original: {original_link}")
                print(f"Affiliate: {affiliate_link}")
                print("---")

                # Проверяем, что affiliate ссылка сгенерирована
                assert affiliate_link is not None
                assert isinstance(affiliate_link, str)
                product["ref_link"] = affiliate_link

        # Шаг 4: Тестируем работу корзины
        cart_store = CartStore()

        # Добавляем товары в корзину
        for category_products in makeup_result.values():
            for product in category_products:
                cart_store.add_item(
                    user_id=12345,
                    product_id=product["id"],
                    quantity=1,
                    brand=product["brand"],
                    name=product["name"],
                    price=product["price"],
                    currency=product["currency"],
                    ref_link=product.get("ref_link"),
                    category=product["category"],
                )

        # Проверяем корзину
        cart = cart_store.get_cart(12345)
        assert len(cart) == 2

        # Проверяем данные товаров
        foundation1 = next(item for item in cart if item.product_id == "goldapple-001")
        foundation2 = next(item for item in cart if item.product_id == "loreal-001")

        assert foundation1.quantity == 1
        assert foundation1.price == 749.0
        assert foundation1.currency == "RUB"
        assert foundation1.ref_link is not None

        assert foundation2.quantity == 1
        assert foundation2.price == 899.0
        assert foundation2.currency == "RUB"
        assert foundation2.ref_link is not None

        # Шаг 5: Тестируем операции с корзиной
        # Увеличиваем количество первого товара
        cart_store.update_quantity(12345, "goldapple-001", None, 2)
        cart = cart_store.get_cart(12345)
        foundation1 = next(item for item in cart if item.product_id == "goldapple-001")
        assert foundation1.quantity == 2

        # Уменьшаем количество второго товара до 0 (удаление)
        cart_store.update_quantity(12345, "loreal-001", None, 0)
        cart = cart_store.get_cart(12345)
        loreal_items = [item for item in cart if item.product_id == "loreal-001"]
        assert len(loreal_items) == 0  # Товар должен быть удален

        # Шаг 6: Финальная проверка корзины
        cart = cart_store.get_cart(12345)
        assert len(cart) == 1  # Остался только один товар

        remaining_item = cart[0]
        assert remaining_item.product_id == "goldapple-001"
        assert remaining_item.quantity == 2
        assert remaining_item.price == 749.0
        assert remaining_item.currency == "RUB"

        print("✅ Full bot scenario test passed!")

    @patch("services.affiliates.get_settings")
    def test_skincare_recommendation_scenario(self, mock_settings):
        """Тест сценария: Подробный уход за кожей → подбор skincare → корзина"""
        mock_settings.return_value = Mock()

        # Шаг 1: Имитируем данные теста skincare

        # Шаг 2: Имитируем результат подбора skincare продуктов
        skincare_result = {
            "cleanser": [
                {
                    "id": "cerave-001",
                    "brand": "CeraVe",
                    "name": "Увлажняющий очищающий гель",
                    "price": 1200.0,
                    "currency": "RUB",
                    "link": "https://goldapple.ru/product/cerave-cleanser",
                    "category": "Очищение",
                }
            ],
            "toner": [
                {
                    "id": "cosrx-001",
                    "brand": "COSRX",
                    "name": "AHA/BHA Clarifying Treatment Toner",
                    "price": 1800.0,
                    "currency": "RUB",
                    "link": "https://goldapple.ru/product/cosrx-toner",
                    "category": "Тоник",
                }
            ],
            "serum": [
                {
                    "id": "klairs-001",
                    "brand": "Klairs",
                    "name": "Supple Preparation Unscented Serum",
                    "price": 3200.0,
                    "currency": "RUB",
                    "link": "https://goldapple.ru/product/klairs-serum",
                    "category": "Сыворотка",
                }
            ],
        }

        # Шаг 3: Тестируем affiliate и корзину
        affiliate_service = AffiliateService()
        cart_store = CartStore()

        total_products = 0
        total_value = 0.0

        for category, products in skincare_result.items():
            for product in products:
                # Генерируем affiliate ссылку
                affiliate_link = affiliate_service.build_ref_link(product, "skincare_test")
                assert affiliate_link is not None
                product["ref_link"] = affiliate_link

                # Добавляем в корзину
                cart_store.add_item(
                    user_id=67890,
                    product_id=product["id"],
                    quantity=1,
                    brand=product["brand"],
                    name=product["name"],
                    price=product["price"],
                    currency=product["currency"],
                    ref_link=product["ref_link"],
                    category=product["category"],
                )

                total_products += 1
                total_value += product["price"]

        # Проверяем корзину
        cart = cart_store.get_cart(67890)
        assert len(cart) == total_products

        # Проверяем общую стоимость
        cart_total = sum(item.price * item.quantity for item in cart)
        assert cart_total == total_value

        # Проверяем, что все товары имеют affiliate ссылки
        for item in cart:
            assert item.ref_link is not None
            assert item.currency == "RUB"
            assert item.quantity == 1

        print(
            f"✅ Skincare scenario test passed! {total_products} products, total value: {total_value} RUB"
        )

    def test_error_handling_scenario(self):
        """Тест сценария с ошибками и их обработкой"""
        cart_store = CartStore()
        affiliate_service = AffiliateService()

        # Тест с невалидными данными
        invalid_product = {"id": None, "link": None, "brand": "Invalid Brand"}

        # Affiliate должен обработать ошибку gracefully
        result = affiliate_service.build_ref_link(invalid_product)
        assert result is None  # Должен вернуть None без падения

        # Корзина должна игнорировать невалидные товары
        cart_store.add_item(
            user_id=99999,
            product_id="",  # Пустой ID
            quantity=1,
            brand="Invalid",
            name="Invalid Product",
        )

        cart = cart_store.get_cart(99999)
        assert len(cart) == 0  # Ничего не должно добавиться

        print("✅ Error handling test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
