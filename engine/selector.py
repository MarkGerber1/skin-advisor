from __future__ import annotations

import urllib.parse
from typing import Dict, List

from .models import Product, UserProfile


def _with_affiliate(link: str | None, partner_code: str, redirect_base: str | None) -> str | None:
    if not link:
        return None
    if redirect_base:
        return f"{redirect_base}?url={urllib.parse.quote(link, safe='')}\u0026aff={urllib.parse.quote(partner_code)}"
    sep = "&" if ("?" in link) else "?"
    return f"{link}{sep}aff={urllib.parse.quote(partner_code)}"


def _filter_catalog(catalog: List[Product], *, category: str | None = None, tags: List[str] | None = None,
                    actives: List[str] | None = None, finish: List[str] | None = None) -> List[Product]:
    result: List[Product] = []
    for p in catalog:
        if category and p.category != category:
            continue
        if tags:
            if not set(map(str.lower, p.tags or [])).intersection(set(map(str.lower, tags))):
                continue
        if actives:
            if not set(map(str.lower, p.actives or [])).intersection(set(map(str.lower, actives))):
                continue
        if finish:
            if not p.finish or (str(p.finish).lower() not in [f.lower() for f in finish]):
                continue
        if p.in_stock is False:
            continue
        result.append(p)
    return result


def _pick_top(products: List[Product], limit: int = 3) -> List[Product]:
    return products[:limit]


def select_products(
    user_profile: UserProfile,
    catalog: List[Product],
    partner_code: str,
    redirect_base: str | None = None,
) -> Dict:
    skincare: Dict[str, List[Dict]] = {"AM": [], "PM": [], "weekly": []}
    makeup: Dict[str, List[Dict]] = {"face": [], "brows": [], "eyes": [], "lips": []}

    skin_type = (user_profile.skin_type or "normal").lower()
    concerns = [c.lower() for c in user_profile.concerns or []]

    # Mapping активов под задачи
    concern_to_actives = {
        "acne": ["bha", "salicylic", "ниацинамид", "niacinamide"],
        "dehydration": ["hyaluronic", "гиалурон", "glycerin"],
        "redness": ["panthenol", "d-panthenol", "centella", "cica", "ниацинамид"],
        "pigmentation": ["vitamin c", "аскорб", "arbutin", "kojic"],
        "aging": ["retinol", "ретин", "peptide", "peptides"],
        "sensitivity": ["ceramide", "церамид", "panthenol"],
    }

    wanted_actives: List[str] = []
    for c in concerns:
        wanted_actives.extend(concern_to_actives.get(c, []))
    if skin_type == "oily":
        wanted_actives.extend(["niacinamide", "aha", "bha"])
    if skin_type == "dry":
        wanted_actives.extend(["ceramide", "squalane", "panthenol", "hyaluronic"])

    # AM routine
    am_cleanser = _pick_top(_filter_catalog(catalog, category="Очищение"), 1)
    am_toner = _pick_top(_filter_catalog(catalog, category="Тоник", actives=wanted_actives), 1)
    am_serum = _pick_top(_filter_catalog(catalog, category="Сыворотка", actives=wanted_actives), 2)
    am_moist = _pick_top(_filter_catalog(catalog, category="Крем", actives=wanted_actives), 1)
    am_spf = _pick_top(_filter_catalog(catalog, category="Солнцезащита"), 1)

    # PM routine
    pm_cleanser = _pick_top(_filter_catalog(catalog, category="Очищение"), 1)
    pm_treatment = _pick_top(_filter_catalog(catalog, category="Сыворотка", actives=wanted_actives), 2)
    pm_moist = _pick_top(_filter_catalog(catalog, category="Крем", actives=wanted_actives), 1)

    # Weekly
    weekly_exf = _pick_top(_filter_catalog(catalog, category="Пилинг", actives=wanted_actives), 1)
    weekly_mask = _pick_top(_filter_catalog(catalog, category="Маска", actives=wanted_actives), 1)

    def _as_dict(p: Product) -> Dict:
        return {
            "id": p.id,
            "brand": p.brand,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "price_currency": p.price_currency,
            "link": str(p.link) if p.link else None,
            "ref_link": _with_affiliate(str(p.link) if p.link else None, partner_code, redirect_base),
        }

    skincare["AM"] = [_as_dict(x) for x in (am_cleanser + am_toner + am_serum + am_moist + am_spf)]
    skincare["PM"] = [_as_dict(x) for x in (pm_cleanser + pm_treatment + pm_moist)]
    skincare["weekly"] = [_as_dict(x) for x in (weekly_exf + weekly_mask)]

    # Makeup simplistic mapping by undertone/value/contrast
    _ = (user_profile.undertone or "neutral")
    face = _pick_top(_filter_catalog(catalog, category="Тональный крем"), 2)
    brows = _pick_top(_filter_catalog(catalog, category="Брови"), 1)
    eyes = _pick_top(_filter_catalog(catalog, category="Тушь"), 1)
    lips = _pick_top(_filter_catalog(catalog, category="Помада"), 2)

    makeup["face"] = [_as_dict(x) for x in face]
    makeup["brows"] = [_as_dict(x) for x in brows]
    makeup["eyes"] = [_as_dict(x) for x in eyes]
    makeup["lips"] = [_as_dict(x) for x in lips]

    return {"skincare": skincare, "makeup": makeup}


