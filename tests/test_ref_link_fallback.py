from reco_engine import Product, _build_product_card, PricingPolicy, DeeplinkConfig


def test_ref_link_fallback_search():
    p = Product(
        id="1",
        name="Make Up Expert",
        brand="NIVEA",
        category="foundation",
        price_tier="mid",
        base_price=1000.0,
    )
    card = _build_product_card(
        p.to_dict(),
        PricingPolicy(user_discount=0.0),
        partner_code="S1",
        deeplink_cfg=DeeplinkConfig(network="none"),
        redirect_base=None,
    )
    assert "goldapple.ru" in card["ref_link"]

