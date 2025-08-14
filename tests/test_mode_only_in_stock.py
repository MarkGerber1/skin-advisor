import app.services.recommendation as svc


def test_build_recommendations_enforces_only_in_stock(monkeypatch):
    calls = {}

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
        calls["availability_mode"] = availability_mode
        return {
            "products": [],
            "routines": {"am": [], "pm": [], "weekly": []},
            "summary": {},
        }

    monkeypatch.setattr(svc, "select_products_avail", fake_select)
    svc.build_recommendations({"skin_type": "normal"}, [])
    assert calls["availability_mode"] == "only_in_stock"

