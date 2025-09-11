"""
🎯 Source Resolver - Приоритизация источников товаров
Золотое Яблоко → RU официальные → RU маркетплейсы → Зарубежные
"""

from __future__ import annotations

from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from engine.catalog_store import CatalogStore


@dataclass
class SourceInfo:
    """Информация об источнике товара"""

    name: str
    priority: int
    category: str  # goldapple, ru_official, ru_marketplace, intl
    domain: str
    currency: str = "RUB"
    is_official: bool = False


@dataclass
class ResolvedProduct:
    """Разрешенный товар с информацией об источнике"""

    original: Dict[str, Any]
    source_info: SourceInfo
    is_available: bool
    alternative: Optional[Dict[str, Any]] = None
    alternative_reason: Optional[str] = None
    checked_at: str = ""


class SourceResolver:
    """Разрешитель источников с приоритизацией"""

    def __init__(self):
        # Приоритизация источников (меньше число = выше приоритет)
        self.source_priorities = {
            # 🥇 Золотое Яблоко (наивысший приоритет)
            "goldapple.ru": SourceInfo(
                "Золотое Яблоко", 1, "goldapple", "goldapple.ru", "RUB", True
            ),
            "золотоеяблочко.рф": SourceInfo(
                "Золотое Яблоко", 1, "goldapple", "золотоеяблочко.рф", "RUB", True
            ),
            # 🥈 Российские официальные магазины
            "sephora.ru": SourceInfo("SEPHORA Russia", 2, "ru_official", "sephora.ru", "RUB", True),
            "letu.ru": SourceInfo("Л'Этуаль", 2, "ru_official", "letu.ru", "RUB", True),
            "rive-gauche.ru": SourceInfo(
                "Рив Гош", 2, "ru_official", "rive-gauche.ru", "RUB", True
            ),
            "aroma-zone.ru": SourceInfo(
                "Aroma-Zone", 2, "ru_official", "aroma-zone.ru", "RUB", True
            ),
            # 🥉 Российские маркетплейсы
            "wildberries.ru": SourceInfo(
                "Wildberries", 3, "ru_marketplace", "wildberries.ru", "RUB", False
            ),
            "ozon.ru": SourceInfo("Ozon", 3, "ru_marketplace", "ozon.ru", "RUB", False),
            "yandex.market.ru": SourceInfo(
                "Яндекс.Маркет", 3, "ru_marketplace", "yandex.market.ru", "RUB", False
            ),
            "lamoda.ru": SourceInfo("Lamoda", 3, "ru_marketplace", "lamoda.ru", "RUB", False),
            # 🌍 Зарубежные магазины (низший приоритет)
            "sephora.com": SourceInfo(
                "SEPHORA International", 4, "intl", "sephora.com", "USD", False
            ),
            "ulta.com": SourceInfo("Ulta", 4, "intl", "ulta.com", "USD", False),
            "cultbeauty.com": SourceInfo("Cult Beauty", 4, "intl", "cultbeauty.com", "GBP", False),
            "lookfantastic.com": SourceInfo(
                "LookFantastic", 4, "intl", "lookfantastic.com", "GBP", False
            ),
        }

    def _extract_domain_from_url(self, url: str) -> str:
        """Извлечение домена из URL"""
        if not url:
            return ""

        # Убираем протокол
        url = url.replace("https://", "").replace("http://", "")

        # Берем домен до первого слеша
        domain = url.split("/")[0].split("?")[0]

        # Приводим к нижнему регистру
        return domain.lower()

    def _get_source_info(self, url: str) -> SourceInfo:
        """Получение информации об источнике по URL"""
        domain = self._extract_domain_from_url(url)

        # Проверяем точное совпадение домена
        if domain in self.source_priorities:
            return self.source_priorities[domain]

        # Проверяем частичное совпадение (для поддоменов)
        for known_domain, info in self.source_priorities.items():
            if known_domain in domain or domain in known_domain:
                return info

        # Неизвестный источник - низший приоритет
        return SourceInfo("Неизвестный магазин", 999, "unknown", domain, "RUB", False)

    def resolve_source(self, product: Dict[str, Any]) -> ResolvedProduct:
        """
        Разрешение источника товара с приоритизацией

        Args:
            product: Товар из каталога

        Returns:
            ResolvedProduct: Товар с разрешенной информацией об источнике
        """
        try:
            # Получаем URL товара
            product_url = (
                product.get("link", "") or product.get("buy_url", "") or product.get("url", "")
            )

            # Определяем источник
            source_info = self._get_source_info(product_url)

            # Проверяем доступность товара
            in_stock = product.get("in_stock", True)
            price = product.get("price", 0)

            # Если товар недоступен или без цены - ищем альтернативы
            if not in_stock or price <= 0:
                alternative = self._find_alternative(product)
                alternative_reason = "out_of_stock" if not in_stock else "no_price"
            else:
                alternative = None
                alternative_reason = None

            return ResolvedProduct(
                original=product,
                source_info=source_info,
                is_available=in_stock and price > 0,
                alternative=alternative,
                alternative_reason=alternative_reason,
                checked_at=datetime.now().isoformat(),
            )

        except Exception as e:
            print(f"❌ Error resolving source for product {product.get('id', 'unknown')}: {e}")
            # Возвращаем товар с минимальной информацией
            return ResolvedProduct(
                original=product,
                source_info=SourceInfo("Ошибка", 999, "error", "unknown", "RUB", False),
                is_available=False,
                checked_at=datetime.now().isoformat(),
            )

    def _find_alternative(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Поиск альтернативы для недоступного товара

        Стратегии поиска:
        1. Тот же бренд + другое название (другой объем/оттенок)
        2. Другая марка в той же категории
        3. Аналог из другой категории (замена по назначению)
        """
        try:
            # Получаем каталог
            catalog_path = "assets/fixed_catalog.yaml"  # Можно параметризовать
            catalog_store = CatalogStore.instance(catalog_path)
            catalog = catalog_store.get()

            product_brand = product.get("brand", "").lower()
            product_category = product.get("category", "").lower()
            product_id = product.get("id", "")

            alternatives = []
            best_alternative = None
            best_priority = 999

            for item in catalog:
                # Пропускаем тот же товар
                if item.id == product_id or str(getattr(item, "key", "")) == str(product_id):
                    continue

                # Проверяем доступность
                if not getattr(item, "in_stock", True) or getattr(item, "price", 0) <= 0:
                    continue

                item_brand = getattr(item, "brand", "").lower()
                item_category = getattr(item, "category", "").lower()

                # Стратегия 1: Тот же бренд, другая модель (высокий приоритет)
                if item_brand == product_brand and item_category == product_category:
                    url = getattr(item, "buy_url", "") or getattr(item, "link", "")
                    source_info = self._get_source_info(url)

                    if source_info.priority < best_priority:
                        best_priority = source_info.priority
                        best_alternative = {
                            "id": item.id,
                            "name": getattr(item, "title", item.name),
                            "brand": item.brand,
                            "price": item.price,
                            "price_currency": getattr(item, "price_currency", "RUB"),
                            "category": item.category,
                            "link": url,
                            "source_name": source_info.name,
                            "source_priority": source_info.priority,
                            "alternative_reason": "другой_вариант_товара",
                        }

                # Стратегия 2: Другая марка, та же категория (средний приоритет)
                elif item_category == product_category and not best_alternative:
                    url = getattr(item, "buy_url", "") or getattr(item, "link", "")
                    source_info = self._get_source_info(url)

                    if source_info.priority < best_priority:
                        best_priority = source_info.priority
                        best_alternative = {
                            "id": item.id,
                            "name": getattr(item, "title", item.name),
                            "brand": item.brand,
                            "price": item.price,
                            "price_currency": getattr(item, "price_currency", "RUB"),
                            "category": item.category,
                            "link": url,
                            "source_name": source_info.name,
                            "source_priority": source_info.priority,
                            "alternative_reason": "аналог_категории",
                        }

            return best_alternative

        except Exception as e:
            print(f"❌ Error finding alternative for product {product.get('id', 'unknown')}: {e}")
            return None

    def get_source_display_name(self, product: Dict[str, Any]) -> str:
        """Получение отображаемого имени источника для товара"""
        product_url = (
            product.get("link", "") or product.get("buy_url", "") or product.get("url", "")
        )
        source_info = self._get_source_info(product_url)

        # Маппинг для отображения
        display_names = {
            "goldapple": "Золотое Яблоко",
            "ru_official": "Официал. магазин",
            "ru_marketplace": "Маркетплейс",
            "intl": "Зарубежный магазин",
            "unknown": "Неизвестный источник",
        }

        return display_names.get(source_info.category, source_info.name)

    def get_source_priority(self, product: Dict[str, Any]) -> int:
        """Получение приоритета источника для товара"""
        product_url = (
            product.get("link", "") or product.get("buy_url", "") or product.get("url", "")
        )
        source_info = self._get_source_info(product_url)
        return source_info.priority


# Глобальный экземпляр
_source_resolver = None


def get_source_resolver() -> SourceResolver:
    """Получить глобальный экземпляр SourceResolver"""
    global _source_resolver
    if _source_resolver is None:
        _source_resolver = SourceResolver()
    return _source_resolver


def enhance_product_with_source_info(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Обогащение товара информацией об источнике

    Args:
        product: Исходный товар

    Returns:
        Dict: Товар с дополнительной информацией об источнике
    """
    resolver = get_source_resolver()
    resolved = resolver.resolve_source(product)

    enhanced = dict(product)  # Копия оригинального товара

    # Добавляем информацию об источнике
    enhanced["source_name"] = resolver.get_source_display_name(product)
    enhanced["source_priority"] = resolver.get_source_priority(product)
    enhanced["source_category"] = resolved.source_info.category
    enhanced["is_available"] = resolved.is_available
    enhanced["checked_at"] = resolved.checked_at

    # Добавляем информацию об альтернативе если есть
    if resolved.alternative:
        enhanced["alternative"] = resolved.alternative
        enhanced["alternative_reason"] = resolved.alternative_reason

    return enhanced
