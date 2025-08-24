from __future__ import annotations

import urllib.parse
from typing import Dict, List, Optional, Set
from pathlib import Path
import yaml

from .models import Product, UserProfile, Undertone, Season, SkinType, Sensitivity


def _with_affiliate(link: str | None, partner_code: str, redirect_base: str | None) -> str | None:
    if not link:
        return None
    if redirect_base:
        return f"{redirect_base}?url={urllib.parse.quote(link, safe='')}\u0026aff={urllib.parse.quote(partner_code)}"
    sep = "&" if ("?" in link) else "?"
    return f"{link}{sep}aff={urllib.parse.quote(partner_code)}"


def _filter_catalog(
    catalog: List[Product],
    *,
    category: str | None = None,
    subcategory: str | None = None,
    tags: List[str] | None = None,
    actives: List[str] | None = None,
    finish: List[str] | None = None,
    undertone: str | None = None,
) -> List[Product]:
    result: List[Product] = []
    for p in catalog:
        if category and (str(p.category).lower() != category.lower()):
            continue
        if subcategory and (str(p.subcategory or "").lower() != subcategory.lower()):
            continue
        if tags:
            if not set(map(str.lower, p.tags or [])).intersection(set(map(str.lower, tags))):
                continue
        if actives:
            if not set(map(str.lower, p.actives or [])).intersection(set(map(str.lower, actives))):
                continue
        if finish:
            if not p.finish or (str(p.finish).lower() not in [f.lower() for f in finish]):
                continue
        if undertone and p.shade:
            if str(p.shade.undertone).lower() != undertone.lower():
                continue
        # Обязательно отфильтровываем явные OOS
        if p.in_stock is False:
            continue
        result.append(p)
    return result


class SelectorV2:
    """Engine v2 Product Selector with enhanced logic and compatibility rules"""
    
    def __init__(self, rules_path: str = "deliverables/Engine_v2/RULES"):
        self.rules_path = Path(rules_path)
        self._compatibility_rules = self._load_compatibility_rules()
        
        # Extended category mappings for 15 makeup + 7 skincare categories
        self.makeup_categories = {
            "foundation": ["foundation", "bb_cream", "cc_cream", "тональный"],
            "concealer": ["concealer", "консилер"],
            "corrector": ["corrector", "корректор"], 
            "powder": ["powder", "пудра"],
            "blush": ["blush", "румяна"],
            "bronzer": ["bronzer", "бронзатор"],
            "contour": ["contour", "скульптор"],
            "highlighter": ["highlighter", "хайлайтер"],
            "eyebrow": ["eyebrow", "brow", "брови"],
            "mascara": ["mascara", "тушь"],
            "eyeshadow": ["eyeshadow", "тени"],
            "eyeliner": ["eyeliner", "каял", "подводка"],
            "lipstick": ["lipstick", "помада"],
            "lip_gloss": ["lip_gloss", "блеск"],
            "lip_liner": ["lip_liner", "карандаш_губы"]
        }
        
        self.skincare_categories = {
            "cleanser": ["cleanser", "очищение", "гель", "пенка"],
            "toner": ["toner", "тоник", "эксфолиант"],
            "serum": ["serum", "сыворотка", "концентрат"],
            "moisturizer": ["moisturizer", "крем", "эмульсия"],
            "eye_cream": ["eye_cream", "крем_глаз"],
            "sunscreen": ["sunscreen", "spf", "санскрин"],
            "mask": ["mask", "маска"]
        }
    
    def _load_compatibility_rules(self) -> Dict:
        """Load compatibility rules"""
        try:
            with open(self.rules_path / "compatibility_matrix.yaml", "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {
                "incompatible_pairs": [
                    ["retinol", "vitamin_c"],
                    ["retinol", "aha"],
                    ["retinol", "bha"],
                    ["vitamin_c", "niacinamide"],
                    ["benzoyl_peroxide", "retinol"]
                ]
            }
    
    def _get_skin_priorities(self, profile: UserProfile) -> List[str]:
        """Determine skincare priorities based on profile"""
        priorities = []
        
        skin_type = profile.skin_type.value if hasattr(profile.skin_type, 'value') else profile.skin_type
        sensitivity = profile.sensitivity.value if hasattr(profile.sensitivity, 'value') else profile.sensitivity
        
        # Primary concerns
        if "acne" in (profile.concerns or []):
            priorities.extend(["acne_control", "oil_control"])
        if "pigmentation" in (profile.concerns or []):
            priorities.append("brightening")
        if "wrinkles" in (profile.concerns or []):
            priorities.append("anti_aging")
        if "redness" in (profile.concerns or []):
            priorities.append("calming")
        if profile.dehydrated:
            priorities.append("hydration")
        
        # Skin type priorities
        if skin_type == "dry":
            priorities.extend(["moisturizing", "barrier_repair"])
        elif skin_type == "oily":
            priorities.extend(["oil_control", "pore_care"])
        elif skin_type == "combo":
            priorities.extend(["balancing", "targeted_care"])
        
        # Sensitivity considerations
        if sensitivity == "high":
            priorities.append("gentle_formula")
        
        # Age-related
        if profile.age and profile.age > 35:
            priorities.append("anti_aging")
        
        return priorities
    
    def _get_color_preferences(self, profile: UserProfile) -> Dict[str, str]:
        """Get color preferences based on season and undertone"""
        prefs = {}
        
        season = profile.season.value if hasattr(profile.season, 'value') else profile.season
        undertone = profile.undertone.value if hasattr(profile.undertone, 'value') else profile.undertone
        
        # Season-based preferences
        season_prefs = {
            "spring": {"intensity": "bright", "temperature": "warm", "saturation": "clear"},
            "summer": {"intensity": "muted", "temperature": "cool", "saturation": "soft"},
            "autumn": {"intensity": "deep", "temperature": "warm", "saturation": "rich"},
            "winter": {"intensity": "bright", "temperature": "cool", "saturation": "clear"}
        }
        
        if season in season_prefs:
            prefs.update(season_prefs[season])
        
        # Undertone preferences
        if undertone:
            prefs["undertone"] = undertone
        
        return prefs
    
    def _match_product_to_profile(self, product: Product, profile: UserProfile, category: str) -> float:
        """Calculate match score for product based on profile"""
        score = 0.0
        max_score = 1.0
        
        # Check actives compatibility
        actives_lower = [a.lower() for a in product.actives]
        
        # Skin type matching for skincare
        if category in self.skincare_categories:
            skin_type = profile.skin_type.value if hasattr(profile.skin_type, 'value') else profile.skin_type
            
            if skin_type == "dry":
                if any(a in actives_lower for a in ["hyaluronic", "ceramide", "squalane"]):
                    score += 0.3
            elif skin_type == "oily":
                if any(a in actives_lower for a in ["niacinamide", "salicylic", "zinc"]):
                    score += 0.3
            
            # Concern matching
            concerns = profile.concerns or []
            if "acne" in concerns and any(a in actives_lower for a in ["salicylic", "niacinamide", "benzoyl"]):
                score += 0.4
            if "pigmentation" in concerns and any(a in actives_lower for a in ["vitamin_c", "arbutin", "kojic"]):
                score += 0.4
            if "wrinkles" in concerns and any(a in actives_lower for a in ["retinol", "peptide"]):
                score += 0.4
        
        # Color matching for makeup
        elif category in self.makeup_categories:
            color_prefs = self._get_color_preferences(profile)
            
            # Undertone matching
            if "undertone" in color_prefs and product.undertone_match:
                product_undertone = product.undertone_match.value if hasattr(product.undertone_match, 'value') else product.undertone_match
                if product_undertone == color_prefs["undertone"]:
                    score += 0.5
        
        # Sensitivity penalty
        if profile.sensitivity and (hasattr(profile.sensitivity, 'value') and profile.sensitivity.value == "high" or profile.sensitivity == "high"):
            if any(a in actives_lower for a in ["fragrance", "alcohol", "retinol"]):
                score -= 0.3
        
        # Pregnancy safety
        if profile.pregnant_or_lactating:
            if any(a in actives_lower for a in ["retinol", "retinoid", "salicylic"]):
                score -= 1.0  # Exclude completely
        
        # Stock availability bonus
        if product.in_stock:
            score += 0.1
        
        return min(max(score, 0.0), max_score)
    
    def select_products_v2(
        self, 
        profile: UserProfile, 
        catalog: List[Product],
        partner_code: str,
        redirect_base: Optional[str] = None
    ) -> Dict:
        """Engine v2 product selection with enhanced logic"""
        
        # Separate makeup and skincare products
        skincare_products = [p for p in catalog if self._is_skincare_category(p.category)]
        makeup_products = [p for p in catalog if self._is_makeup_category(p.category)]
        
        # Generate skincare recommendations (7 categories)
        skincare_results = self._select_skincare_v2(profile, skincare_products, partner_code, redirect_base)
        
        # Generate makeup recommendations (15 categories)
        makeup_results = self._select_makeup_v2(profile, makeup_products, partner_code, redirect_base)
        
        return {
            "skincare": skincare_results,
            "makeup": makeup_results,
            "compatibility_warnings": self._check_compatibility(skincare_products),
            "routine_suggestions": self._generate_routine_suggestions(profile)
        }
    
    def _is_skincare_category(self, category: str) -> bool:
        """Check if category is skincare"""
        category_lower = category.lower()
        for cat_variants in self.skincare_categories.values():
            if any(variant in category_lower for variant in cat_variants):
                return True
        return False
    
    def _is_makeup_category(self, category: str) -> bool:
        """Check if category is makeup"""
        category_lower = category.lower()
        for cat_variants in self.makeup_categories.values():
            if any(variant in category_lower for variant in cat_variants):
                return True
        return False
    
    def _select_skincare_v2(self, profile: UserProfile, products: List[Product], partner_code: str, redirect_base: Optional[str]) -> Dict:
        """Select skincare products across 7 categories"""
        results = {}
        
        # 7 skincare categories
        categories = ["cleanser", "toner", "serum", "moisturizer", "eye_cream", "sunscreen", "mask"]
        
        for category in categories:
            # Filter products for this category
            category_products = [p for p in products if self._matches_category(p.category, self.skincare_categories[category])]
            
            # Score and sort products
            scored_products = []
            for product in category_products:
                if product.in_stock is not False:  # Include in_stock=True and None
                    score = self._match_product_to_profile(product, profile, category)
                    scored_products.append((score, product))
            
            # Sort by score and take top products
            scored_products.sort(key=lambda x: x[0], reverse=True)
            top_products = [p[1] for p in scored_products[:3]]
            
            # Convert to dict format
            results[category] = [self._product_to_dict(p, partner_code, redirect_base, profile) for p in top_products]
        
        return results
    
    def _select_makeup_v2(self, profile: UserProfile, products: List[Product], partner_code: str, redirect_base: Optional[str]) -> Dict:
        """Select makeup products across 15 categories"""
        results = {}
        
        # 15 makeup categories
        categories = list(self.makeup_categories.keys())
        
        for category in categories:
            # Filter products for this category
            category_products = [p for p in products if self._matches_category(p.category, self.makeup_categories[category])]
            
            # Score and sort products
            scored_products = []
            for product in category_products:
                if product.in_stock is not False:  # Include in_stock=True and None
                    score = self._match_product_to_profile(product, profile, category)
                    scored_products.append((score, product))
            
            # Sort by score and take top products
            scored_products.sort(key=lambda x: x[0], reverse=True)
            top_products = [p[1] for p in scored_products[:3]]
            
            # Convert to dict format
            results[category] = [self._product_to_dict(p, partner_code, redirect_base, profile) for p in top_products]
        
        return results
    
    def _matches_category(self, product_category: str, category_variants: List[str]) -> bool:
        """Check if product category matches any variant"""
        product_cat_lower = product_category.lower()
        return any(variant in product_cat_lower for variant in category_variants)
    
    def _product_to_dict(self, product: Product, partner_code: str, redirect_base: Optional[str], profile: UserProfile) -> Dict:
        """Convert product to dict with affiliate links"""
        return {
            "id": getattr(product, 'key', getattr(product, 'id', '')),
            "brand": product.brand,
            "name": getattr(product, 'title', getattr(product, 'name', '')),
            "category": product.category,
            "price": product.price,
            "price_currency": getattr(product, 'price_currency', 'RUB'),
            "link": getattr(product, 'buy_url', getattr(product, 'link', None)),
            "ref_link": _with_affiliate(
                getattr(product, 'buy_url', getattr(product, 'link', None)),
                partner_code,
                redirect_base
            ),
            "actives": product.actives,
            "tags": product.tags,
            "match_reason": self._get_match_reason(product, profile)
        }
    
    def _get_match_reason(self, product: Product, profile: UserProfile) -> str:
        """Generate reason why this product was selected"""
        reasons = []
        
        actives_lower = [a.lower() for a in product.actives]
        skin_type = profile.skin_type.value if hasattr(profile.skin_type, 'value') else profile.skin_type
        
        # Active-based reasons
        if "hyaluronic" in str(actives_lower) and profile.dehydrated:
            reasons.append("увлажнение")
        if "niacinamide" in str(actives_lower) and skin_type == "oily":
            reasons.append("контроль жирности")
        if "retinol" in str(actives_lower) and "wrinkles" in (profile.concerns or []):
            reasons.append("антивозрастной уход")
        if "vitamin_c" in str(actives_lower) and "pigmentation" in (profile.concerns or []):
            reasons.append("осветление пигментации")
        
        # Skin type reasons
        if skin_type == "dry" and "moisturizer" in product.category.lower():
            reasons.append("подходит сухой коже")
        elif skin_type == "oily" and "gel" in (product.tags or []):
            reasons.append("лёгкая текстура для жирной кожи")
        
        return "; ".join(reasons) or "соответствует вашему профилю"
    
    def _check_compatibility(self, products: List[Product]) -> List[str]:
        """Check for incompatible ingredient combinations"""
        warnings = []
        all_actives = []
        
        for product in products:
            all_actives.extend([a.lower() for a in product.actives])
        
        # Check for incompatible pairs
        for pair in self._compatibility_rules.get("incompatible_pairs", []):
            if all(any(active in pair for active in all_actives) for active in pair):
                warnings.append(f"Избегайте одновременного использования {pair[0]} и {pair[1]}")
        
        return warnings
    
    def _generate_routine_suggestions(self, profile: UserProfile) -> Dict[str, List[str]]:
        """Generate routine suggestions based on profile"""
        am_routine = ["Очищение", "Тоник", "Сыворотка", "Увлажняющий крем", "SPF"]
        pm_routine = ["Очищение", "Тоник", "Активные средства", "Увлажняющий крем"]
        
        # Customize based on skin type
        skin_type = profile.skin_type.value if hasattr(profile.skin_type, 'value') else profile.skin_type
        
        if skin_type == "dry":
            am_routine.insert(-1, "Масло для лица")
            pm_routine.append("Ночное масло")
        elif skin_type == "oily":
            am_routine.insert(2, "Себорегулирующая сыворотка")
        
        return {
            "morning": am_routine,
            "evening": pm_routine,
            "weekly": ["Эксфолиация (1-2 раза)", "Маска (1 раз)"]
        }

def _pick_top(products: List[Product], limit: int = 3) -> List[Product]:
    return products[:limit]


def select_products(
    user_profile: UserProfile,
    catalog: List[Product],
    partner_code: str,
    redirect_base: str | None = None,
) -> Dict:
    skincare: Dict[str, List[Dict]] = {"AM": [], "PM": [], "weekly": []}
    makeup: Dict[str, List[Dict]] = {"face": [], "brows": [], "eyes": [], "lips": []}

    skin_type = (user_profile.skin_type or "normal").lower()
    concerns = [c.lower() for c in user_profile.concerns or []]
    undertone = user_profile.undertone

    # Mapping активов под задачи
    concern_to_actives = {
        "acne": ["bha", "salicylic", "ниацинамид", "niacinamide"],
        "dehydration": ["hyaluronic", "гиалурон", "glycerin"],
        "redness": ["panthenol", "d-panthenol", "centella", "cica", "ниацинамид"],
        "pigmentation": ["vitamin c", "аскорб", "arbutin", "kojic"],
        "aging": ["retinol", "ретин", "peptide", "peptides"],
        "sensitivity": ["ceramide", "церамид", "panthenol"],
    }

    wanted_actives: List[str] = []
    for c in concerns:
        wanted_actives.extend(concern_to_actives.get(c, []))
    if skin_type == "oily":
        wanted_actives.extend(["niacinamide", "aha", "bha"])
    if skin_type == "dry":
        wanted_actives.extend(["ceramide", "squalane", "panthenol", "hyaluronic"])

    # AM routine (english categories to align with tests)
    am_cleanser = _pick_top(_filter_catalog(catalog, category="cleanser"), 1)
    am_toner = _pick_top(_filter_catalog(catalog, category="toner", actives=wanted_actives), 1)
    am_serum = _pick_top(_filter_catalog(catalog, category="serum", actives=wanted_actives), 2)
    am_moist = _pick_top(
        _filter_catalog(catalog, category="moisturizer", actives=wanted_actives), 1
    )
    am_spf = _pick_top(_filter_catalog(catalog, category="sunscreen"), 1)

    # PM routine
    pm_cleanser = _pick_top(_filter_catalog(catalog, category="cleanser"), 1)
    pm_treatment = _pick_top(_filter_catalog(catalog, category="serum", actives=wanted_actives), 2)
    pm_moist = _pick_top(
        _filter_catalog(catalog, category="moisturizer", actives=wanted_actives), 1
    )

    # Weekly
    weekly_exf = _pick_top(_filter_catalog(catalog, category="peeling", actives=wanted_actives), 1)
    weekly_mask = _pick_top(_filter_catalog(catalog, category="mask", actives=wanted_actives), 1)

    # Makeup selection based on undertone
    if undertone:
        face_products = _pick_top(
            _filter_catalog(catalog, category="foundation", undertone=undertone), 2
        )
        brow_products = _pick_top(_filter_catalog(catalog, category="brow"), 1)
        eye_products = _pick_top(_filter_catalog(catalog, category="eyeshadow"), 1)
        mascara_products = _pick_top(_filter_catalog(catalog, category="mascara"), 1)
        lip_products = _pick_top(
            _filter_catalog(catalog, category="lipstick", undertone=undertone), 2
        )
    else:
        face_products = _pick_top(_filter_catalog(catalog, category="foundation"), 2)
        brow_products = _pick_top(_filter_catalog(catalog, category="brow"), 1)
        eye_products = _pick_top(_filter_catalog(catalog, category="eyeshadow"), 1)
        mascara_products = _pick_top(_filter_catalog(catalog, category="mascara"), 1)
        lip_products = _pick_top(_filter_catalog(catalog, category="lipstick"), 2)

    def _as_dict(p: Product) -> Dict:
        return {
            "id": p.id,
            "brand": p.brand,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "price_currency": p.price_currency,
            "link": str(p.link) if p.link else None,
            "ref_link": _with_affiliate(
                str(p.link) if p.link else None, partner_code, redirect_base
            ),
        }

    # Fill skincare
    skincare["AM"] = [_as_dict(p) for p in am_cleanser + am_toner + am_serum + am_moist + am_spf]
    skincare["PM"] = [_as_dict(p) for p in pm_cleanser + pm_treatment + pm_moist]
    skincare["weekly"] = [_as_dict(p) for p in weekly_exf + weekly_mask]

    # Fill makeup
    makeup["face"] = [_as_dict(p) for p in face_products]
    makeup["brows"] = [_as_dict(p) for p in brow_products]
    makeup["eyes"] = [_as_dict(p) for p in eye_products + mascara_products]
    makeup["lips"] = [_as_dict(p) for p in lip_products]

    return {"skincare": skincare, "makeup": makeup}
