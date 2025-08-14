from stock_availability import parse_ga_product


def test_add_to_cart_heuristic():
    html = '<button data-qa="add-to-cart">В корзину</button><meta itemprop="price" content="1999" />'
    assert parse_ga_product(html) == (True, 1999.0)

