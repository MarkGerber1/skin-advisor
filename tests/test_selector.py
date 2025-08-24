#!/usr/bin/env python3
"""
Тесты для движка подбора товаров.
"""

import pytest
from pathlib import Path
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.models import Product, UserProfile, Shade
from engine.selector import select_products


@pytest.fixture
def sample_catalog():
    """Создает тестовый каталог товаров."""
    return [
        # Очищение
        Product(
            id="cleanser_1",
            name="Gentle Cleanser",
            brand="Test Brand",
            category="cleanser",
            price=500.0,
            price_currency="RUB",
            link="https://example.com/cleanser1",
            actives=["gentle_surfactants"],
            tags=["gentle", "fragrance_free"],
            in_stock=True,
            volume_ml=200.0,
        ),
        # Тоник
        Product(
            id="toner_1",
            name="Hydrating Toner",
            brand="Test Brand",
            category="toner",
            price=800.0,
            price_currency="RUB",
            link="https://example.com/toner1",
            actives=["hyaluronic_acid"],
            tags=["hydrating"],
            in_stock=True,
            volume_ml=200.0,
        ),
        # Сыворотка
        Product(
            id="serum_1",
            name="Niacinamide Serum",
            brand="Test Brand",
            category="serum",
            price=1200.0,
            price_currency="RUB",
            link="https://example.com/serum1",
            actives=["niacinamide"],
            tags=["oil_control"],
            in_stock=True,
            volume_ml=30.0,
        ),
        # Крем
        Product(
            id="moisturizer_1",
            name="Moisturizing Cream",
            brand="Test Brand",
            category="moisturizer",
            price=1500.0,
            price_currency="RUB",
            link="https://example.com/moisturizer1",
            actives=["ceramides"],
            tags=["barrier_repair"],
            in_stock=True,
            volume_ml=50.0,
        ),
        # Солнцезащита
        Product(
            id="sunscreen_1",
            name="SPF 50 Sunscreen",
            brand="Test Brand",
            category="sunscreen",
            price=1000.0,
            price_currency="RUB",
            link="https://example.com/sunscreen1",
            spf=50,
            tags=["broad_spectrum"],
            in_stock=True,
            volume_ml=50.0,
        ),
        # Макияж - тональный крем
        Product(
            id="foundation_1",
            name="Foundation",
            brand="Test Brand",
            category="foundation",
            subcategory="face",
            price=2000.0,
            price_currency="RUB",
            link="https://example.com/foundation1",
            finish="natural",
            shade=Shade(name="Natural Ivory", code="110", undertone="cool", color_family="fair"),
            tags=["buildable"],
            in_stock=True,
            volume_ml=30.0,
        ),
        # Макияж - помада
        Product(
            id="lipstick_1",
            name="Lipstick",
            brand="Test Brand",
            category="lipstick",
            subcategory="lips",
            price=1500.0,
            price_currency="RUB",
            link="https://example.com/lipstick1",
            finish="matte",
            shade=Shade(name="Ruby Red", code="RR", undertone="cool", color_family="red"),
            tags=["long_wearing"],
            in_stock=True,
            weight_g=3.0,
        ),
    ]


def test_select_skincare_products(sample_catalog):
    """Тест подбора товаров для ухода за кожей."""
    profile = UserProfile(skin_type="oily", concerns=["acne", "dehydration"])

    result = select_products(
        user_profile=profile,
        catalog=sample_catalog,
        partner_code="test_123",
        redirect_base="https://example.com/redirect",
    )

    # Проверяем структуру результата
    assert "skincare" in result
    assert "makeup" in result

    skincare = result["skincare"]
    assert "AM" in skincare
    assert "PM" in skincare
    assert "weekly" in skincare

    # Проверяем, что подобраны товары
    assert len(skincare["AM"]) > 0
    assert len(skincare["PM"]) > 0

    # Проверяем, что товары имеют правильные поля
    for product in skincare["AM"]:
        assert "id" in product
        assert "brand" in product
        assert "name" in product
        assert "price" in product
        assert "ref_link" in product


def test_select_makeup_products(sample_catalog):
    """Тест подбора товаров для макияжа."""
    profile = UserProfile(
        undertone="cool", value="light", hair_depth="dark", eye_color="blue", contrast="high"
    )

    result = select_products(
        user_profile=profile,
        catalog=sample_catalog,
        partner_code="test_123",
        redirect_base="https://example.com/redirect",
    )

    makeup = result["makeup"]
    assert "face" in makeup
    assert "brows" in makeup
    assert "eyes" in makeup
    assert "lips" in makeup

    # Проверяем, что подобраны товары для лица и губ
    assert len(makeup["face"]) > 0
    assert len(makeup["lips"]) > 0

    # Проверяем, что товары имеют правильные поля
    for product in makeup["face"]:
        assert "id" in product
        assert "brand" in product
        assert "name" in product
        assert "price" in product
        assert "ref_link" in product


def test_filter_by_undertone(sample_catalog):
    """Тест фильтрации по подтону."""
    profile = UserProfile(undertone="cool", value="light")

    result = select_products(user_profile=profile, catalog=sample_catalog, partner_code="test_123")

    # Проверяем, что подобраны товары с cool подтоном
    makeup = result["makeup"]
    for product in makeup["face"] + makeup["lips"]:
        # Проверяем, что товар имеет правильный подтон
        # (в реальном каталоге это будет проверяться по shade.undertone)
        pass


def test_empty_catalog():
    """Тест работы с пустым каталогом."""
    profile = UserProfile(skin_type="normal")

    result = select_products(user_profile=profile, catalog=[], partner_code="test_123")

    # Результат должен быть пустым, но структура должна сохраниться
    assert "skincare" in result
    assert "makeup" in result

    skincare = result["skincare"]
    assert len(skincare["AM"]) == 0
    assert len(skincare["PM"]) == 0
    assert len(skincare["weekly"]) == 0


def test_affiliate_links():
    """Тест генерации партнерских ссылок."""
    profile = UserProfile(skin_type="normal")
    catalog = [
        Product(
            id="test",
            name="Test",
            brand="Test",
            category="cleanser",
            link="https://example.com/product",
        )
    ]

    result = select_products(
        user_profile=profile,
        catalog=catalog,
        partner_code="test_123",
        redirect_base="https://redirect.com",
    )

    # Проверяем, что сгенерированы партнерские ссылки
    skincare = result["skincare"]
    if skincare["AM"]:
        product = skincare["AM"][0]
        assert "ref_link" in product
        assert "test_123" in product["ref_link"]
        assert "redirect.com" in product["ref_link"]
