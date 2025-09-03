#!/usr/bin/env python3
"""
🧪 Автотесты для приоритизации источников товаров
Тестирует: SourcePrioritizer, интеграцию с селектором, корректность приоритетов
"""

import pytest
import sys
import os

# Импорты из проекта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from engine.source_prioritizer import SourcePrioritizer, SourceInfo


class TestSourcePrioritizer:
    """Тесты для системы приоритизации источников"""
    
    def setup_method(self):
        self.prioritizer = SourcePrioritizer()
    
    def test_golden_apple_highest_priority(self):
        """Золотое Яблоко должно иметь наивысший приоритет"""
        golden_apple_urls = [
            "https://goldapple.ru/product/123",
            "https://goldenappletree.ru/product/456",
            "https://золотоеяблочко.рф/товар/789"
        ]
        
        for url in golden_apple_urls:
            priority = self.prioritizer.get_priority(url)
            assert priority == 1, f"Золотое Яблоко должно иметь приоритет 1, получен {priority} для {url}"
            
            source_info = self.prioritizer.get_source_info(url)
            assert source_info is not None
            assert source_info.category == "golden_apple"
    
    def test_russian_official_priority(self):
        """Российские официальные магазины должны иметь приоритет 2"""
        ru_official_urls = [
            "https://sephora.ru/product/123",
            "https://letu.ru/product/456", 
            "https://rive-gauche.ru/product/789"
        ]
        
        for url in ru_official_urls:
            priority = self.prioritizer.get_priority(url)
            assert priority == 2, f"Российские официальные должны иметь приоритет 2, получен {priority} для {url}"
            
            source_info = self.prioritizer.get_source_info(url)
            assert source_info is not None
            assert source_info.category == "ru_official"
    
    def test_russian_marketplace_priority(self):
        """Российские маркетплейсы должны иметь приоритет 3"""
        ru_marketplace_urls = [
            "https://wildberries.ru/catalog/123",
            "https://ozon.ru/product/456",
            "https://market.yandex.ru/product/789"
        ]
        
        for url in ru_marketplace_urls:
            priority = self.prioritizer.get_priority(url)
            assert priority == 3, f"Российские маркетплейсы должны иметь приоритет 3, получен {priority} для {url}"
            
            source_info = self.prioritizer.get_source_info(url)
            assert source_info is not None
            assert source_info.category == "ru_marketplace"
    
    def test_foreign_priority(self):
        """Зарубежные источники должны иметь приоритет 4"""
        foreign_urls = [
            "https://sephora.com/product/123",
            "https://ulta.com/product/456",
            "https://beautylish.com/product/789"
        ]
        
        for url in foreign_urls:
            priority = self.prioritizer.get_priority(url)
            assert priority == 4, f"Зарубежные должны иметь приоритет 4, получен {priority} для {url}"
            
            source_info = self.prioritizer.get_source_info(url)
            assert source_info is not None
            assert source_info.category == "foreign"
    
    def test_unknown_source_lowest_priority(self):
        """Неизвестные источники должны иметь самый низкий приоритет"""
        unknown_urls = [
            "https://unknown-shop.com/product/123",
            "https://random-site.net/item/456",
            ""  # Пустая ссылка
        ]
        
        for url in unknown_urls:
            priority = self.prioritizer.get_priority(url)
            assert priority == 999, f"Неизвестные источники должны иметь приоритет 999, получен {priority} для {url}"
    
    def test_domain_extraction(self):
        """Тест корректного извлечения домена"""
        test_cases = [
            ("https://www.goldapple.ru/product/123", "goldapple.ru"),
            ("http://sephora.ru/beauty/456", "sephora.ru"),
            ("https://wildberries.ru/catalog/789?ref=abc", "wildberries.ru"),
            ("", None),
            ("invalid-url", None)
        ]
        
        for url, expected_domain in test_cases:
            actual_domain = self.prioritizer.get_domain_from_url(url)
            assert actual_domain == expected_domain, f"Для {url} ожидался домен {expected_domain}, получен {actual_domain}"
    
    def test_sort_products_by_priority(self):
        """Тест сортировки продуктов по приоритету источников"""
        products = [
            {"name": "Product A", "link": "https://unknown-shop.com/a"},  # priority 999
            {"name": "Product B", "link": "https://goldapple.ru/b"},      # priority 1
            {"name": "Product C", "link": "https://wildberries.ru/c"},    # priority 3
            {"name": "Product D", "link": "https://sephora.ru/d"},        # priority 2
        ]
        
        sorted_products = self.prioritizer.sort_products_by_source_priority(products)
        
        # Проверяем правильный порядок: золотое яблоко → sephora.ru → wildberries → unknown
        expected_order = ["Product B", "Product D", "Product C", "Product A"]
        actual_order = [p["name"] for p in sorted_products]
        
        assert actual_order == expected_order, f"Неправильная сортировка: ожидалось {expected_order}, получено {actual_order}"
    
    def test_get_best_source_product(self):
        """Тест выбора продукта с лучшим источником"""
        products = [
            {"name": "Wildberries Product", "link": "https://wildberries.ru/product"},
            {"name": "Golden Apple Product", "link": "https://goldapple.ru/product"},
            {"name": "Unknown Shop Product", "link": "https://unknown.com/product"},
        ]
        
        best_product = self.prioritizer.get_best_source_product(products)
        
        assert best_product is not None
        assert best_product["name"] == "Golden Apple Product"
    
    def test_group_by_source_category(self):
        """Тест группировки продуктов по категориям источников"""
        products = [
            {"name": "GA Product", "link": "https://goldapple.ru/1"},
            {"name": "Sephora Product", "link": "https://sephora.ru/2"},
            {"name": "WB Product", "link": "https://wildberries.ru/3"},
            {"name": "Ulta Product", "link": "https://ulta.com/4"},
            {"name": "Unknown Product", "link": "https://unknown.com/5"},
        ]
        
        groups = self.prioritizer.group_by_source_category(products)
        
        assert len(groups["golden_apple"]) == 1
        assert len(groups["ru_official"]) == 1
        assert len(groups["ru_marketplace"]) == 1
        assert len(groups["foreign"]) == 1
        assert len(groups["unknown"]) == 1
        
        assert groups["golden_apple"][0]["name"] == "GA Product"
        assert groups["ru_official"][0]["name"] == "Sephora Product"
        assert groups["ru_marketplace"][0]["name"] == "WB Product"
        assert groups["foreign"][0]["name"] == "Ulta Product"
        assert groups["unknown"][0]["name"] == "Unknown Product"
    
    def test_source_stats(self):
        """Тест статистики по источникам"""
        products = [
            {"link": "https://goldapple.ru/1"},
            {"link": "https://goldapple.ru/2"},
            {"link": "https://sephora.ru/3"},
            {"link": "https://wildberries.ru/4"},
            {"link": "https://unknown.com/5"},
        ]
        
        stats = self.prioritizer.get_source_stats(products)
        
        assert stats["golden_apple"] == 2
        assert stats["ru_official"] == 1
        assert stats["ru_marketplace"] == 1
        assert stats["foreign"] == 0
        assert stats["unknown"] == 1
    
    def test_prioritized_links_single_product(self):
        """Тест получения приоритизированных ссылок для одного товара"""
        product = {
            "name": "Test Product",
            "link": "https://wildberries.ru/product/123",
            "additional_links": [
                {"url": "https://goldapple.ru/product/123"},
                {"url": "https://unknown-shop.com/product/123"}
            ]
        }
        
        prioritized_links = self.prioritizer.get_prioritized_links(product)
        
        # Должно быть 3 ссылки, отсортированные по приоритету
        assert len(prioritized_links) == 3
        assert prioritized_links[0]["url"] == "https://goldapple.ru/product/123"  # priority 1
        assert prioritized_links[1]["url"] == "https://wildberries.ru/product/123"  # priority 3
        assert prioritized_links[2]["url"] == "https://unknown-shop.com/product/123"  # priority 999
        
        # Проверяем метаданные
        assert prioritized_links[0]["source_name"] == "Золотое Яблоко"
        assert prioritized_links[0]["category"] == "golden_apple"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




