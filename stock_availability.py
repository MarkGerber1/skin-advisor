import json
import time
from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reco_engine import (
    DeeplinkConfig,
    PricingPolicy,
    compose_ga_link,
    env_deeplink_config,
    select_products,
)


@dataclass
class StockInfo:
    in_stock: Optional[bool]
    price: Optional[float]
    url_checked: str


class StockCache:
    def __init__(self, ttl_sec: int = 1800):
        self.ttl = ttl_sec
        self._data: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        item = self._data.get(key)
        if not item:
            return None
        if time.time() - item["ts"] > self.ttl:
            self._data.pop(key, None)
            return None
        return item["value"]

    def set(self, key: str, value: Dict[str, Any]):
        self._data[key] = {"ts": time.time(), "value": value}


def parse_ga_product(html: str) -> Tuple[Optional[bool], Optional[float]]:
    """Очень простой парсер признаков наличия/цены для Gold Apple из html/json-скрипта.
    Возвращает (in_stock, price) где price - float или None.
    """
    try:
        start = html.find('{"@type":"Product"')
        if start != -1:
            end = html.find("</script>", start)
            chunk = html[start:end] if end != -1 else html[start:]
            data = json.loads(chunk)
            offers = data.get("offers", {}) if isinstance(data, dict) else {}
            avail = offers.get("availability")
            price = offers.get("price") or data.get("price")
            price_f = (
                float(price)
                if isinstance(price, (int, float, str))
                and str(price).replace(".", "", 1).isdigit()
                else None
            )
            if isinstance(avail, str):
                if "InStock" in avail:
                    return True, price_f
                if "OutOfStock" in avail:
                    return False, price_f
    except Exception:
        pass
    # Fallback: detect schema.org URLs for availability and extract price
    try:
        if re.search(
            r'"availability"\s*:\s*"(?:https?:\/\/schema\.org\/)?InStock"', html, re.I
        ):
            mp = re.search(r'"price"\s*:\s*"?([0-9]+[\.,]?[0-9]*)', html)
            price = float(mp.group(1).replace(",", ".")) if mp else None
            return True, price
        if re.search(
            r'"availability"\s*:\s*"(?:https?:\/\/schema\.org\/)?OutOfStock"',
            html,
            re.I,
        ):
            mp = re.search(r'"price"\s*:\s*"?([0-9]+[\.,]?[0-9]*)', html)
            price = float(mp.group(1).replace(",", ".")) if mp else None
            return False, price
    except Exception:
        pass
    lower = html.lower()
    if "нет в наличии" in lower:
        return False, None
    # Heuristics: presence of add-to-cart button
    if re.search(r'data-qa\s*=\s*"add-to-cart"', html, re.I) or re.search(
        r">\s*в корзину\s*<", lower
    ):
        mp = re.search(r'itemprop="price"\s+content="([0-9]+[\.,]?[0-9]*)"', html)
        if not mp:
            mp = re.search(r'data-price\s*=\s*"([0-9]+[\.,]?[0-9]*)"', html)
        price = float(mp.group(1).replace(",", ".")) if mp else None
        return True, price
    return None, None


def _apply_live_pricing(item: Dict[str, Any], policy: PricingPolicy) -> None:
    """Заполняет user_price и аналитические поля на основе живой цены из _stock.price."""
    stock = item.get("_stock") or {}
    live_price = stock.get("price")
    if live_price is None:
        return
    item["user_price"] = round(
        live_price * (1.0 - (policy.user_discount or policy.discount_rate)), 2
    )
    an = item.setdefault("_analytics", {})
    an["owner_commission"] = round(
        live_price * (policy.owner_commission or policy.commission_rate), 2
    )
    an["total_discount_value"] = round(
        live_price * (policy.merchant_total_discount or 0.0), 2
    )


def _load_stock_report(path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _find_analog(
    product: Dict[str, Any],
    all_products: List[Dict[str, Any]],
    prefer_same_tier: bool = True,
) -> Optional[Dict[str, Any]]:
    # tolerate both dicts and objects with attributes
    def _get(obj, key):
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)

    cat = (_get(product, "category") or "").lower()
    tier = _get(product, "price_tier")
    pid = _get(product, "id")
    for p in all_products:
        p_id = _get(p, "id")
        if p_id == pid:
            continue
        if ((_get(p, "category") or "").lower()) != cat:
            continue
        if prefer_same_tier and _get(p, "price_tier") != tier:
            continue
        # normalize to dict if needed
        if not isinstance(p, dict) and hasattr(p, "to_dict"):
            return p.to_dict()
        return p
    return None


def select_products_avail(
    user_profile: Dict[str, Any],
    catalog: List[Dict[str, Any]],
    partner_code: Optional[str],
    policy: Optional[PricingPolicy] = None,
    redirect_base: Optional[str] = None,
    include_makeup: bool = True,
    deeplink_cfg: Optional[DeeplinkConfig] = None,
    availability_mode: str = "prefer_in_stock",
    stock_cache: Optional[StockCache] = None,
    preload_report: Optional[Path] = None,
) -> Dict[str, Any]:
    policy = policy or PricingPolicy()
    deeplink_cfg = deeplink_cfg or env_deeplink_config()
    stock_cache = stock_cache or StockCache()
    stock_report = _load_stock_report(preload_report)

    # Normalize incoming catalog (Product objects -> dicts)
    if catalog and not isinstance(catalog[0], dict):
        catalog = [c.to_dict() if hasattr(c, "to_dict") else dict(c) for c in catalog]  # type: ignore

    base = select_products(
        user_profile=user_profile,
        catalog=catalog,
        partner_code=partner_code,
        policy=policy,
        redirect_base=redirect_base,
        include_makeup=include_makeup,
        deeplink_cfg=deeplink_cfg,
    )

    unavailable: List[int] = []
    replaced: List[Dict[str, Any]] = []

    def check_product(prod: Dict[str, Any]) -> StockInfo:
        url = prod.get("ref_link") or compose_ga_link(
            prod.get("brand", ""), prod.get("name", "")
        )
        cache_key = url
        cached = stock_cache.get(cache_key)
        if cached:
            return StockInfo(
                in_stock=cached.get("in_stock"),
                price=cached.get("price"),
                url_checked=url,
            )
        info = stock_report.get(str(prod.get("id"))) if stock_report else None
        in_stock = info.get("in_stock") if info else None
        price = info.get("price") if info else None
        stock_cache.set(cache_key, {"in_stock": in_stock, "price": price})
        return StockInfo(in_stock=in_stock, price=price, url_checked=url)

    final_products: List[Dict[str, Any]] = []
    used_ids: set = set()
    # ensure products are dicts
    base_products: List[Dict[str, Any]] = []
    for item in base.get("products", []):
        if isinstance(item, dict):
            base_products.append(item)
        elif hasattr(item, "to_dict"):
            base_products.append(item.to_dict())
        else:
            # best-effort casting
            base_products.append(
                {
                    "id": getattr(item, "id", None),
                    "brand": getattr(item, "brand", None),
                    "name": getattr(item, "name", None),
                    "category": getattr(item, "category", None),
                    "price_tier": getattr(item, "price_tier", None),
                }
            )

    for p in list(base_products):
        info = check_product(p)
        p.setdefault("_stock", {})
        p["_stock"].update(
            {
                "in_stock": info.in_stock,
                "price": info.price,
                "url_checked": info.url_checked,
                "checked_at": time.time(),
            }
        )
        if availability_mode == "only_in_stock":
            if info.in_stock is True:
                _apply_live_pricing(p, policy)
                final_products.append(p)
                used_ids.add(p.get("id"))
                continue
            analog = _find_analog(p, catalog, prefer_same_tier=True) or _find_analog(
                p, catalog, prefer_same_tier=False
            )
            if analog:
                an_info = check_product(analog)
                analog.setdefault("_stock", {})
                analog["_stock"].update(
                    {
                        "in_stock": an_info.in_stock,
                        "price": an_info.price,
                        "url_checked": an_info.url_checked,
                        "checked_at": time.time(),
                    }
                )
                if an_info.in_stock is True:
                    _apply_live_pricing(analog, policy)
                    replaced.append({"from": p.get("id"), "to": analog.get("id")})
                    final_products.append(analog)
                    used_ids.add(analog.get("id"))
                    continue
            unavailable.append(p.get("id"))
        else:
            if info.in_stock is True:
                _apply_live_pricing(p, policy)
                final_products.append(p)
                used_ids.add(p.get("id"))
            elif info.in_stock is False:
                analog = _find_analog(
                    p, catalog, prefer_same_tier=True
                ) or _find_analog(p, catalog, prefer_same_tier=False)
                if analog:
                    an_info = check_product(analog)
                    analog.setdefault("_stock", {})
                    analog["_stock"].update(
                        {
                            "in_stock": an_info.in_stock,
                            "price": an_info.price,
                            "url_checked": an_info.url_checked,
                            "checked_at": time.time(),
                        }
                    )
                    if an_info.in_stock is True:
                        _apply_live_pricing(analog, policy)
                        replaced.append({"from": p.get("id"), "to": analog.get("id")})
                        final_products.append(analog)
                        used_ids.add(analog.get("id"))
                        continue
                _apply_live_pricing(p, policy)
                final_products.append(p)
                used_ids.add(p.get("id"))
            else:
                _apply_live_pricing(p, policy)
                final_products.append(p)
                used_ids.add(p.get("id"))

    base["products"] = final_products
    base["unavailable"] = unavailable
    base["replaced"] = replaced
    return base
