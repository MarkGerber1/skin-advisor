#!/usr/bin/env python
"""Проверка каталога продуктов"""

from engine.catalog import load_catalog
from collections import Counter


def main():
    try:
        products = load_catalog("assets/fixed_catalog.yaml")
        print(f"✅ Успешно загружено {len(products)} продуктов\n")

        # Статистика по брендам
        brands = Counter(p.brand for p in products)
        print(f"📊 Всего брендов: {len(brands)}")
        print("Топ-5 брендов по количеству продуктов:")
        for brand, count in brands.most_common(5):
            print(f"  • {brand}: {count} продуктов")

        # Статистика по категориям
        categories = Counter(p.category for p in products)
        print(f"\n📦 Всего категорий: {len(categories)}")
        print("Распределение по категориям:")
        for category, count in sorted(categories.items()):
            print(f"  • {category}: {count} продуктов")

        # Проверка полей
        with_links = sum(1 for p in products if p.link)
        with_actives = sum(1 for p in products if p.actives)
        with_price = sum(1 for p in products if p.price)

        print("\n✨ Качество данных:")
        print(f"  • Продукты с ссылками: {with_links}/{len(products)}")
        print(f"  • Продукты с активами: {with_actives}/{len(products)}")
        print(f"  • Продукты с ценами: {with_price}/{len(products)}")

    except Exception as e:
        print(f"❌ Ошибка загрузки каталога: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
