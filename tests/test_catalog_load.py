from __future__ import annotations

from engine.catalog import load_catalog


def test_load_catalog_minimal():
    items = load_catalog("data/fixed_catalog.yaml")
    assert items, "catalog should not be empty"
    assert all(getattr(p, "brand", None) for p in items)


