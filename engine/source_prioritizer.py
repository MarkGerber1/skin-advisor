#!/usr/bin/env python3
"""
🎯 Приоритизация источников товаров
Реализует иерархию: Золотое Яблоко → Российские официальные → Российские маркетплейсы → Зарубежные
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class SourceInfo:
    """Информация об источнике товара"""

    domain: str
    priority: int  # Чем меньше, тем выше приоритет
    category: str  # golden_apple, ru_official, ru_marketplace, foreign
    name: str


class SourcePrioritizer:
    """Система приоритизации источников товаров"""

    def __init__(self):
        self.sources = self._init_sources()

    def _init_sources(self) -> Dict[str, SourceInfo]:
        """Инициализация списка источников с приоритетами"""
        sources = {}

        # 1. Золотое Яблоко (наивысший приоритет)
        golden_apple_domains = ["goldapple.ru", "goldenappletree.ru", "золотоеяблочко.рф"]
        for domain in golden_apple_domains:
            sources[domain] = SourceInfo(
                domain=domain, priority=1, category="golden_apple", name="Золотое Яблоко"
            )

        # 2. Российские официальные магазины
        ru_official = [
            ("sephora.ru", "Sephora Russia"),
            ("letu.ru", "Л'Этуаль"),
            ("rive-gauche.ru", "Рив Гош"),
            ("letual.ru", "Л'Этуаль"),
            ("pudra.ru", "Пудра.ру"),
            ("brownsbeauty.ru", "Browns Beauty"),
            ("золтоеяблоко.рф", "Золтое Яблоко"),
        ]
        for domain, name in ru_official:
            sources[domain] = SourceInfo(
                domain=domain, priority=2, category="ru_official", name=name
            )

        # 3. Российские маркетплейсы
        ru_marketplaces = [
            ("wildberries.ru", "Wildberries"),
            ("ozon.ru", "Ozon"),
            ("yandex.market.ru", "Яндекс.Маркет"),
            ("market.yandex.ru", "Яндекс.Маркет"),
            ("lamoda.ru", "Lamoda"),
            ("goods.ru", "Goods.ru"),
        ]
        for domain, name in ru_marketplaces:
            sources[domain] = SourceInfo(
                domain=domain, priority=3, category="ru_marketplace", name=name
            )

        # 4. Зарубежные авторизованные
        foreign_authorized = [
            ("sephora.com", "Sephora International"),
            ("ulta.com", "Ulta Beauty"),
            ("beautylish.com", "Beautylish"),
            ("dermstore.com", "Dermstore"),
            ("lookfantastic.com", "LookFantastic"),
            ("feelunique.com", "FeelUnique"),
            ("notino.com", "Notino"),
        ]
        for domain, name in foreign_authorized:
            sources[domain] = SourceInfo(domain=domain, priority=4, category="foreign", name=name)

        return sources

    def get_domain_from_url(self, url: str) -> Optional[str]:
        """Извлекает домен из URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Убираем www. префикс
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return None

    def get_source_info(self, url: str) -> Optional[SourceInfo]:
        """Получает информацию об источнике по URL"""
        domain = self.get_domain_from_url(url)
        if not domain:
            return None

        return self.sources.get(domain)

    def get_priority(self, url: str) -> int:
        """Получает приоритет источника (чем меньше, тем выше приоритет)"""
        source_info = self.get_source_info(url)
        if source_info:
            return source_info.priority
        else:
            # Неизвестный источник - самый низкий приоритет
            return 999

    def sort_products_by_source_priority(
        self, products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Сортирует продукты по приоритету источников"""

        def get_product_priority(product):
            link = product.get("link") or product.get("ref_link") or ""
            return self.get_priority(link)

        return sorted(products, key=get_product_priority)

    def get_best_source_product(self, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Возвращает продукт с источником наивысшего приоритета"""
        if not products:
            return None

        sorted_products = self.sort_products_by_source_priority(products)
        return sorted_products[0]

    def group_by_source_category(
        self, products: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Группирует продукты по категориям источников"""
        groups = {
            "golden_apple": [],
            "ru_official": [],
            "ru_marketplace": [],
            "foreign": [],
            "unknown": [],
        }

        for product in products:
            link = product.get("link") or product.get("ref_link") or ""
            source_info = self.get_source_info(link)

            if source_info:
                groups[source_info.category].append(product)
            else:
                groups["unknown"].append(product)

        return groups

    def get_prioritized_links(self, product: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Возвращает список ссылок продукта, отсортированный по приоритету
        Ожидает что у продукта может быть несколько ссылок
        """
        links = []

        # Основная ссылка
        main_link = product.get("link") or product.get("ref_link")
        if main_link:
            source_info = self.get_source_info(main_link)
            links.append(
                {
                    "url": main_link,
                    "priority": source_info.priority if source_info else 999,
                    "source_name": source_info.name if source_info else "Неизвестный источник",
                    "category": source_info.category if source_info else "unknown",
                }
            )

        # Дополнительные ссылки (если есть)
        additional_links = product.get("additional_links", [])
        for link_info in additional_links:
            url = link_info.get("url")
            if url:
                source_info = self.get_source_info(url)
                links.append(
                    {
                        "url": url,
                        "priority": source_info.priority if source_info else 999,
                        "source_name": source_info.name if source_info else "Неизвестный источник",
                        "category": source_info.category if source_info else "unknown",
                    }
                )

        # Сортируем по приоритету
        return sorted(links, key=lambda x: x["priority"])

    def get_source_stats(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """Возвращает статистику по источникам"""
        stats = {}
        groups = self.group_by_source_category(products)

        for category, category_products in groups.items():
            stats[category] = len(category_products)

        return stats


# Глобальный экземпляр для использования в проекте
_prioritizer = None


def get_source_prioritizer() -> SourcePrioritizer:
    """Получить глобальный экземпляр приоритизатора"""
    global _prioritizer
    if _prioritizer is None:
        _prioritizer = SourcePrioritizer()
    return _prioritizer


if __name__ == "__main__":
    # Тестирование
    prioritizer = SourcePrioritizer()

    test_urls = [
        "https://wildberries.ru/catalog/123",
        "https://goldapple.ru/product/456",
        "https://sephora.com/product/789",
        "https://letu.ru/product/abc",
        "https://unknown-site.com/product/xyz",
    ]

    print("🧪 Тестирование приоритизации:")
    for url in test_urls:
        priority = prioritizer.get_priority(url)
        source_info = prioritizer.get_source_info(url)
        source_name = source_info.name if source_info else "Неизвестный"
        print(f"  {url} → Приоритет: {priority}, Источник: {source_name}")
