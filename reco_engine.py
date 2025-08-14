import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


GA_SEARCH_BASE = "https://goldapple.ru/catalogsearch/result/?q="


@dataclass
class PricingPolicy:
    # New fields per monetization
    user_discount: float = 0.0  # e.g., 0.05 for 5% user discount
    owner_commission: float = 0.0  # e.g., 0.10 for 10% commission
    merchant_total_discount: float = 0.0  # for analytics
    # Legacy aliases (kept for compatibility)
    commission_rate: float = 0.0
    discount_rate: float = 0.0

    def apply(self, base_price: Optional[float]) -> Optional[float]:
        if base_price is None:
            return None
        # Prefer new user_discount; fallback to legacy discount_rate
        disc = self.user_discount if self.user_discount > 0 else self.discount_rate
        price = base_price * (1 - max(disc, 0.0))
        return round(price, 2)


@dataclass
class DeeplinkConfig:
    network: str = "none"  # advcake|admitad|custom|none
    custom_template: Optional[str] = None


@dataclass
class Product:
    id: Any
    brand: str
    name: str
    category: str
    price_tier: Optional[str] = None
    price: Optional[float] = None
    base_price: Optional[float] = None
    usage: Optional[str] = None
    actives: Optional[List[str]] = None
    ga_url: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Product":
        return cls(
            id=d.get("id"),
            brand=d.get("brand", ""),
            name=d.get("name", ""),
            category=d.get("category", ""),
            price_tier=d.get("price_tier"),
            price=d.get("price") or d.get("base_price"),
            base_price=d.get("base_price") or d.get("price"),
            usage=d.get("purpose") or d.get("usage"),
            actives=d.get("actives") or [],
            ga_url=d.get("ga_url") or d.get("link"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "brand": self.brand,
            "name": self.name,
            "category": self.category,
            "price_tier": self.price_tier,
            "price": self.price or self.base_price,
            "purpose": self.usage,
            "usage": self.usage,
            "actives": self.actives or [],
            "ga_url": self.ga_url,
        }


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        # поддержка формата {"products": [...]} и прямого списка
        if (
            isinstance(data, dict)
            and "products" in data
            and isinstance(data["products"], list)
        ):
            return data["products"]
        return data


def _read_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError(
            "PyYAML не установлен. Установите pyyaml или используйте JSON каталог."
        )
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_catalog(preferred: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Загружает пользовательский каталог из YAML/JSON. Возвращает список продуктов (dict)."""
    candidates: List[Path] = []
    root = Path(__file__).resolve().parent
    if preferred:
        candidates.append(preferred)
    # Популярные имена файлов
    candidates += [
        root / "catalog_user.yaml",
        root / "catalog_user.json",
        root / "catalog_user_ga_full.json",
    ]
    for p in candidates:
        if p.exists():
            if p.suffix.lower() in (".yaml", ".yml"):
                data = _read_yaml(p)
                if isinstance(data, dict) and "products" in data:
                    return list(data["products"])
                return list(data)
            return list(_read_json(p))
    raise FileNotFoundError(
        "Каталог не найден. Поместите 'catalog_user.yaml' или 'catalog_user.json' или 'catalog_user_ga_full.json' рядом с проектом."
    )


def compose_ga_link(brand: str, name: str, direct_url: Optional[str] = None) -> str:
    from urllib.parse import quote

    if direct_url and "goldapple.ru" in direct_url:
        return direct_url
    query = quote(f"{brand} {name}")
    return f"{GA_SEARCH_BASE}{query}"


def _wrap_deeplink(
    url: str,
    partner_code: Optional[str],
    deeplink_cfg: Optional[DeeplinkConfig],
    redirect_base: Optional[str],
) -> str:
    final_url = url
    subid = partner_code or ""
    if redirect_base:
        from urllib.parse import quote

        return (
            f"{redirect_base.rstrip('/')}/r?url={quote(final_url)}&subid={quote(subid)}"
        )
    if deeplink_cfg and deeplink_cfg.network.lower() != "none":
        net = deeplink_cfg.network.lower()
        if net == "custom" and deeplink_cfg.custom_template:
            return deeplink_cfg.custom_template.replace("{url}", final_url).replace(
                "{subid}", subid
            )
        # Заглушки для сетей (подставьте реальные шаблоны при интеграции)
        if net == "advcake":
            return f"https://advcake.example/deeplink?url={final_url}&subid={subid}"
        if net == "admitad":
            return f"https://admitad.example/deeplink?ulp={final_url}&subid={subid}"
    return final_url


def _product_analytics(product: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": product.get("id"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "price_tier": product.get("price_tier"),
    }


def _category_for_routines(category: str) -> Optional[str]:
    """Мэппинг категорий каталога к AM/PM/weekly слотам."""
    cat = category.lower()
    if cat in ("очищение", "cleanser", "wash"):
        return "cleanser"
    if cat in ("сыворотка", "serum"):
        return "serum"
    if cat in ("увлажнение", "крем", "moisturizer", "cream"):
        return "moisturizer"
    if cat in ("spf", "sunscreen"):
        return "spf"
    if cat in ("маска", "mask", "пилинг", "peel"):
        return "weekly"
    # декоративка
    if cat in (
        "тон",
        "foundation",
        "powder",
        "blush",
        "bronzer",
        "concealer",
        "lip",
        "губы",
    ):
        return "makeup"
    return None


def _score_product(user_profile: Dict[str, Any], product: Dict[str, Any]) -> int:
    score = 0
    skin_type = (user_profile.get("skin_type") or "").lower()
    concerns: List[str] = [c.lower() for c in user_profile.get("concerns", [])]
    ptype = [p.lower() for p in product.get("skin_type", [])]
    pstate = [p.lower() for p in product.get("skin_state", [])]
    if skin_type and (skin_type in ptype or "любой" in ptype or "any" in ptype):
        score += 2
    if concerns:
        score += len(set(concerns) & set(pstate))
    return score


def _build_product_card(
    product: Dict[str, Any],
    policy: PricingPolicy,
    partner_code: Optional[str],
    deeplink_cfg: Optional[DeeplinkConfig],
    redirect_base: Optional[str],
) -> Dict[str, Any]:
    brand = product.get("brand", "")
    name = product.get("name", "")
    ga_url = product.get("ga_url")
    base_url = compose_ga_link(brand, name, ga_url)
    ref_link = _wrap_deeplink(base_url, partner_code, deeplink_cfg, redirect_base)
    user_price = policy.apply(product.get("price")) if "price" in product else None
    card = {
        "id": product.get("id"),
        "name": name,
        "brand": brand,
        "category": product.get("category", ""),
        "price_tier": product.get("price_tier"),
        "usage": product.get("purpose") or product.get("usage") or "",
        "actives": product.get("actives", []),
        "user_price": user_price,
        "ref_link": ref_link,
        "_analytics": _product_analytics(product),
    }
    # annotate analytics with policy rates
    card["_analytics"].update(
        {
            "owner_commission_rate": policy.owner_commission or policy.commission_rate,
            "user_discount_rate": policy.user_discount or policy.discount_rate,
            "merchant_total_discount_rate": policy.merchant_total_discount,
        }
    )
    return card


def select_products(
    user_profile: Dict[str, Any],
    catalog: List[Any],
    partner_code: Optional[str],
    policy: Optional[PricingPolicy] = None,
    redirect_base: Optional[str] = None,
    include_makeup: bool = True,
    deeplink_cfg: Optional[DeeplinkConfig] = None,
) -> Dict[str, Any]:
    """Основной движок подбора. Возвращает summary, products (карточки), routines и makeup-блок."""
    policy = policy or PricingPolicy()

    # Отбираем кандидатов по простому скорингу
    # normalize incoming items to dicts
    normalized: List[Dict[str, Any]] = []
    for p in catalog:
        if hasattr(p, "to_dict"):
            normalized.append(p.to_dict())
        else:
            normalized.append(p)
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for p in normalized:
        scored.append((_score_product(user_profile, p), p))
    scored.sort(key=lambda x: x[0], reverse=True)

    picked: List[Dict[str, Any]] = []
    routines = {"am": [], "pm": [], "weekly": []}
    makeup: Dict[str, List[int]] = {}

    # Проходим по отсортированным и забираем по слотам/категориям
    for _, p in scored:
        cat_key = _category_for_routines(str(p.get("category", "")))
        if not cat_key:
            continue
        card = _build_product_card(p, policy, partner_code, deeplink_cfg, redirect_base)
        picked.append(card)
        pid = card["id"]
        if cat_key == "weekly":
            if pid not in routines["weekly"]:
                routines["weekly"].append(pid)
        elif cat_key == "makeup" and include_makeup:
            grp = p.get("category", "makeup").lower()
            makeup.setdefault(grp, []).append(pid)
        else:
            # Простая логика: cleanser/serum/moisturizer/spf -> раскидать по am/pm
            for section in ("am", "pm"):
                if pid not in routines[section]:
                    routines[section].append(pid)

    summary = {
        "skin_type": user_profile.get("skin_type"),
        "modifiers": user_profile.get("modifiers", []),
        "concerns": user_profile.get("concerns", []),
        "disclaimer": user_profile.get("disclaimer")
        or "Информация носит образовательный характер.",
    }
    result: Dict[str, Any] = {
        "summary": summary,
        "products": picked,
        "routines": routines,
    }
    if include_makeup:
        result["makeup"] = makeup
    return result


def env_deeplink_config() -> DeeplinkConfig:
    network = os.getenv("DEEPLINK_NETWORK", "none")
    custom_template = os.getenv("DEEPLINK_CUSTOM_TEMPLATE")
    return DeeplinkConfig(network=network, custom_template=custom_template)
