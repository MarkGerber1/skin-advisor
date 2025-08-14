import re
from typing import Dict, Any, List


CATMAP = {
    r"\b(spf|sunscreen|sun|uv)\b": "sunscreen",
    r"\bcleanser|foam|гел[ья]\b": "cleanser",
    r"\btoner|tonic|тоник\b": "toner",
    r"\bserum|сыворотк": "serum",
    r"\bmoistur|крем|cream|эмульс\b": "moisturizer",
    r"\bretinol|ретин\b": "retinoid",
    r"\bexfol|peel|кислот|aha|bha\b": "exfoliant",
    r"\bfoundation|тональн|bb|cc\b": "foundation",
    r"\bconceal|консил\b": "concealer",
    r"\bpowder|пудр\b": "powder",
    r"\bblush|румян\b": "blush",
    r"\bbronzer|бронзер\b": "bronzer",
    r"\bhighlighter|хайлайт\b": "highlighter",
    r"\bshadow|palette|тени\b": "eyeshadow",
    r"\bmascara|туш\b": "mascara",
    r"\beyeliner|лайнер|подводк\b": "eyeliner",
    r"\bbrow|бров\b": "brow",
    r"\blip|губ\b": "lips",
}


def _guess_category(brand: str, name: str) -> str | None:
    text = f"{brand} {name}".lower()
    for pat, cat in CATMAP.items():
        if re.search(pat, text):
            return cat
    return None


def normalize_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, it in enumerate(items):
        brand = (it.get("brand") or "").strip()
        name = (it.get("name") or "").strip()
        link = it.get("link") or it.get("ref_link") or ""
        cat = (it.get("category") or "").strip()
        if not cat:
            cat = _guess_category(brand, name) or "serum"
        price_tier = (it.get("price_tier") or "mid").strip()
        base_price = float(it.get("base_price") or it.get("price") or 0.0)
        actives = it.get("actives") or []
        if not it.get("id"):
            it["id"] = f"auto_{i}"
        it.update(
            {
                "brand": brand,
                "name": name,
                "link": link,
                "category": cat,
                "price_tier": price_tier,
                "base_price": base_price,
                "actives": actives,
            }
        )
        out.append(it)
    return out

