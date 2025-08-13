from stock_availability import parse_ga_product

def test_parse_instock_with_price():
	html = '<script type="application/ld+json">{"@type":"Product","offers":{"availability":"InStock"},"price":"2990"}</script>'
	assert parse_ga_product(html) == (True, 2990.0)

def test_parse_outofstock_with_price():
	html = '<script type="application/ld+json">{"@type":"Product","offers":{"availability":"OutOfStock"},"price":"1234"}</script>'
	assert parse_ga_product(html) == (False, 1234.0)

def test_parse_text_markers():
	assert parse_ga_product("нет в наличии") == (False, None)

