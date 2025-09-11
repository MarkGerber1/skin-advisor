"""
Тесты для системы канонических слагов selector_schema
"""

import pytest
from engine.selector_schema import canon_slug, safe_get_skincare_data, SKINCARE_CANONICAL_SLUGS


class TestCanonSlug:
    """Тесты нормализации слагов"""

    def test_canon_slug_basic(self):
        """Тест базовой нормализации"""
        assert canon_slug("cleanser") == "cleanser"
        assert canon_slug("CLEANER") == "cleanser"
        assert canon_slug(" очищающее средство ") == "cleanser"
        assert canon_slug("тонер") == "toner"
        assert canon_slug("TOning") == "toner"

    def test_canon_slug_variants(self):
        """Тест всех вариантов для каждого канонического слага"""
        for canonical, variants in SKINCARE_CANONICAL_SLUGS.items():
            for variant in variants:
                assert canon_slug(variant) == canonical
                assert canon_slug(variant.upper()) == canonical
                assert canon_slug(f" {variant} ") == canonical

    def test_canon_slug_unknown(self):
        """Тест неизвестных слагов"""
        assert canon_slug("unknown_category") == "unknown_category"
        assert canon_slug("") == ""
        assert canon_slug(None) == None


class TestSafeGetSkincareData:
    """Тесты безопасного извлечения данных"""

    def test_safe_get_existing_data(self):
        """Тест извлечения существующих данных"""
        data = {
            "skincare": {
                "cleanser": [{"id": "test1"}],
                "toner": [{"id": "test2"}],
                "serum": [{"id": "test3"}],
            }
        }

        assert safe_get_skincare_data(data["skincare"], "cleanser") == [{"id": "test1"}]
        assert safe_get_skincare_data(data["skincare"], "очищающее средство") == [{"id": "test1"}]

    def test_safe_get_missing_data(self):
        """Тест извлечения отсутствующих данных"""
        data = {"skincare": {"cleanser": [{"id": "test1"}]}}
        assert safe_get_skincare_data(data["skincare"], "unknown") == []

    def test_safe_get_invalid_data(self):
        """Тест обработки некорректных данных"""
        assert safe_get_skincare_data(None, "cleanser") == []
        assert safe_get_skincare_data({}, "cleanser") == []
        assert safe_get_skincare_data("invalid", "cleanser") == []


if __name__ == "__main__":
    pytest.main([__file__])
