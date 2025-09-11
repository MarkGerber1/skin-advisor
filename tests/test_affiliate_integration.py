"""Интеграционные тесты для партнерских ссылок"""

import pytest
from unittest.mock import Mock, patch
from services.affiliates import AffiliateService


class TestAffiliateIntegration:
    """Интеграционные тесты для affiliate системы"""

    @patch("services.affiliates.get_settings")
    def test_affiliate_full_workflow(self, mock_settings):
        """Тест полного workflow генерации affiliate ссылок"""
        mock_settings.return_value = Mock()
        service = AffiliateService()

        products = [
            {
                "id": "goldapple-001",
                "link": "https://goldapple.ru/product/123",
                "brand": "Gold Apple",
                "name": "Test Foundation",
            },
            {
                "id": "wb-001",
                "link": "https://wildberries.ru/product/456",
                "brand": "Wildberries",
                "name": "Test Mascara",
            },
            {
                "id": "unknown-001",
                "link": "https://unknown-shop.com/product/789",
                "brand": "Unknown Brand",
                "name": "Test Product",
            },
            {"id": "nolink-001", "brand": "No Link Brand", "name": "No Link Product"},
        ]

        results = []
        for product in products:
            result = service.build_ref_link(product, "test_campaign")
            results.append(result)

            print(f"Product: {product.get('id')}")
            print(f"Original link: {product.get('link')}")
            print(f"Affiliate link: {result}")
            print("---")

        # Проверяем результаты
        assert results[0] is not None  # Gold Apple должен иметь affiliate ссылку
        assert "partner=" in results[0]  # Должна содержать партнерский параметр

        assert results[1] is not None  # Wildberries должен иметь affiliate ссылку
        assert "partner=" in results[1]  # Должна содержать партнерский параметр

        assert results[2] is not None  # Unknown должен вернуть оригинальную ссылку
        assert results[2] == "https://unknown-shop.com/product/789"

        assert results[3] is None  # Без ссылки должен вернуть None

    @patch("services.affiliates.get_settings")
    def test_affiliate_priority_system(self, mock_settings):
        """Тест системы приоритетов affiliate источников"""
        mock_settings.return_value = Mock()
        service = AffiliateService()

        # Тестируем определение источников
        test_cases = [
            ({"link": "https://goldapple.ru/p1", "brand": "Gold Apple"}, "goldapple"),
            ({"link": "https://wildberries.ru/p1", "brand": "WB"}, "ru_marketplace"),
            ({"link": "https://ozon.ru/p1", "brand": "Ozon"}, "ru_marketplace"),
            ({"link": "https://sephora.ru/p1", "brand": "Sephora"}, "intl_authorized"),
            ({"link": "https://unknown.com/p1", "brand": "Unknown"}, None),
            ({"brand": "Gold Apple"}, "goldapple"),  # По бренду
            ({"brand": "Some Unknown"}, None),  # Неизвестный бренд
        ]

        for product_data, expected_source in test_cases:
            source = service._detect_source(product_data)
            assert (
                source == expected_source
            ), f"Expected {expected_source} for {product_data}, got {source}"

    @patch("services.affiliates.get_settings")
    def test_affiliate_config_fallback(self, mock_settings):
        """Тест fallback при отсутствии конфигурации"""
        # Имитируем отсутствие настроек
        mock_settings.side_effect = Exception("Settings not available")
        service = AffiliateService()

        product = {
            "id": "test-001",
            "link": "https://example.com/product/123",
            "brand": "Test Brand",
        }

        result = service.build_ref_link(product)
        # Должен вернуть оригинальную ссылку при отсутствии конфигурации
        assert result == "https://example.com/product/123"

    @patch("services.affiliates.get_settings")
    def test_affiliate_existing_ref_link(self, mock_settings):
        """Тест, что существующая ref_link не перезаписывается"""
        mock_settings.return_value = Mock()
        service = AffiliateService()

        product = {
            "id": "test-001",
            "link": "https://example.com/product/123",
            "ref_link": "https://existing-affiliate-link.com",
            "brand": "Test Brand",
        }

        result = service.build_ref_link(product)
        # Должен вернуть существующую ref_link
        assert result == "https://existing-affiliate-link.com"

    @patch("services.affiliates.get_settings")
    def test_affiliate_url_encoding(self, mock_settings):
        """Тест правильного URL encoding в affiliate ссылках"""
        mock_settings.return_value = Mock()
        service = AffiliateService()

        product = {
            "id": "test-001",
            "link": "https://example.com/product/123?param=value with spaces",
            "brand": "Gold Apple",
        }

        result = service.build_ref_link(product)
        assert result is not None
        assert (
            "https://example.com/product/123?param=value%20with%20spaces" in result
            or "partner=" in result
        )

    def test_affiliate_error_handling(self):
        """Тест обработки ошибок в affiliate системе"""
        service = AffiliateService()

        # Тест с невалидными данными
        invalid_cases = [
            None,
            {},
            {"id": None},
            {"id": "", "link": None},
            {"id": "test", "link": ""},
        ]

        for invalid_product in invalid_cases:
            try:
                result = service.build_ref_link(invalid_product)
                # Должен вернуть None или оригинальную ссылку без падения
                assert result is None or isinstance(result, str)
            except Exception as e:
                pytest.fail(f"Affiliate service failed on invalid input {invalid_product}: {e}")

    @patch("services.affiliates.get_settings")
    def test_affiliate_source_priority(self, mock_settings):
        """Тест приоритета источников affiliate"""
        mock_settings.return_value = Mock()
        service = AffiliateService()

        # Проверяем, что приоритеты определены корректно
        sources = ["goldapple", "ru_official", "ru_marketplace", "intl_authorized", "default"]
        priorities = [service.get_source_priority(src) for src in sources]

        # Приоритеты должны быть в порядке возрастания (меньше = выше приоритет)
        assert priorities[0] < priorities[1]  # goldapple имеет высший приоритет
        assert priorities[-1] > priorities[0]  # default имеет низший приоритет

        # Неизвестный источник должен иметь низший приоритет
        assert service.get_source_priority("unknown_source") > max(priorities)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
