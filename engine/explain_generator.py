"""
💡 Explain Generator for Product Cards
Generates contextual explanations for why products are recommended
"""

from typing import List, Optional
from .models import Product, UserProfile


class ExplainGenerator:
    """Generates personalized explanations for product recommendations"""

    def __init__(self):
        self.undertone_explanations = {
            "warm": {
                "foundation": "теплый подтон",
                "lipstick": "теплые оттенки",
                "eyeshadow": "золотистые тона",
            },
            "cool": {
                "foundation": "холодный подтон",
                "lipstick": "розовые тона",
                "eyeshadow": "серебристые оттенки",
            },
            "neutral": {
                "foundation": "нейтральный подтон",
                "lipstick": "универсальные оттенки",
                "eyeshadow": "сбалансированные тона",
            },
        }

        self.season_explanations = {
            "spring": {"makeup": "яркие, свежие тона", "skincare": "легкие текстуры"},
            "summer": {"makeup": "мягкие, прохладные оттенки", "skincare": "увлажняющие формулы"},
            "autumn": {"makeup": "глубокие, теплые цвета", "skincare": "питательные средства"},
            "winter": {
                "makeup": "контрастные, яркие оттенки",
                "skincare": "восстанавливающие формулы",
            },
        }

        self.contrast_explanations = {
            "low": "мягкие переходы",
            "medium": "сбалансированная интенсивность",
            "high": "яркие, контрастные оттенки",
        }

        self.concern_explanations = {
            "acne": "борьба с воспалениями",
            "dehydration": "глубокое увлажнение",
            "redness": "успокаивание кожи",
            "pigmentation": "выравнивание тона",
            "aging": "омоложение",
            "sensitivity": "деликатный уход",
            "oily": "контроль жирности",
            "dry": "интенсивное питание",
        }

    def generate_explain(
        self,
        product: Product,
        profile: UserProfile,
        is_fallback: bool = False,
        fallback_reason: Optional[str] = None,
    ) -> str:
        """Generate explanation for why this product suits the user"""

        explanations = []

        # Fallback explanation
        if is_fallback and fallback_reason:
            explanations.append(f"Аналог ({fallback_reason})")

        # Undertone match for makeup
        if self._is_makeup_category(product.category) and profile.undertone:
            undertone_key = profile.undertone.lower()
            category_key = self._get_category_key(product.category)

            if undertone_key in self.undertone_explanations:
                undertone_match = self.undertone_explanations[undertone_key].get(
                    category_key, "подходящий подтон"
                )
                explanations.append(undertone_match)

        # Season match
        if profile.season:
            season_key = profile.season.lower()
            product_type = "makeup" if self._is_makeup_category(product.category) else "skincare"

            if season_key in self.season_explanations:
                season_match = self.season_explanations[season_key].get(
                    product_type, "сезонный выбор"
                )
                explanations.append(season_match)

        # Contrast match for makeup
        if self._is_makeup_category(product.category) and profile.contrast:
            contrast_key = profile.contrast.lower()
            if contrast_key in self.contrast_explanations:
                explanations.append(self.contrast_explanations[contrast_key])

        # Concern-based explanations for skincare
        if self._is_skincare_category(product.category) and profile.concerns:
            concern_matches = []
            product_actives = [a.lower() for a in product.actives or []]

            for concern in profile.concerns[:2]:  # Top 2 concerns
                concern_key = concern.lower()
                if concern_key in self.concern_explanations:
                    # Check if product addresses this concern
                    if self._product_addresses_concern(product_actives, concern_key):
                        concern_matches.append(self.concern_explanations[concern_key])

            explanations.extend(concern_matches)

        # Skin type match for skincare
        if self._is_skincare_category(product.category) and profile.skin_type:
            skin_type = profile.skin_type.lower()
            if skin_type in self.concern_explanations:
                if self._product_addresses_concern(
                    [a.lower() for a in product.actives or []], skin_type
                ):
                    explanations.append(self.concern_explanations[skin_type])

        # Sensitivity consideration
        if profile.sensitivity and hasattr(profile.sensitivity, "value"):
            sensitivity = profile.sensitivity.value.lower()
        else:
            sensitivity = str(profile.sensitivity).lower() if profile.sensitivity else None

        if sensitivity == "high":
            product_actives = [a.lower() for a in product.actives or []]
            gentle_indicators = ["panthenol", "ceramide", "hyaluronic", "aloe"]

            if any(gentle in " ".join(product_actives) for gentle in gentle_indicators):
                explanations.append("деликатная формула")

        # Pregnancy safety
        if profile.pregnant_or_lactating:
            unsafe_actives = ["retinol", "retinoid", "salicylic", "hydroquinone"]
            product_actives = [a.lower() for a in product.actives or []]

            if not any(unsafe in " ".join(product_actives) for unsafe in unsafe_actives):
                explanations.append("безопасно при беременности")

        # Default explanation if none found
        if not explanations:
            if self._is_makeup_category(product.category):
                explanations.append("подходит вашему типу")
            else:
                explanations.append("рекомендовано для вашей кожи")

        # Format final explanation
        result = "Подойдет: " + ", ".join(explanations[:3])  # Limit to 3 reasons
        return result if len(result) <= 120 else result[:117] + "..."

    def _is_makeup_category(self, category: str) -> bool:
        """Check if category is makeup"""
        makeup_categories = [
            "foundation",
            "concealer",
            "corrector",
            "powder",
            "blush",
            "bronzer",
            "contour",
            "highlighter",
            "eyebrow",
            "mascara",
            "eyeshadow",
            "eyeliner",
            "lipstick",
            "lip_gloss",
            "lip_liner",
            "bb_cream",
            "cc_cream",
        ]
        return category.lower() in makeup_categories

    def _is_skincare_category(self, category: str) -> bool:
        """Check if category is skincare"""
        skincare_categories = [
            "cleanser",
            "toner",
            "serum",
            "moisturizer",
            "eye_cream",
            "sunscreen",
            "mask",
            "peeling",
            "essence",
            "emulsion",
        ]
        return category.lower() in skincare_categories

    def _get_category_key(self, category: str) -> str:
        """Map product category to explanation key"""
        category_mapping = {
            "foundation": "foundation",
            "bb_cream": "foundation",
            "cc_cream": "foundation",
            "concealer": "foundation",
            "lipstick": "lipstick",
            "lip_gloss": "lipstick",
            "eyeshadow": "eyeshadow",
            "eyeliner": "eyeshadow",
        }
        return category_mapping.get(category.lower(), "foundation")

    def _product_addresses_concern(self, product_actives: List[str], concern: str) -> bool:
        """Check if product actives address specific concern"""
        concern_actives = {
            "acne": ["salicylic", "bha", "niacinamide", "retinol", "benzoyl peroxide"],
            "dehydration": ["hyaluronic", "glycerin", "squalane", "ceramide"],
            "redness": ["panthenol", "centella", "cica", "niacinamide", "azelaic"],
            "pigmentation": ["vitamin c", "arbutin", "kojic", "retinol", "hydroquinone"],
            "aging": ["retinol", "peptide", "vitamin c", "aha", "bakuchiol"],
            "sensitivity": ["panthenol", "ceramide", "aloe", "oat", "chamomile"],
            "oily": ["niacinamide", "bha", "salicylic", "retinol", "zinc"],
            "dry": ["ceramide", "squalane", "hyaluronic", "shea butter", "glycerin"],
        }

        if concern not in concern_actives:
            return False

        concern_keywords = concern_actives[concern]
        actives_text = " ".join(product_actives)

        return any(keyword in actives_text for keyword in concern_keywords)


# Global instance
_explain_generator = None


def get_explain_generator() -> ExplainGenerator:
    """Get global explain generator instance"""
    global _explain_generator
    if _explain_generator is None:
        _explain_generator = ExplainGenerator()
    return _explain_generator


if __name__ == "__main__":
    # Test the explain generator
    from .models import UserProfile, Product

    generator = ExplainGenerator()

    # Test profile
    profile = UserProfile(
        undertone="warm",
        season="autumn",
        contrast="medium",
        skin_type="dry",
        concerns=["aging", "dehydration"],
    )

    # Test products
    foundation = Product(
        key="test_foundation",
        title="Test Foundation",
        brand="Test Brand",
        category="foundation",
        in_stock=True,
        shade_name="medium warm",
    )

    serum = Product(
        key="test_serum",
        title="Test Serum",
        brand="Test Brand",
        category="serum",
        in_stock=True,
        actives=["hyaluronic acid", "vitamin c"],
    )

    # Generate explanations
    foundation_explain = generator.generate_explain(foundation, profile)
    serum_explain = generator.generate_explain(serum, profile)

    print(f"Foundation: {foundation_explain}")
    print(f"Serum: {serum_explain}")

    # Test fallback explanation
    fallback_explain = generator.generate_explain(
        foundation, profile, is_fallback=True, fallback_reason="соседний оттенок"
    )
    print(f"Fallback: {fallback_explain}")
