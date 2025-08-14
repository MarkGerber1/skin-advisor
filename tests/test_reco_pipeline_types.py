from app.services.recommendation import build_recommendations


def test_build_recommendations_accepts_dicts(monkeypatch):
    # monkeypatch select_products_avail to capture catalog type
    received = {}

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
        received["types"] = [type(x).__name__ for x in catalog]
        return {"products": [], "routines": {"am": [], "pm": [], "weekly": []}}

    import app.services.recommendation as svc

    monkeypatch.setattr(svc, "select_products_avail", fake_select)
    build_recommendations({"skin_type": "normal"}, [{"brand": "B", "name": "N"}])
    assert received["types"][0] in ("Product",)

