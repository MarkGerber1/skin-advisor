"""
Каноническая схема категорий и слагов для селектора
Обеспечивает единообразное маппинг между UI и данными селектора
"""

from typing import Dict, List, Set

# Каноническая карта слагов для ухода за кожей
SKINCARE_CANONICAL_SLUGS = {
    "cleanser": ["cleanser", "очищающее средство", "очищение", "cleansing"],
    "toner": ["toner", "toning", "тоник", "тонизирование"],
    "serum": ["serum", "сыворотка", "treatment"],
    "moisturizer": ["moisturizer", "cream", "крем", "увлажнение", "увлажняющий"],
    "eye_cream": ["eye_cream", "eye_care", "крем для глаз", "глаза", "eye"],
    "sunscreen": ["sunscreen", "spf", "солнцезащита", "sun_protection"],
    "mask": ["mask", "masks", "маска", "маски"]
}

# Обратное маппинг для быстрого поиска
SLUG_TO_CANONICAL = {}
for canonical, variants in SKINCARE_CANONICAL_SLUGS.items():
    for variant in variants:
        SLUG_TO_CANONICAL[variant.lower()] = canonical


def canon_slug(slug: str) -> str:
    """
    Нормализует слаг к каноническому виду

    Args:
        slug: Входящий слаг (может быть в любом варианте)

    Returns:
        Канонический слаг или исходный если не найден
    """
    if not slug:
        return slug

    normalized = slug.lower().strip()
    return SLUG_TO_CANONICAL.get(normalized, slug)


def get_canonical_variants(slug: str) -> List[str]:
    """
    Возвращает все варианты для канонического слага

    Args:
        slug: Канонический слаг

    Returns:
        Список всех возможных вариантов
    """
    canonical = canon_slug(slug)
    return SKINCARE_CANONICAL_SLUGS.get(canonical, [slug])


def safe_get_skincare_data(data: Dict, slug: str) -> List:
    """
    Безопасно извлекает данные по слагу из результата селектора

    Args:
        data: Данные селектора (обычно result.get("skincare", {}))
        slug: Слаг категории

    Returns:
        Список продуктов или пустой список
    """
    if not data or not isinstance(data, dict):
        return []

    canonical = canon_slug(slug)

    # Пробуем разные варианты
    for variant in SKINCARE_CANONICAL_SLUGS.get(canonical, [canonical]):
        if variant in data:
            products = data[variant]
            if isinstance(products, list):
                return products

    # Если ничего не нашли, возвращаем пустой список
    return []
