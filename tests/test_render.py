#!/usr/bin/env python3
"""
Тесты для рендеринга отчетов.
"""

import pytest
from pathlib import Path
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.ui.render import render_skincare_report, render_makeup_report


@pytest.fixture
def sample_skincare_result():
    """Создает тестовый результат для ухода за кожей."""
    return {
        "skincare": {
            "AM": [
                {
                    "id": "cleanser_1",
                    "brand": "Test Brand",
                    "name": "Gentle Cleanser",
                    "price": 500.0,
                    "price_currency": "RUB",
                    "ref_link": "https://example.com/cleanser1?aff=test",
                },
                {
                    "id": "serum_1",
                    "brand": "Test Brand",
                    "name": "Niacinamide Serum",
                    "price": 1200.0,
                    "price_currency": "RUB",
                    "ref_link": "https://example.com/serum1?aff=test",
                },
            ],
            "PM": [
                {
                    "id": "moisturizer_1",
                    "brand": "Test Brand",
                    "name": "Moisturizing Cream",
                    "price": 1500.0,
                    "price_currency": "RUB",
                    "ref_link": "https://example.com/moisturizer1?aff=test",
                }
            ],
            "weekly": [
                {
                    "id": "mask_1",
                    "brand": "Test Brand",
                    "name": "Hydrating Mask",
                    "price": 800.0,
                    "price_currency": "RUB",
                    "ref_link": "https://example.com/mask1?aff=test",
                }
            ],
        }
    }


@pytest.fixture
def sample_makeup_result():
    """Создает тестовый результат для макияжа."""
    return {
        "makeup": {
            "face": [
                {
                    "id": "foundation_1",
                    "brand": "Test Brand",
                    "name": "Foundation",
                    "price": 2000.0,
                    "price_currency": "RUB",
                    "ref_link": "https://example.com/foundation1?aff=test",
                }
            ],
            "brows": [
                {
                    "id": "brow_1",
                    "brand": "Test Brand",
                    "name": "Brow Pencil",
                    "price": 1000.0,
                    "price_currency": "RUB",
                    "ref_link": "https://example.com/brow1?aff=test",
                }
            ],
            "eyes": [
                {
                    "id": "mascara_1",
                    "brand": "Test Brand",
                    "name": "Mascara",
                    "price": 1200.0,
                    "price_currency": "RUB",
                    "ref_link": "https://example.com/mascara1?aff=test",
                }
            ],
            "lips": [
                {
                    "id": "lipstick_1",
                    "brand": "Test Brand",
                    "name": "Lipstick",
                    "price": 1500.0,
                    "price_currency": "RUB",
                    "ref_link": "https://example.com/lipstick1?aff=test",
                }
            ],
        }
    }


def test_render_skincare_report(sample_skincare_result):
    """Тест рендеринга отчета по уходу за кожей."""
    text, keyboard = render_skincare_report(sample_skincare_result)

    # Проверяем текст
    assert "📋 Персональный уход" in text
    assert "AM:" in text
    assert "PM:" in text
    assert "Weekly:" in text
    assert "Test Brand Gentle Cleanser" in text
    assert "500 ₽" in text

    # Проверяем клавиатуру
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Проверяем кнопки покупки
    buy_buttons = []
    for row in keyboard.inline_keyboard:
        for button in row:
            if button.url and "example.com" in button.url:
                buy_buttons.append(button)

    assert len(buy_buttons) > 0


def test_render_makeup_report(sample_makeup_result):
    """Тест рендеринга отчета по макияжу."""
    text, keyboard = render_makeup_report(sample_makeup_result)

    # Проверяем текст
    assert "🎨 Макияж по палитре" in text
    assert "Лицо:" in text
    assert "Брови:" in text
    assert "Глаза:" in text
    assert "Губы:" in text
    assert "Test Brand Foundation" in text
    assert "2000 ₽" in text

    # Проверяем клавиатуру
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0

    # Проверяем кнопки покупки
    buy_buttons = []
    for row in keyboard.inline_keyboard:
        for button in row:
            if button.url and "example.com" in button.url:
                buy_buttons.append(button)

    assert len(buy_buttons) > 0


def test_render_empty_skincare():
    """Тест рендеринга пустого отчета по уходу за кожей."""
    empty_result = {"skincare": {"AM": [], "PM": [], "weekly": []}}

    text, keyboard = render_skincare_report(empty_result)

    # Проверяем текст
    assert "📋 Персональный уход" in text
    assert "AM:" in text
    assert "PM:" in text
    assert "Weekly:" in text

    # Проверяем, что нет товаров
    assert "—" in text

    # Проверяем клавиатуру (должна быть кнопка "Обновить")
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 1
    assert keyboard.inline_keyboard[0][0].callback_data == "noop"


def test_render_empty_makeup():
    """Тест рендеринга пустого отчета по макияжу."""
    empty_result = {"makeup": {"face": [], "brows": [], "eyes": [], "lips": []}}

    text, keyboard = render_makeup_report(empty_result)

    # Проверяем текст
    assert "🎨 Макияж по палитре" in text
    assert "Лицо:" in text
    assert "Брови:" in text
    assert "Глаза:" in text
    assert "Губы:" in text

    # Проверяем, что нет товаров
    assert "—" in text

    # Проверяем клавиатуру (должна быть кнопка "Обновить")
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 1
    assert keyboard.inline_keyboard[0][0].callback_data == "noop"


def test_render_without_ref_links(sample_skincare_result):
    """Тест рендеринга без партнерских ссылок."""
    # Убираем ref_link из товаров
    for category in sample_skincare_result["skincare"].values():
        for product in category:
            product.pop("ref_link", None)

    text, keyboard = render_skincare_report(sample_skincare_result)

    # Проверяем текст
    assert "📋 Персональный уход" in text

    # Проверяем клавиатуру (должна быть кнопка "Обновить")
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 1
    assert keyboard.inline_keyboard[0][0].callback_data == "noop"
