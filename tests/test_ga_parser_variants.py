from stock_availability import parse_ga_product


def test_schema_org_availability():
    html = '<script type="application/ld+json">{"offers":{"availability":"https://schema.org/InStock"},"price":"2990"}</script>'
    assert parse_ga_product(html) == (True, 2990.0)

