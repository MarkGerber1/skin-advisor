from app.services.catalog_normalize import normalize_items


def test_normalize_assigns_category():
    items = [{"brand": "NIVEA", "name": "make up expert"}]
    out = normalize_items(items)
    assert out[0]["category"] in {
        "foundation",
        "serum",
        "moisturizer",
        "powder",
        "blush",
        "bronzer",
        "highlighter",
        "eyeshadow",
        "mascara",
        "eyeliner",
        "brow",
        "lips",
        "cleanser",
        "toner",
        "sunscreen",
        "exfoliant",
        "retinoid",
    }

