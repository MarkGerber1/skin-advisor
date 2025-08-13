from stock_availability import _apply_live_pricing
from reco_engine import PricingPolicy

def test_live_pricing_applies_user_price_and_commission():
	item = {"_stock": {"price": 2990.0}, "_analytics": {}}
	policy = PricingPolicy(user_discount=0.05, owner_commission=0.10, merchant_total_discount=0.15)
	_apply_live_pricing(item, policy)
	assert item["user_price"] == 2840.5
	assert item["_analytics"]["owner_commission"] == 299.0

