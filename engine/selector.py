from __future__ import annotations

import urllib.parse
from typing import Dict, List, Optional
from .shade_normalization import get_shade_normalizer
from .explain_generator import get_explain_generator
from pathlib import Path
import yaml

from .models import Product, UserProfile


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
    """Original filter function - excludes OOS products"""
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


def _filter_catalog_with_fallback(
    catalog: List[Product],
    *,
    category: str | None = None,
    subcategory: str | None = None,
    tags: List[str] | None = None,
    actives: List[str] | None = None,
    finish: List[str] | None = None,
    undertone: str | None = None,
    target_shade: str | None = None,
    season: str | None = None,
    limit: int = 3,
) -> List[Product]:
    """Enhanced filter with OOS fallback logic"""

    # First try: exact match with in_stock products only
    in_stock_results = []
    all_matches = []

    normalizer = get_shade_normalizer()
    target_shade_info = normalizer.normalize_shade(target_shade) if target_shade else None

    for p in catalog:
        # Basic filters
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

        all_matches.append(p)
        if p.in_stock:
            in_stock_results.append(p)

    # If we have enough in-stock results, return them
    if len(in_stock_results) >= limit:
        return in_stock_results[:limit]

    # Fallback logic for OOS products
    result = in_stock_results.copy()

    if target_shade_info and target_shade_info.shade_id != "unknown":
        # Step 1: Try neighboring shades
        neighbors = normalizer.get_shade_neighbors(target_shade_info.shade_id)
        for neighbor_id in neighbors:
            if len(result) >= limit:
                break

            neighbor_products = [
                p
                for p in all_matches
                if p.in_stock and normalizer.normalize_shade(p.shade_name).shade_id == neighbor_id
            ]
            result.extend(neighbor_products)

        # Step 2: Try same category/finish alternatives
        if len(result) < limit:
            same_category = [
                p
                for p in all_matches
                if p.in_stock
                and (
                    not target_shade_info.depth
                    or normalizer.normalize_shade(p.shade_name).depth == target_shade_info.depth
                )
            ]
            result.extend(same_category)

        # Step 3: Try season universals
        if len(result) < limit and season:
            universals = normalizer.get_season_universals(season)
            for universal_id in universals:
                if len(result) >= limit:
                    break

                universal_products = [
                    p
                    for p in all_matches
                    if p.in_stock
                    and normalizer.normalize_shade(p.shade_name).shade_id == universal_id
                ]
                result.extend(universal_products)

    # Final fallback: any in-stock product from same category
    if len(result) < limit:
        remaining = [p for p in all_matches if p.in_stock and p not in result]
        result.extend(remaining)

    return result[:limit]


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
            "lip_liner": ["lip_liner", "карандаш_губы"],
        }

        self.skincare_categories = {
            "cleanser": ["cleanser", "очищение", "гель", "пенка"],
            "toner": ["toner", "тоник", "эксфолиант"],
            "serum": ["serum", "сыворотка", "концентрат"],
            "moisturizer": ["moisturizer", "крем", "эмульсия"],
            "eye_cream": ["eye_cream", "крем_глаз", "крем для глаз"],
            "sunscreen": ["sunscreen", "spf", "санскрин"],
            "mask": ["mask", "маска"],
        }

        # Season-specific makeup preferences
        self.season_preferences = {
            "spring": {
                "colors": ["coral", "peach", "bright pink", "warm beige", "golden"],
                "intensity": {"high": "bright", "medium": "moderate", "low": "subtle"},
                "finishes": ["dewy", "natural", "luminous"],
            },
            "summer": {
                "colors": ["berry", "plum", "dusty rose", "mauve", "soft pink"],
                "intensity": {"high": "muted bright", "medium": "medium", "low": "very soft"},
                "finishes": ["matte", "satin", "semi-matte"],
            },
            "autumn": {
                "colors": ["rust", "bronze", "deep orange", "warm brown", "golden"],
                "intensity": {"high": "rich", "medium": "warm", "low": "earthy"},
                "finishes": ["matte", "velvet", "semi-matte"],
            },
            "winter": {
                "colors": ["deep red", "burgundy", "cool pink", "icy blue", "silver"],
                "intensity": {"high": "dramatic", "medium": "bold", "low": "classic"},
                "finishes": ["matte", "metallic", "satin"],
            },
        }

        # Enhanced category priorities and rules
        self.category_rules = {
            "foundation": {"priority": 1, "required_match": ["undertone", "season"]},
            "concealer": {"priority": 2, "required_match": ["undertone"]},
            "corrector": {"priority": 3, "required_match": ["concerns"]},
            "powder": {"priority": 4, "required_match": ["skin_type"]},
            "blush": {"priority": 5, "required_match": ["season", "contrast"]},
            "bronzer": {"priority": 6, "required_match": ["season", "undertone"]},
            "contour": {"priority": 7, "required_match": ["contrast"]},
            "highlighter": {"priority": 8, "required_match": ["season", "contrast"]},
            "eyebrow": {"priority": 9, "required_match": ["hair_color"]},
            "mascara": {"priority": 10, "required_match": ["eye_color"]},
            "eyeshadow": {"priority": 11, "required_match": ["season", "eye_color", "contrast"]},
            "eyeliner": {"priority": 12, "required_match": ["eye_color", "contrast"]},
            "lipstick": {"priority": 13, "required_match": ["season", "undertone", "contrast"]},
            "lip_gloss": {"priority": 14, "required_match": ["season", "undertone"]},
            "lip_liner": {"priority": 15, "required_match": ["undertone"]},
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
                    ["benzoyl_peroxide", "retinol"],
                ]
            }

    def _get_skin_priorities(self, profile: UserProfile) -> List[str]:
        """Determine skincare priorities based on profile"""
        priorities = []

        skin_type = (
            profile.skin_type.value if hasattr(profile.skin_type, "value") else profile.skin_type
        )
        sensitivity = (
            profile.sensitivity.value
            if hasattr(profile.sensitivity, "value")
            else profile.sensitivity
        )

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

    def _get_season_makeup_intensity(self, season: str, contrast: str) -> str:
        """Get makeup intensity based on season and contrast"""
        season_prefs = self.season_preferences.get(season.lower(), {})
        intensities = season_prefs.get("intensity", {})
        return intensities.get(contrast.lower(), "medium")

    def _get_season_colors(self, season: str) -> List[str]:
        """Get recommended colors for season"""
        season_prefs = self.season_preferences.get(season.lower(), {})
        return season_prefs.get("colors", [])

    def _get_season_finishes(self, season: str) -> List[str]:
        """Get recommended finishes for season"""
        season_prefs = self.season_preferences.get(season.lower(), {})
        return season_prefs.get("finishes", ["natural"])

    def _select_by_category_rules(
        self, category: str, profile: UserProfile, products: List[Product]
    ) -> List[Product]:
        """Enhanced category-specific selection with season/contrast rules"""
        category_rule = self.category_rules.get(category, {})
        required_matches = category_rule.get("required_match", [])

        filtered_products = []
        season_colors = self._get_season_colors(profile.season) if profile.season else []
        self._get_season_finishes(profile.season) if profile.season else []

        for product in products:
            score = 0

            # Basic in-stock filter
            if not product.in_stock:
                continue

            # Season color matching
            if "season" in required_matches and profile.season:
                product_tags = [tag.lower() for tag in product.tags or []]
                if any(color.lower() in " ".join(product_tags) for color in season_colors):
                    score += 2
                elif category in ["foundation", "concealer"]:  # Always include base products
                    score += 1

            # Undertone matching
            if "undertone" in required_matches and profile.undertone:
                if hasattr(product, "undertone_match") and product.undertone_match:
                    if str(product.undertone_match).lower() == profile.undertone.lower():
                        score += 3
                    elif str(product.undertone_match).lower() == "neutral":
                        score += 1  # Neutral is generally compatible

            # Contrast matching (intensity)
            if "contrast" in required_matches and profile.contrast:
                intensity = self._get_season_makeup_intensity(
                    profile.season or "autumn", profile.contrast
                )
                product_tags = [tag.lower() for tag in product.tags or []]

                if intensity == "bright" and any(
                    tag in product_tags for tag in ["bright", "vibrant", "bold"]
                ):
                    score += 2
                elif intensity == "subtle" and any(
                    tag in product_tags for tag in ["subtle", "soft", "natural"]
                ):
                    score += 2
                elif intensity == "medium":
                    score += 1  # Medium works for most

            # Eye color matching for eye products
            if "eye_color" in required_matches and profile.eye_color:
                if category in ["eyeshadow", "eyeliner", "mascara"]:
                    eye_color = str(profile.eye_color).lower()
                    product_tags = [tag.lower() for tag in product.tags or []]

                    # Complementary color rules
                    complementary_map = {
                        "blue": ["bronze", "copper", "warm brown", "orange"],
                        "green": ["purple", "plum", "pink", "red"],
                        "brown": ["blue", "purple", "green", "gold"],
                        "hazel": ["purple", "green", "bronze", "gold"],
                        "gray": ["purple", "pink", "plum"],
                    }

                    if eye_color in complementary_map:
                        if any(
                            comp_color in " ".join(product_tags)
                            for comp_color in complementary_map[eye_color]
                        ):
                            score += 2

            # Skin type matching for base products
            if category in ["foundation", "powder", "primer"] and profile.skin_type:
                skin_type = str(profile.skin_type).lower()
                product_tags = [tag.lower() for tag in product.tags or []]

                if skin_type == "oily" and any(
                    tag in product_tags for tag in ["matte", "oil-free", "long-wear"]
                ):
                    score += 2
                elif skin_type == "dry" and any(
                    tag in product_tags for tag in ["dewy", "hydrating", "luminous"]
                ):
                    score += 2
                elif skin_type in ["combo", "normal"]:
                    score += 1  # Most products work

            if score > 0:
                filtered_products.append((product, score))

        # Sort by score and return top products
        filtered_products.sort(key=lambda x: x[1], reverse=True)
        return [product for product, score in filtered_products[:3]]

    def _get_color_preferences(self, profile: UserProfile) -> Dict[str, str]:
        """Get color preferences based on season and undertone"""
        prefs = {}

        season = profile.season.value if hasattr(profile.season, "value") else profile.season
        undertone = (
            profile.undertone.value if hasattr(profile.undertone, "value") else profile.undertone
        )

        # Season-based preferences
        season_prefs = {
            "spring": {"intensity": "bright", "temperature": "warm", "saturation": "clear"},
            "summer": {"intensity": "muted", "temperature": "cool", "saturation": "soft"},
            "autumn": {"intensity": "deep", "temperature": "warm", "saturation": "rich"},
            "winter": {"intensity": "bright", "temperature": "cool", "saturation": "clear"},
        }

        if season in season_prefs:
            prefs.update(season_prefs[season])

        # Undertone preferences
        if undertone:
            prefs["undertone"] = undertone

        return prefs

    def _match_product_to_profile(
        self, product: Product, profile: UserProfile, category: str
    ) -> float:
        """Calculate match score for product based on profile"""
        score = 0.0
        max_score = 1.0

        # Check actives compatibility
        actives_lower = [a.lower() for a in product.actives]

        # Skin type matching for skincare
        if category in self.skincare_categories:
            skin_type = (
                profile.skin_type.value
                if hasattr(profile.skin_type, "value")
                else profile.skin_type
            )

            if skin_type == "dry":
                if any(a in actives_lower for a in ["hyaluronic", "ceramide", "squalane"]):
                    score += 0.3
            elif skin_type == "oily":
                if any(a in actives_lower for a in ["niacinamide", "salicylic", "zinc"]):
                    score += 0.3

            # Concern matching
            concerns = profile.concerns or []
            if "acne" in concerns and any(
                a in actives_lower for a in ["salicylic", "niacinamide", "benzoyl"]
            ):
                score += 0.4
            if "pigmentation" in concerns and any(
                a in actives_lower for a in ["vitamin_c", "arbutin", "kojic"]
            ):
                score += 0.4
            if "wrinkles" in concerns and any(a in actives_lower for a in ["retinol", "peptide"]):
                score += 0.4

        # Color matching for makeup
        elif category in self.makeup_categories:
            color_prefs = self._get_color_preferences(profile)

            # Undertone matching
            if "undertone" in color_prefs and product.undertone_match:
                product_undertone = (
                    product.undertone_match.value
                    if hasattr(product.undertone_match, "value")
                    else product.undertone_match
                )
                if product_undertone == color_prefs["undertone"]:
                    score += 0.5

        # Sensitivity penalty
        if profile.sensitivity and (
            hasattr(profile.sensitivity, "value")
            and profile.sensitivity.value == "high"
            or profile.sensitivity == "high"
        ):
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
        redirect_base: Optional[str] = None,
    ) -> Dict:
        """Engine v2 product selection with enhanced logic"""

        # Separate makeup and skincare products
        skincare_products = [p for p in catalog if self._is_skincare_category(p.category)]
        makeup_products = [p for p in catalog if self._is_makeup_category(p.category)]

        # Generate skincare recommendations (7 categories)
        skincare_results = self._select_skincare_v2(
            profile, skincare_products, partner_code, redirect_base
        )

        # Generate makeup recommendations (15 categories)
        makeup_results = self._select_makeup_v2_enhanced(
            profile, makeup_products, partner_code, redirect_base
        )

        return {
            "skincare": skincare_results,
            "makeup": makeup_results,
            "compatibility_warnings": self._check_compatibility(skincare_products),
            "routine_suggestions": self._generate_routine_suggestions(profile),
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

    def _select_skincare_v2(
        self,
        profile: UserProfile,
        products: List[Product],
        partner_code: str,
        redirect_base: Optional[str],
    ) -> Dict:
        """Select skincare products across 7 categories"""
        results = {}

        # 7 skincare categories
        categories = ["cleanser", "toner", "serum", "moisturizer", "eye_cream", "sunscreen", "mask"]

        for category in categories:
            # Filter products for this category
            category_products = [
                p
                for p in products
                if self._matches_category(p.category, self.skincare_categories[category])
            ]

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
            results[category] = [
                self._product_to_dict(p, partner_code, redirect_base, profile) for p in top_products
            ]

        return results

    def _select_makeup_v2(
        self,
        profile: UserProfile,
        products: List[Product],
        partner_code: str,
        redirect_base: Optional[str],
    ) -> Dict:
        """Select makeup products across 15 categories"""
        results = {}

        # 15 makeup categories
        categories = list(self.makeup_categories.keys())

        for category in categories:
            # Filter products for this category
            category_products = [
                p
                for p in products
                if self._matches_category(p.category, self.makeup_categories[category])
            ]

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
            results[category] = [
                self._product_to_dict(p, partner_code, redirect_base, profile) for p in top_products
            ]

        return results

    def _matches_category(self, product_category: str, category_variants: List[str]) -> bool:
        """Check if product category matches any variant"""
        product_cat_lower = product_category.lower()
        return any(variant in product_cat_lower for variant in category_variants)

    def _product_to_dict(
        self,
        product: Product,
        partner_code: str,
        redirect_base: Optional[str],
        profile: UserProfile,
        is_fallback: bool = False,
        fallback_reason: Optional[str] = None,
    ) -> Dict:
        """Convert product to dict with affiliate links and explanation"""
        from engine.source_prioritizer import get_source_prioritizer

        explain_generator = get_explain_generator()
        source_prioritizer = get_source_prioritizer()

        # Get source prioritization info
        original_link = getattr(product, "buy_url", getattr(product, "link", None))
        source_info = source_prioritizer.get_source_info(original_link) if original_link else None

        return {
            "id": getattr(product, "key", getattr(product, "id", "")),
            "brand": product.brand,
            "name": getattr(product, "title", getattr(product, "name", "")),
            "category": product.category,
            "price": product.price,
            "price_currency": getattr(product, "price_currency", "RUB"),
            "link": original_link,
            "ref_link": _with_affiliate(original_link, partner_code, redirect_base),
            "actives": product.actives,
            "tags": product.tags,
            "in_stock": product.in_stock,
            "explain": explain_generator.generate_explain(
                product, profile, is_fallback, fallback_reason
            ),
            "match_reason": self._get_match_reason(product, profile),
            # NEW: Source prioritization info
            "source_priority": source_info.priority if source_info else 999,
            "source_name": source_info.name if source_info else "Неизвестный источник",
            "source_category": source_info.category if source_info else "unknown",
        }

    def _get_match_reason(self, product: Product, profile: UserProfile) -> str:
        """Generate reason why this product was selected"""
        reasons = []

        actives_lower = [a.lower() for a in product.actives]
        skin_type = (
            profile.skin_type.value if hasattr(profile.skin_type, "value") else profile.skin_type
        )

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

    def _select_makeup_v2_enhanced(
        self,
        profile: UserProfile,
        products: List[Product],
        partner_code: str,
        redirect_base: Optional[str],
    ) -> Dict:
        """Enhanced makeup selection with comprehensive category coverage"""
        makeup_results = {
            "base": [],  # foundation, concealer, corrector, powder
            "face": [],  # blush, bronzer, contour, highlighter
            "eyes": [],  # eyebrow, eyeshadow, eyeliner, mascara
            "lips": [],  # lipstick, lip_gloss, lip_liner
        }

        # Group categories by sections
        category_groups = {
            "base": ["foundation", "concealer", "corrector", "powder"],
            "face": ["blush", "bronzer", "contour", "highlighter"],
            "eyes": ["eyebrow", "eyeshadow", "eyeliner", "mascara"],
            "lips": ["lipstick", "lip_gloss", "lip_liner"],
        }

        for section, categories in category_groups.items():
            section_products = []

            for category in categories:
                # Use enhanced category-specific selection
                category_products = [
                    p
                    for p in products
                    if self._matches_category(
                        p.category, self.makeup_categories.get(category, [category])
                    )
                ]

                if category_products:
                    selected = self._select_by_category_rules(category, profile, category_products)

                    # Convert to dict format with enhanced info
                    for product in selected:
                        product_dict = self._product_to_dict(
                            product, partner_code, redirect_base, profile
                        )
                        product_dict["section"] = section
                        product_dict["category_priority"] = self.category_rules.get(
                            category, {}
                        ).get("priority", 99)
                        section_products.append(product_dict)

            # Sort by priority and limit per section
            section_products.sort(key=lambda x: x.get("category_priority", 99))
            makeup_results[section] = section_products[:5]  # Max 5 per section

        return makeup_results

    def _select_makeup_v2(
        self,
        profile: UserProfile,
        products: List[Product],
        partner_code: str,
        redirect_base: Optional[str],
    ) -> Dict:
        """Fallback to enhanced method"""
        return self._select_makeup_v2_enhanced(profile, products, partner_code, redirect_base)

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
        skin_type = (
            profile.skin_type.value if hasattr(profile.skin_type, "value") else profile.skin_type
        )

        if skin_type == "dry":
            am_routine.insert(-1, "Масло для лица")
            pm_routine.append("Ночное масло")
        elif skin_type == "oily":
            am_routine.insert(2, "Себорегулирующая сыворотка")

        return {
            "morning": am_routine,
            "evening": pm_routine,
            "weekly": ["Эксфолиация (1-2 раза)", "Маска (1 раз)"],
        }


def _pick_top(products: List[Product], limit: int = 3) -> List[Product]:
    """Pick top products with source prioritization"""
    if not products:
        return []

    from engine.source_prioritizer import get_source_prioritizer

    prioritizer = get_source_prioritizer()

    # Convert to dict format for prioritization
    product_dicts = []
    for p in products:
        product_dict = {
            "link": getattr(p, "buy_url", getattr(p, "link", None)),
            "product": p,  # Keep reference to original product
        }
        product_dicts.append(product_dict)

    # Sort by source priority
    sorted_dicts = prioritizer.sort_products_by_source_priority(product_dicts)

    # Extract original products and limit
    sorted_products = [pd["product"] for pd in sorted_dicts]
    return sorted_products[:limit]


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
        from engine.source_prioritizer import get_source_prioritizer

        explain_generator = get_explain_generator()
        source_prioritizer = get_source_prioritizer()

        # Get prioritized links for this product
        original_link = getattr(p, "buy_url", getattr(p, "link", None))
        source_info = source_prioritizer.get_source_info(original_link) if original_link else None

        return {
            "id": getattr(p, "key", getattr(p, "id", "")),
            "brand": p.brand,
            "name": getattr(p, "title", getattr(p, "name", "")),
            "category": p.category,
            "price": p.price,
            "price_currency": getattr(p, "price_currency", "RUB"),
            "link": original_link,
            "ref_link": _with_affiliate(original_link, partner_code, redirect_base),
            "in_stock": p.in_stock,
            "explain": explain_generator.generate_explain(p, user_profile),
            # NEW: Source prioritization info
            "source_priority": source_info.priority if source_info else 999,
            "source_name": source_info.name if source_info else "Неизвестный источник",
            "source_category": source_info.category if source_info else "unknown",
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
