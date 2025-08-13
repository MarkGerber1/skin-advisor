"""
Stock & Availability helpers for Gold Apple (GA)
================================================

Что это
-------
Модуль добавляет к боту:
1) Проверку наличия и цены по ссылке goldapple.ru (через JSON‑LD/эвристики).
2) Кэш результатов, чтобы не долбить сайт (TTL по умолч. 30 мин).
3) Обёртку `select_products_avail(...)`, которая вызывает ваш `select_products(...)`,
   проверяет наличие и при необходимости подбирает аналоги из вашего каталога.

Как использовать
---------------
from stock_availability import select_products_avail, StockCache
rec = select_products_avail(
    user_profile, catalog, partner_code,
    policy=PricingPolicy(), redirect_base=None,
    include_makeup=True, deeplink_cfg=DeeplinkConfig(network="none"),
    availability_mode="prefer_in_stock",
    stock_cache=StockCache(ttl_sec=1800)
)

Ограничения
-----------
GA может отдавать часть данных через JS; используется JSON‑LD и текстовые маркеры.
Для ссылок-поиска модуль пытается резолвить первую карточку товара.
Для масштаба рекомендуются партнёрские фиды.
"""
from __future__ import annotations
from typing import Any, Dict, List
from dataclasses import dataclass, asdict
import time, json, re
from reco_engine import (
    select_products, PricingPolicy, DeeplinkConfig, goldapple_search_url
)

@dataclass
class StockRecord:
    url: str
    in_stock: bool | None = None
    price: float | None = None
    checked_at: float = 0.0

class StockCache:
    def __init__(self, path: str = "stock_cache.json", ttl_sec: int = 1800):
        self.path = path
        self.ttl = ttl_sec
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data: Dict[str, Any] = json.load(f)
        except Exception:
            self.data = {}

    def get(self, url: str) -> StockRecord | None:
        rec = self.data.get(url)
        if not rec:
            return None
        if time.time() - rec.get("checked_at", 0) > self.ttl:
            return None
        return StockRecord(**rec)

    def put(self, rec: StockRecord):
        self.data[rec.url] = asdict(rec)
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

try:
    import requests
except Exception:
    requests = None

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

def _http_get(url: str, timeout: float = 8.0) -> str | None:
    if not requests:
        return None
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and r.text:
            return r.text
    except Exception:
        return None
    return None


def parse_ga_product(html: str) -> tuple[bool | None, float | None]:
    if not html:
        return None, None
    for m in re.finditer(r"<script[^>]*type=\"application/ld\+json\"[^>]*>(.*?)</script>", html, re.S|re.I):
        block = m.group(1)
        if '"Product"' in block:
            instock = True if "InStock" in block else (False if "OutOfStock" in block else None)
            mp = re.search(r'"price"\s*:\s*"?([0-9]+[\.,]?[0-9]*)', block)
            price = float(mp.group(1).replace(',', '.')) if mp else None
            return instock, price
    if re.search(r"нет в наличии|ожидается|sold out", html, re.I):
        return False, None
    if re.search(r"в наличии|доступно|в корзину|add to cart", html, re.I):
        return True, None
    return None, None


def resolve_ga_product_url_from_search(search_url: str) -> str | None:
    html = _http_get(search_url)
    if not html:
        return None
    m = re.search(r"href=\"(https?://goldapple\.ru/[0-9]{6,}[^\"]+)\"", html)
    if m:
        return m.group(1)
    m2 = re.search(r"href=\"(/([0-9]{6,}[^\"]+))\"", html)
    if m2:
        return "https://goldapple.ru" + m2.group(1)
    return None


def check_ga_availability(url_or_search: str, cache: StockCache | None = None) -> StockRecord:
    cache = cache or StockCache()
    cached = cache.get(url_or_search)
    if cached:
        return cached
    url = url_or_search
    if "catalogsearch/result" in url_or_search:
        resolved = resolve_ga_product_url_from_search(url_or_search)
        if resolved:
            url = resolved
    html = _http_get(url)
    in_stock, price = parse_ga_product(html) if html else (None, None)
    rec = StockRecord(url=url, in_stock=in_stock, price=price, checked_at=time.time())
    cache.put(rec)
    return rec


def find_alternatives(base_item: Dict[str, Any], all_items: List[Dict[str, Any]], max_n: int = 3) -> List[Dict[str, Any]]:
    cat = base_item.get("category")
    tier = base_item.get("price_tier")
    primary = [x for x in all_items if x.get("category") == cat and x.get("price_tier") == tier and x.get("id") != base_item.get("id")]
    secondary = [x for x in all_items if x.get("category") == cat and x.get("id") != base_item.get("id") and x not in primary]
    return (primary + secondary)[:max_n]


def select_products_avail(user_profile: Dict[str, Any], catalog: List[Any], partner_code: str,
                          policy: PricingPolicy = PricingPolicy(), redirect_base: str | None = None,
                          include_makeup: bool = True, deeplink_cfg: DeeplinkConfig | None = None,
                          availability_mode: str = "prefer_in_stock",
                          stock_cache: StockCache | None = None) -> Dict[str, Any]:
    base = select_products(user_profile, catalog, partner_code, policy, redirect_base, include_makeup, deeplink_cfg)
    if availability_mode == "ignore":
        return base
    stock_cache = stock_cache or StockCache()
    products = base.get("products", [])
    unavailable: List[str] = []
    replaced: List[Dict[str, str]] = []
    final_products: List[Dict[str, Any]] = []
    used_ids = set()
    for item in products:
        item_id = item.get("id")
        if item_id in used_ids:
            continue
        brand = item.get("brand", "")
        name = item.get("name", "")
        ga_url = item.get("ref_link") or item.get("link")
        if not ga_url or "goldapple.ru" not in ga_url:
            ga_url = goldapple_search_url(brand, name)
        rec = check_ga_availability(ga_url, cache=stock_cache)
        item.setdefault("_stock", {})
        item["_stock"].update({"in_stock": rec.in_stock, "price": rec.price, "url_checked": rec.url})
        if availability_mode == "only_in_stock":
            if rec.in_stock is True:
                final_products.append(item)
                used_ids.add(item_id)
            else:
                analogs = find_alternatives(item, products, max_n=3)
                picked = None
                for an in analogs:
                    an_id = an.get("id")
                    if an_id in used_ids:
                        continue
                    b2, n2 = an.get("brand", ""), an.get("name", "")
                    url2 = an.get("ref_link") or an.get("link") or goldapple_search_url(b2, n2)
                    r2 = check_ga_availability(url2, cache=stock_cache)
                    an.setdefault("_stock", {})
                    an["_stock"].update({"in_stock": r2.in_stock, "price": r2.price, "url_checked": r2.url})
                    if r2.in_stock is True:
                        picked = an
                        break
                if picked:
                    replaced.append({"from": item_id, "to": picked.get("id")})
                    final_products.append(picked)
                    used_ids.add(picked.get("id"))
                else:
                    unavailable.append(item_id)
            continue
        if rec.in_stock is False:
            analogs = find_alternatives(item, products, max_n=3)
            picked = None
            for an in analogs:
                an_id = an.get("id")
                if an_id in used_ids:
                    continue
                b2, n2 = an.get("brand", ""), an.get("name", "")
                url2 = an.get("ref_link") or an.get("link") or goldapple_search_url(b2, n2)
                r2 = check_ga_availability(url2, cache=stock_cache)
                an.setdefault("_stock", {})
                an["_stock"].update({"in_stock": r2.in_stock, "price": r2.price, "url_checked": r2.url})
                if r2.in_stock is True:
                    picked = an
                    break
            if picked:
                replaced.append({"from": item_id, "to": picked.get("id")})
                final_products.append(picked)
                used_ids.add(picked.get("id"))
            else:
                final_products.append(item)
                used_ids.add(item_id)
        else:
            final_products.append(item)
            used_ids.add(item_id)
    base["products"] = final_products
    base["unavailable"] = unavailable
    base["replaced"] = replaced
    return base

if __name__ == "__main__":
    h1 = '<script type="application/ld+json">{"@type":"Product","offers":{"availability":"InStock"},"price":"1999"}</script>'
    a1 = parse_ga_product(h1)
    assert a1 == (True, 1999.0)
    h2 = '<script type="application/ld+json">{"@type":"Product","offers":{"availability":"OutOfStock"},"price":"1234"}</script>'
    a2 = parse_ga_product(h2)
    assert a2 == (False, 1234.0)
    h3 = 'нет в наличии'
    a3 = parse_ga_product(h3)
    assert a3 == (False, None)
    h4 = 'в корзину'
    a4 = parse_ga_product(h4)
    assert a4 == (True, None)
    def fake_get(url: str, timeout: float = 8.0) -> str | None:
        return '<a href="/123456-test-item">x</a>'
    _orig = _http_get
    _globals = globals()
    _globals['_http_get'] = fake_get
    s = resolve_ga_product_url_from_search("https://goldapple.ru/catalogsearch/result/?q=test")
    assert s == "https://goldapple.ru/123456-test-item"
    _globals['_http_get'] = _orig
    print("OK")
