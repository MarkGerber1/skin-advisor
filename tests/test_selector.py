from __future__ import annotations

from engine.catalog import load_catalog
from engine.models import UserProfile
from engine.selector import select_products


def test_selector_slots():
    catalog = load_catalog("data/fixed_catalog.yaml")
    prof = UserProfile(skin_type="oily", concerns=["acne"], undertone="neutral")
    res = select_products(prof, catalog, partner_code="t")
    s = res.get("skincare", {})
    assert s.get("AM"), "AM should be populated"
    assert s.get("PM"), "PM should be populated"


