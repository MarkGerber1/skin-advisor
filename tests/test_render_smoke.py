"""Дымовые тесты для render модуля"""

import pytest
from unittest.mock import Mock


def test_render_import():
    """Тест импорта render модуля без SyntaxError"""
    try:
        from bot.ui.render import render_skincare_report, render_makeup_report

        print("✅ render.py syntax OK, imports successful")
        assert True
    except SyntaxError as e:
        pytest.fail(f"SyntaxError in render.py: {e}")
    except ImportError as e:
        pytest.fail(f"ImportError in render.py: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error importing render.py: {e}")


def test_render_skincare_basic():
    """Тест базового рендера skincare с пустыми данными"""
    try:
        from bot.ui.render import render_skincare_report

        # Пустой результат
        result = {"skincare": {}}
        text, kb = render_skincare_report(result)

        assert isinstance(text, str)
        assert len(text) > 0
        assert kb is not None
        print("✅ render_skincare_report works with empty data")

    except Exception as e:
        pytest.fail(f"render_skincare_report failed: {e}")


def test_render_makeup_basic():
    """Тест базового рендера makeup с пустыми данными"""
    try:
        from bot.ui.render import render_makeup_report

        # Пустой результат
        result = {"makeup": {}}
        text, kb = render_makeup_report(result)

        assert isinstance(text, str)
        assert len(text) > 0
        assert kb is not None
        print("✅ render_makeup_report works with empty data")

    except Exception as e:
        pytest.fail(f"render_makeup_report failed: {e}")


def test_render_skincare_with_data():
    """Тест рендера skincare с тестовыми данными"""
    try:
        from bot.ui.render import render_skincare_report

        # Тестовые данные
        result = {
            "skincare": {
                "cleanser": [
                    {
                        "id": "test-001",
                        "brand": "Test Brand",
                        "name": "Test Cleanser",
                        "price": 1000.0,
                        "currency": "RUB",
                        "link": "https://example.com/product/1",
                        "ref_link": "https://affiliate.example.com/product/1",
                        "category": "Очищение",
                    }
                ]
            }
        }

        text, kb = render_skincare_report(result)

        assert isinstance(text, str)
        assert len(text) > 0
        assert kb is not None
        assert "Test Cleanser" in text
        print("✅ render_skincare_report works with test data")

    except Exception as e:
        pytest.fail(f"render_skincare_report failed with data: {e}")


def test_render_makeup_with_data():
    """Тест рендера makeup с тестовыми данными"""
    try:
        from bot.ui.render import render_makeup_report

        # Тестовые данные
        result = {
            "makeup": {
                "base": [
                    {
                        "id": "foundation-001",
                        "brand": "Test Foundation",
                        "name": "Test Foundation",
                        "price": 2000.0,
                        "currency": "RUB",
                        "link": "https://example.com/foundation/1",
                        "ref_link": "https://affiliate.example.com/foundation/1",
                        "category": "Тональный крем",
                    }
                ]
            }
        }

        text, kb = render_makeup_report(result)

        assert isinstance(text, str)
        assert len(text) > 0
        assert kb is not None
        assert "Test Foundation" in text
        print("✅ render_makeup_report works with test data")

    except Exception as e:
        pytest.fail(f"render_makeup_report failed with data: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
