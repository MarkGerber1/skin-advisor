from __future__ import annotations

import yaml
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .models import UserProfile, Product, Routine, ReportData, Undertone, Season, SkinType


class AnswerExpanderV2:
    """Engine v2 Answer Expander with TL;DR/FULL reports and rules application"""

    def __init__(self, rules_path: str = "deliverables/Engine_v2/RULES"):
        self.rules_path = Path(rules_path)
        self._compatibility_rules = self._load_compatibility_rules()
        self._layering_rules = self._load_layering_rules()
        self._cautions = self._load_cautions()

    def _load_compatibility_rules(self) -> Dict[str, Any]:
        """Load active ingredient compatibility matrix"""
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
                ],
                "avoid_with_sensitive": ["retinol", "aha", "bha", "fragrance"],
            }

    def _load_layering_rules(self) -> Dict[str, Any]:
        """Load product layering order rules"""
        try:
            with open(self.rules_path / "layering_order.yaml", "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {
                "morning_order": ["cleanser", "toner", "serum", "moisturizer", "spf"],
                "evening_order": ["cleanser", "toner", "treatment", "serum", "moisturizer", "oil"],
                "ph_order": ["low_ph_first", "water_based", "oil_based", "occlusive"],
            }

    def _load_cautions(self) -> Dict[str, Any]:
        """Load cautions and warnings"""
        try:
            with open(self.rules_path / "cautions.yaml", "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {
                "pregnancy_avoid": ["retinol", "retinoids", "high_salicylic_acid", "hydroquinone"],
                "sensitive_skin_avoid": ["fragrance", "essential_oils", "high_alcohol"],
                "sun_sensitivity": ["retinol", "aha", "bha", "vitamin_c"],
            }

    def generate_tldr_report(self, report_data: ReportData) -> str:
        """Generate TL;DR (short) report"""
        profile = report_data.user_profile

        # Color analysis
        color_summary = self._analyze_color_profile(profile)

        # Skin analysis
        skin_summary = self._analyze_skin_profile(profile)

        # Product count
        skincare_count = len(report_data.skincare_products)
        makeup_count = len(report_data.makeup_products)

        # Key warnings
        warnings = self._get_key_warnings(profile, report_data.skincare_products)

        tldr = f"""🎨 **ВАША ПАЛИТРА**: {color_summary}

🧴 **ТИП КОЖИ**: {skin_summary}

📦 **РЕКОМЕНДОВАНО**: 
• Уход: {skincare_count} средств
• Макияж: {makeup_count} средств

⚠️ **ВАЖНО**: {warnings if warnings else "Особых ограничений нет"}

💡 **ГЛАВНЫЙ СОВЕТ**: {self._get_main_tip(profile)}"""

        return tldr

    def generate_full_report(self, report_data: ReportData) -> str:
        """Generate FULL (detailed) report"""
        profile = report_data.user_profile

        sections = []

        # 1. Color profile analysis
        sections.append(self._generate_color_analysis(profile))

        # 2. Skin analysis
        sections.append(self._generate_skin_analysis(profile))

        # 3. Product recommendations with reasoning
        sections.append(self._generate_product_analysis(report_data))

        # 4. Routine suggestions
        sections.append(self._generate_routine_suggestions(report_data))

        # 5. Warnings and compatibility
        sections.append(self._generate_warnings_section(profile, report_data.skincare_products))

        # 6. Professional tips
        sections.append(self._generate_pro_tips(profile))

        return "\n\n".join(sections)

    def _analyze_color_profile(self, profile: UserProfile) -> str:
        """Analyze color profile for TL;DR"""
        if profile.season:
            season_name = (
                profile.season.value.title()
                if hasattr(profile.season, "value")
                else str(profile.season).title()
            )
            undertone_desc = ""
            if profile.undertone and profile.undertone != Undertone.UNKNOWN:
                undertone_desc = f" ({profile.undertone.value if hasattr(profile.undertone, 'value') else profile.undertone} подтон)"
            return f"{season_name}{undertone_desc}"
        elif profile.undertone and profile.undertone != Undertone.UNKNOWN:
            undertone_val = (
                profile.undertone.value
                if hasattr(profile.undertone, "value")
                else profile.undertone
            )
            return f"{undertone_val.title()} подтон"
        else:
            return "Индивидуальная палитра"

    def _analyze_skin_profile(self, profile: UserProfile) -> str:
        """Analyze skin profile for TL;DR"""
        skin_parts = []

        if profile.skin_type:
            skin_type = (
                profile.skin_type.value
                if hasattr(profile.skin_type, "value")
                else profile.skin_type
            )
            skin_parts.append(skin_type)

        if profile.dehydrated:
            skin_parts.append("обезвоженная")

        if profile.sensitivity:
            sens_val = (
                profile.sensitivity.value
                if hasattr(profile.sensitivity, "value")
                else profile.sensitivity
            )
            skin_parts.append(f"чувствительность {sens_val}")

        if profile.concerns:
            main_concern = profile.concerns[0] if profile.concerns else None
            if main_concern:
                concern_map = {
                    "acne": "акне",
                    "pigmentation": "пигментация",
                    "wrinkles": "возрастные изменения",
                    "redness": "покраснения",
                }
                concern_desc = concern_map.get(main_concern, main_concern)
                skin_parts.append(concern_desc)

        return ", ".join(skin_parts) or "Нормальная кожа"

    def _get_key_warnings(self, profile: UserProfile, products: List[Product]) -> str:
        """Get key warnings for TL;DR"""
        warnings = []

        # Pregnancy warnings
        if profile.pregnant_or_lactating:
            dangerous_actives = []
            for product in products:
                for active in product.actives:
                    if active.lower() in ["retinol", "retinoid", "salicylic"]:
                        dangerous_actives.append(active)
            if dangerous_actives:
                warnings.append("Избегайте ретиноидов и салициловой кислоты")

        # Sensitivity warnings
        if profile.sensitivity and (
            (hasattr(profile.sensitivity, "value") and profile.sensitivity.value == "high")
            or profile.sensitivity == "high"
        ):
            warnings.append("Начинайте с минимальных концентраций")

        # Sun protection
        has_photosensitizing = any(
            any(active.lower() in ["retinol", "aha", "bha"] for active in product.actives)
            for product in products
        )
        if has_photosensitizing:
            warnings.append("Обязательно используйте SPF")

        return "; ".join(warnings)

    def _get_main_tip(self, profile: UserProfile) -> str:
        """Get main tip based on profile"""
        skin_type_val = (
            profile.skin_type.value if hasattr(profile.skin_type, "value") else profile.skin_type
        )
        season_val = profile.season.value if hasattr(profile.season, "value") else profile.season

        if skin_type_val == "dry":
            return "Увлажнение — ваш приоритет номер один"
        elif skin_type_val == "oily":
            return "Контроль жирности без пересушивания кожи"
        elif profile.dehydrated:
            return "Восстановление гидробаланса кожи"
        elif "acne" in (profile.concerns or []):
            return "Мягкое очищение + точечное лечение"
        elif season_val == "spring":
            return "Яркие, чистые цвета подчеркнут вашу естественную красоту"
        elif season_val == "summer":
            return "Приглушённые, прохладные оттенки — ваша сила"
        elif season_val == "autumn":
            return "Тёплые, насыщенные цвета создадут гармоничный образ"
        elif season_val == "winter":
            return "Контрастные, чистые цвета — ваше преимущество"
        else:
            return "Индивидуальный подход с учётом особенностей вашей кожи"

    def _generate_color_analysis(self, profile: UserProfile) -> str:
        """Generate detailed color analysis"""
        analysis = "# 🎨 АНАЛИЗ ЦВЕТОТИПА\n\n"

        if profile.season:
            season_val = (
                profile.season.value if hasattr(profile.season, "value") else profile.season
            )
            season_descriptions = {
                "spring": "**Весна** — яркая, тёплая, лучистая. Вам подходят чистые, яркие цвета с тёплым подтоном.",
                "summer": "**Лето** — мягкая, прохладная, приглушённая. Ваши цвета — нежные, пыльные оттенки с холодным подтоном.",
                "autumn": "**Осень** — глубокая, тёплая, насыщенная. Вам к лицу богатые, землистые цвета с золотистым подтоном.",
                "winter": "**Зима** — яркая, холодная, контрастная. Ваши цвета — чистые, интенсивные с холодным подтоном.",
            }
            analysis += season_descriptions.get(season_val, "Индивидуальная цветовая палитра")

        if profile.undertone:
            undertone_val = (
                profile.undertone.value
                if hasattr(profile.undertone, "value")
                else profile.undertone
            )
            analysis += f"\n\n**Подтон кожи**: {undertone_val}"

        if profile.contrast:
            contrast_val = (
                profile.contrast.value if hasattr(profile.contrast, "value") else profile.contrast
            )
            analysis += f"\n**Контрастность**: {contrast_val}"

        if profile.eye_color:
            eye_val = (
                profile.eye_color.value
                if hasattr(profile.eye_color, "value")
                else profile.eye_color
            )
            analysis += f"\n**Цвет глаз**: {eye_val} — подчеркните комплементарными оттенками"

        return analysis

    def _generate_skin_analysis(self, profile: UserProfile) -> str:
        """Generate detailed skin analysis"""
        analysis = "# 🧴 АНАЛИЗ КОЖИ\n\n"

        if profile.fitzpatrick:
            fitz_val = (
                profile.fitzpatrick.value
                if hasattr(profile.fitzpatrick, "value")
                else profile.fitzpatrick
            )
            fitz_descriptions = {
                "I": "Очень светлая кожа, легко обгорает, практически не загорает",
                "II": "Светлая кожа, легко обгорает, слабо загорает",
                "III": "Светлая кожа, иногда обгорает, постепенно загорает",
                "IV": "Оливковая кожа, редко обгорает, хорошо загорает",
                "V": "Смуглая кожа, очень редко обгорает, легко загорает",
                "VI": "Очень смуглая кожа, практически не обгорает",
            }
            analysis += (
                f"**Фототип по Фицпатрику**: {fitz_val} — {fitz_descriptions.get(fitz_val, '')}\n\n"
            )

        if profile.baumann:
            analysis += f"**Тип кожи по Бауману**: {profile.baumann}\n"
            analysis += self._decode_baumann(profile.baumann) + "\n\n"

        if profile.skin_type:
            skin_val = (
                profile.skin_type.value
                if hasattr(profile.skin_type, "value")
                else profile.skin_type
            )
            analysis += f"**Базовый тип**: {skin_val}\n\n"

        if profile.concerns:
            analysis += f"**Основные проблемы**: {', '.join(profile.concerns)}\n\n"

        if profile.allergies:
            analysis += f"**Аллергии**: {', '.join(profile.allergies)}\n\n"

        return analysis

    def _decode_baumann(self, baumann: str) -> str:
        """Decode Baumann skin type"""
        if len(baumann) != 4:
            return ""

        o_d = "Жирная" if baumann[0] == "O" else "Сухая"
        s_r = "Чувствительная" if baumann[1] == "S" else "Устойчивая"
        p_n = "Пигментированная" if baumann[2] == "P" else "Не склонная к пигментации"
        w_t = "Склонная к морщинам" if baumann[3] == "W" else "Упругая"

        return f"{o_d}, {s_r.lower()}, {p_n.lower()}, {w_t.lower()}"

    def _generate_product_analysis(self, report_data: ReportData) -> str:
        """Generate product recommendations with reasoning"""
        analysis = "# 💎 РЕКОМЕНДОВАННЫЕ СРЕДСТВА\n\n"

        if report_data.skincare_products:
            analysis += "## Уходовая косметика\n\n"
            for product in report_data.skincare_products:
                analysis += f"**{product.brand} {product.title}**\n"
                analysis += f"*Категория*: {product.category}\n"
                if product.actives:
                    analysis += f"*Активные компоненты*: {', '.join(product.actives)}\n"
                analysis += f"*Обоснование*: {self._get_product_reasoning(product, report_data.user_profile)}\n\n"

        if report_data.makeup_products:
            analysis += "## Декоративная косметика\n\n"
            for product in report_data.makeup_products:
                analysis += f"**{product.brand} {product.title}**\n"
                analysis += f"*Категория*: {product.category}\n"
                if product.shade_name:
                    analysis += f"*Оттенок*: {product.shade_name}\n"
                analysis += f"*Обоснование*: {self._get_makeup_reasoning(product, report_data.user_profile)}\n\n"

        return analysis

    def _get_product_reasoning(self, product: Product, profile: UserProfile) -> str:
        """Get reasoning for skincare product recommendation"""
        reasons = []
        skin_type_val = (
            profile.skin_type.value if hasattr(profile.skin_type, "value") else profile.skin_type
        )

        # Match actives to concerns
        for active in product.actives:
            if "hyaluronic" in active.lower() and profile.dehydrated:
                reasons.append("гиалуроновая кислота для увлажнения")
            elif "niacinamide" in active.lower() and skin_type_val == "oily":
                reasons.append("ниацинамид для контроля жирности")
            elif "retinol" in active.lower() and "wrinkles" in (profile.concerns or []):
                reasons.append("ретинол для борьбы с возрастными изменениями")
            elif "vitamin_c" in active.lower() and "pigmentation" in (profile.concerns or []):
                reasons.append("витамин С против пигментации")

        # Match to skin type
        if skin_type_val == "dry" and "moisturizer" in product.category.lower():
            reasons.append("интенсивное увлажнение для сухой кожи")
        elif skin_type_val == "oily" and "cleanser" in product.category.lower():
            reasons.append("глубокое очищение для жирной кожи")

        return "; ".join(reasons) or "подходит вашему типу кожи"

    def _get_makeup_reasoning(self, product: Product, profile: UserProfile) -> str:
        """Get reasoning for makeup product recommendation"""
        reasons = []
        season_val = profile.season.value if hasattr(profile.season, "value") else profile.season
        undertone_val = (
            profile.undertone.value if hasattr(profile.undertone, "value") else profile.undertone
        )

        # Season matching
        if season_val == "spring" and "bright" in (product.tags or []):
            reasons.append("яркий оттенок для цветотипа Весна")
        elif season_val == "summer" and "muted" in (product.tags or []):
            reasons.append("приглушённый тон для цветотипа Лето")
        elif season_val == "autumn" and "warm" in (product.tags or []):
            reasons.append("тёплый оттенок для цветотипа Осень")
        elif season_val == "winter" and "cool" in (product.tags or []):
            reasons.append("холодный тон для цветотипа Зима")

        # Undertone matching
        product_undertone = (
            product.undertone_match.value
            if hasattr(product.undertone_match, "value")
            else product.undertone_match
        )
        if undertone_val == "warm" and product_undertone == "warm":
            reasons.append("соответствует тёплому подтону")
        elif undertone_val == "cool" and product_undertone == "cool":
            reasons.append("соответствует холодному подтону")

        return "; ".join(reasons) or "гармонирует с вашей палитрой"

    def _generate_routine_suggestions(self, report_data: ReportData) -> str:
        """Generate routine suggestions"""
        return "# ⏰ СХЕМА ПРИМЕНЕНИЯ\n\n**Утром**: Очищение → Тоник → Сыворотка → Увлажняющий крем → SPF\n\n**Вечером**: Очищение → Тоник → Активные средства → Увлажняющий крем"

    def _generate_warnings_section(self, profile: UserProfile, products: List[Product]) -> str:
        """Generate warnings and compatibility section"""
        warnings = []

        # Check for incompatible combinations
        actives_used = []
        for product in products:
            actives_used.extend(product.actives)

        for pair in self._compatibility_rules.get("incompatible_pairs", []):
            if all(any(active.lower() in pair for active in actives_used) for active in pair):
                warnings.append(f"⚠️ Не используйте {pair[0]} и {pair[1]} одновременно")

        if warnings:
            return "# ⚠️ ВАЖНЫЕ ПРЕДУПРЕЖДЕНИЯ\n\n" + "\n".join(warnings)
        else:
            return "# ✅ СОВМЕСТИМОСТЬ\n\nВсе рекомендованные средства совместимы между собой."

    def _generate_pro_tips(self, profile: UserProfile) -> str:
        """Generate professional tips"""
        tips = []

        sensitivity_val = (
            profile.sensitivity.value
            if hasattr(profile.sensitivity, "value")
            else profile.sensitivity
        )
        skin_type_val = (
            profile.skin_type.value if hasattr(profile.skin_type, "value") else profile.skin_type
        )
        season_val = profile.season.value if hasattr(profile.season, "value") else profile.season

        if sensitivity_val == "high":
            tips.append("🌟 Вводите новые средства по одному, тестируя реакцию")

        if skin_type_val == "combo":
            tips.append("🌟 Используйте разные средства для Т-зоны и щёк")

        if season_val == "spring":
            tips.append("🌟 Экспериментируйте с яркими цветами — они ваша сильная сторона")

        if tips:
            return "# 💡 СОВЕТЫ ВИЗАЖИСТА\n\n" + "\n".join(tips)
        else:
            return "# 💡 ОБЩИЕ РЕКОМЕНДАЦИИ\n\nСоблюдайте последовательность нанесения и не торопитесь с результатами."


# Legacy compatibility functions
def build_priorities(profile: Dict) -> List[str]:
    """Build priorities from profile - legacy function"""
    priorities: List[str] = []
    concerns = profile.get("concerns") or []
    if "barrier" in concerns or profile.get("dehydrated"):
        priorities.append("barrier_repair")
    if "acne" in concerns:
        priorities.append("acne_control")
    if "pigmentation" in concerns:
        priorities.append("even_tone")
    if "redness" in concerns:
        priorities.append("calming")
    if not priorities:
        priorities.append("balanced_routine")
    return priorities


def build_tldr_and_full(result_text: str) -> Tuple[str, str]:
    """Build TL;DR and full text - legacy function"""
    lines = [l for l in (result_text or "").splitlines() if l.strip()]
    tldr = "\n".join(lines[:8])
    full = result_text
    return tldr, full


def expand(profile: Dict, rendered_text: str, products: Dict) -> Dict:
    """Expand analysis with rules - legacy function"""
    priorities = build_priorities(profile)
    tl_dr, full = build_tldr_and_full(rendered_text)
    warnings: List[str] = []
    if profile.get("sensitivity") == "high":
        warnings.append("introduce_slowly")
    if "texture" in (profile.get("concerns") or []):
        warnings.append("photosensitivity_acids")
    return {
        "profile": profile,
        "priorities": priorities,
        "routines": {},
        "compatibility": {},
        "products": products,
        "warnings": warnings,
        "tl_dr": tl_dr,
        "full_text": full,
    }
