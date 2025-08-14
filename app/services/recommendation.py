import os
import logging
from collections import Counter
from reco_engine import PricingPolicy, DeeplinkConfig, Product
from stock_availability import select_products_avail, StockCache
from app.services.catalog_normalize import normalize_items
from app.services.catalog import load_catalog_any


log = logging.getLogger("reco")


def build_recommendations(user_profile: dict) -> dict:
    # centralized catalog
    raw_products = load_catalog_any()
    # normalize and convert
    cat_items = [p.to_dict() if hasattr(p, "to_dict") else p for p in raw_products]
    cat_items = normalize_items(cat_items)
    products = [Product.from_dict(d) for d in cat_items]
    counts = Counter([getattr(p, "category", "") for p in products])
    if all((p.base_price or p.price or 0) == 0 for p in products):
        log.warning("reco: catalog has zero prices for all items")
    log.info("reco: catalog size=%d by_category=%s", len(products), dict(counts))

    policy = PricingPolicy(
        user_discount=float(os.getenv("USER_DISCOUNT", "0.05")),
        owner_commission=float(os.getenv("OWNER_COMMISSION", "0.10")),
        merchant_total_discount=0.15,
    )
    log.info(
        "reco: user=%s skin=%s concerns=%s",
        user_profile.get("uid"),
        user_profile.get("skin_type"),
        user_profile.get("concerns"),
    )
    base = select_products_avail(
        user_profile,
        products,
        partner_code=os.getenv("PARTNER_SUBID", "SUBID-123"),
        policy=policy,
        redirect_base=os.getenv("REDIRECT_BASE"),
        include_makeup=True,
        deeplink_cfg=DeeplinkConfig(network=os.getenv("DEEPLINK_NETWORK", "none")),
        availability_mode="only_in_stock",
        stock_cache=StockCache(ttl_sec=60),
    )
    log.info(
        "reco: products=%d unavailable=%d replaced=%d",
        len(base.get("products", [])),
        len(base.get("unavailable", [])),
        len(base.get("replaced", [])),
    )
    if not base.get("products"):
        log.warning(
            "reco: EMPTY after only_in_stock; sample=%s",
            [
                (
                    p.get("brand"),
                    p.get("name"),
                    (p.get("_stock") or {}).get("in_stock"),
                )
                for p in base.get("products", [])[:5]
            ],
        )
        # diagnostic rerun (only if explicitly enabled); optionally return fallback
        if os.getenv("RECO_DIAG") == "1" or os.getenv("RECO_FALLBACK", "0") == "1":
            try:
                diag = select_products_avail(
                    user_profile,
                    products,
                    partner_code=os.getenv("PARTNER_SUBID", "SUBID-123"),
                    policy=policy,
                    redirect_base=os.getenv("REDIRECT_BASE"),
                    include_makeup=True,
                    deeplink_cfg=DeeplinkConfig(
                        network=os.getenv("DEEPLINK_NETWORK", "none")
                    ),
                    availability_mode="prefer_in_stock",
                    stock_cache=StockCache(ttl_sec=60),
                )
                log.info(
                    "reco: diag prefer_in_stock products=%d",
                    len(diag.get("products", [])),
                )
                if os.getenv("RECO_FALLBACK", "0") == "1" and diag.get("products"):
                    log.warning(
                        "reco: returning prefer_in_stock due to empty only_in_stock"
                    )
                    return diag
            except Exception:
                log.exception("reco: diag run failed")
    return base
