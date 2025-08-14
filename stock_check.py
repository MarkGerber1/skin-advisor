#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI: Gold Apple availability scanner
Usage:
  python stock_check.py --in catalog_user_ga_full.json --out stock_report.json --csv stock_report.csv
Options:
  --ttl  : cache TTL seconds (default 1800)
"""
import json
import argparse
import time
import re
from urllib.parse import quote

try:
    import requests  # type: ignore
except Exception:
    requests = None

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def http_get(url: str, timeout: float = 8.0) -> str | None:
    if not requests:
        return None
    try:
        r = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        if r.status_code == 200 and r.text:
            return r.text
    except Exception:
        return None
    return None


def goldapple_search(brand: str, name: str) -> str:
    q = quote(f"{brand} {name}".strip())
    return f"https://goldapple.ru/catalogsearch/result/?q={q}"


def resolve_from_search(search_url: str) -> str | None:
    html = http_get(search_url)
    if not html:
        return None
    m = re.search(r'href="(https?://goldapple\.ru/[0-9]{6,}[^"]+)"', html)
    if m:
        return m.group(1)
    m2 = re.search(r'href="(/([0-9]{6,}[^"]+))"', html)
    if m2:
        return "https://goldapple.ru" + m2.group(1)
    return None


def parse_product(html: str) -> tuple[bool | None, float | None]:
    if not html:
        return None, None
    for m in re.finditer(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.S | re.I,
    ):
        block = m.group(1)
        if '"Product"' in block:
            instock = (
                True
                if "InStock" in block
                else (False if "OutOfStock" in block else None)
            )
            mp = re.search(r'"price"\s*:\s*"?([0-9]+[\.,]?[0-9]*)', block)
            price = float(mp.group(1).replace(",", ".")) if mp else None
            return instock, price
    if re.search(r"нет в наличии|ожидается|sold out", html, re.I):
        return False, None
    if re.search(r"в наличии|доступно|в корзину|add to cart", html, re.I):
        return True, None
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="catalog JSON with items")
    ap.add_argument("--out", dest="out", required=True, help="output JSON report")
    ap.add_argument("--csv", dest="csv", required=False, help="optional CSV path")
    ap.add_argument("--ttl", dest="ttl", type=int, default=1800)
    args = ap.parse_args()

    with open(args.inp, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items") or data.get("products") or []

    report = []
    for it in items:
        brand = it.get("brand", "")
        name = it.get("name", "")
        url = it.get("link") or goldapple_search(brand, name)
        if "catalogsearch/result" in url:
            resolved = resolve_from_search(url)
            if resolved:
                url = resolved
        html = http_get(url)
        instock, price = parse_product(html) if html else (None, None)
        report.append(
            {
                "id": it.get("id"),
                "brand": brand,
                "name": name,
                "url_checked": url,
                "in_stock": instock,
                "price": price,
            }
        )
        time.sleep(0.3)  # бережём сайт

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(
            {"checked_at": int(time.time()), "items": report},
            f,
            ensure_ascii=False,
            indent=2,
        )

    if args.csv:
        import csv

        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["id", "brand", "name", "url_checked", "in_stock", "price"])
            for r in report:
                writer.writerow(
                    [
                        r["id"],
                        r["brand"],
                        r["name"],
                        r["url_checked"],
                        r["in_stock"],
                        r["price"],
                    ]
                )


if __name__ == "__main__":
    main()
