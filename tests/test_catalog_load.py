#!/usr/bin/env python3
"""
Тесты для проверки загрузки каталога.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Добавляем корневую директорию в путь
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.catalog import load_catalog
from engine.models import Product


@pytest.fixture
def valid_catalog_file():
    """Создает временный файл с валидным каталогом."""
    content = """
products:
  - id: "test_001"
    name: "Test Product"
    brand: "Test Brand"
    category: "cleanser"
    price: 100.0
    price_currency: "RUB"
    link: "https://example.com/test"
    actives: ["test_active"]
    tags: ["test_tag"]
    in_stock: true
    volume_ml: 100.0
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Очистка
    os.unlink(temp_path)


@pytest.fixture
def invalid_catalog_file():
    """Создает временный файл с невалидным каталогом."""
    content = """
products:
  - id: "test_001"
    name: "Test Product"
    # Отсутствует обязательное поле brand
    category: "cleanser"
    price: "invalid_price"  # Не число
    price_currency: "INVALID"  # Невалидная валюта
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Очистка
    os.unlink(temp_path)


def test_load_valid_catalog(valid_catalog_file):
    """Тест загрузки валидного каталога."""
    products = load_catalog(valid_catalog_file)
    
    assert len(products) == 1
    product = products[0]
    
    assert product.id == "test_001"
    assert product.name == "Test Product"
    assert product.brand == "Test Brand"
    assert product.category == "cleanser"
    assert product.price == 100.0
    assert product.price_currency == "RUB"
    assert str(product.link) == "https://example.com/test"
    assert product.actives == ["test_active"]
    assert product.tags == ["test_tag"]
    assert product.in_stock is True
    assert product.volume_ml == 100.0


def test_load_invalid_catalog(invalid_catalog_file):
    """Тест загрузки невалидного каталога (должен пропустить невалидные товары)."""
    products = load_catalog(invalid_catalog_file)
    
    # Невалидные товары должны быть пропущены
    assert len(products) == 0


def test_load_empty_catalog():
    """Тест загрузки пустого каталога."""
    content = "products: []"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        products = load_catalog(temp_path)
        assert len(products) == 0
    finally:
        os.unlink(temp_path)


def test_load_nonexistent_file():
    """Тест загрузки несуществующего файла."""
    with pytest.raises(FileNotFoundError):
        load_catalog("nonexistent_file.yaml")


def test_product_validation():
    """Тест валидации модели Product."""
    # Валидный продукт
    valid_product = Product(
        id="test",
        name="Test",
        brand="Test Brand",
        category="cleanser"
    )
    assert valid_product.id == "test"
    
    # Невалидный продукт (отсутствует обязательное поле)
    with pytest.raises(Exception):
        Product(
            id="test",
            name="Test",
            # Отсутствует brand
            category="cleanser"
        )








