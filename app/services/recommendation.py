import os
from reco_engine import PricingPolicy, DeeplinkConfig
from stock_availability import select_products_avail, StockCache


def build_recommendations(user_profile, catalog):
	policy = PricingPolicy(
		user_discount=float(os.getenv("USER_DISCOUNT", "0.05")),
		owner_commission=float(os.getenv("OWNER_COMMISSION", "0.10")),
		merchant_total_discount=0.15,
	)
	return select_products_avail(
		user_profile, catalog,
		partner_code=os.getenv("PARTNER_SUBID", "SUBID-123"),
		policy=policy,
		redirect_base=os.getenv("REDIRECT_BASE"),
		include_makeup=True,
		deeplink_cfg=DeeplinkConfig(network=os.getenv("DEEPLINK_NETWORK", "none")),
		availability_mode="only_in_stock",
		stock_cache=StockCache(ttl_sec=60),
	)

