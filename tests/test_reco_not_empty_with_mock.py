import app.services.recommendation as svc


def test_reco_returns_products_with_mock(monkeypatch):
    def fake_select(
        user_profile,
        catalog,
        partner_code,
        policy,
        redirect_base,
        include_makeup,
        deeplink_cfg,
        availability_mode,
        stock_cache,
    ):
        return {
            "products": [
                {
                    "id": "1",
                    "brand": "Brand",
                    "name": "Item",
                    "_stock": {"in_stock": True, "price": 2990.0},
                },
            ],
            "routines": {"am": ["1"], "pm": [], "weekly": []},
        }

    monkeypatch.setattr(svc, "select_products_avail", fake_select)
    out = svc.build_recommendations(
        {"skin_type": "normal"}, [{"brand": "Brand", "name": "Item"}]
    )
    assert out["products"]

