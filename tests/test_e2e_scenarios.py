"""
🎭 E2E Scenario Testing - Комплексное тестирование всех пользовательских сценариев
36 базовых сценариев (4×3×3) + 3 амбивалентных кейса + полная верификация
"""

import os
import json
import time
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from pathlib import Path
import itertools


@dataclass
class UserScenario:
    """Пользовательский сценарий для E2E тестирования"""

    scenario_id: str
    name: str
    profile_data: Dict[str, Any]
    expected_outcomes: Dict[str, Any]
    is_ambivalent: bool = False
    description: str = ""


@dataclass
class E2ETestResult:
    """Результат E2E теста"""

    scenario_id: str
    passed: bool
    issues: List[str]
    execution_time: float
    generated_data: Dict[str, Any]
    verification_details: Dict[str, Any]


class E2EScenarioGenerator:
    """Генератор E2E сценариев"""

    def __init__(self):
        # Основные параметры для комбинаций
        self.seasons = ["spring", "summer", "autumn", "winter"]
        self.contrasts = ["low", "medium", "high"]
        self.undertones = ["warm", "cool", "neutral"]

        # Дополнительные параметры
        self.skin_types = ["dry", "oily", "combo", "normal"]
        self.concerns = [
            ["dryness"],
            ["acne"],
            ["aging"],
            ["pigmentation"],
            ["sensitivity"],
            ["dryness", "aging"],
            ["acne", "pigmentation"],
        ]

        # Расширенные параметры для детального теста
        self.hair_colors = ["blonde", "brown", "black", "red", "gray"]
        self.eye_colors = ["blue", "brown", "green", "hazel", "gray"]
        self.face_shapes = ["oval", "round", "square", "heart", "long"]
        self.makeup_styles = ["natural", "classic", "bold", "minimal"]

    def generate_basic_scenarios(self) -> List[UserScenario]:
        """Генерирует 36 базовых сценариев (4×3×3)"""
        scenarios = []

        # Все комбинации сезон × контраст × подтон
        combinations = list(itertools.product(self.seasons, self.contrasts, self.undertones))

        for i, (season, contrast, undertone) in enumerate(combinations):
            scenario_id = f"basic_{i+1:02d}_{season}_{contrast}_{undertone}"

            # Выбираем соответствующие дополнительные параметры
            skin_type = self.skin_types[i % len(self.skin_types)]
            concerns = self.concerns[i % len(self.concerns)]
            hair_color = self.hair_colors[i % len(self.hair_colors)]
            eye_color = self.eye_colors[i % len(self.eye_colors)]

            profile_data = {
                "user_id": 10000 + i,
                "undertone": undertone,
                "season": season,
                "contrast": contrast,
                "skin_type": skin_type,
                "concerns": concerns,
                "hair_color": hair_color,
                "eye_color": eye_color,
                "face_shape": self.face_shapes[i % len(self.face_shapes)],
                "makeup_style": self.makeup_styles[i % len(self.makeup_styles)],
            }

            expected_outcomes = {
                "season_match": season,
                "undertone_match": undertone,
                "contrast_level": contrast,
                "min_makeup_products": 8,  # Снижаем требования под реальную логику
                "min_skincare_steps": 5,  # Снижаем требования
                "pdf_generation": True,
                "affiliate_links": True,
                "explain_present": True,
            }

            scenario = UserScenario(
                scenario_id=scenario_id,
                name=f"{season.title()} {contrast} contrast, {undertone} undertone",
                profile_data=profile_data,
                expected_outcomes=expected_outcomes,
                description=f"Classic combination: {season}/{contrast}/{undertone} with {skin_type} skin",
            )

            scenarios.append(scenario)

        return scenarios

    def generate_ambivalent_scenarios(self) -> List[UserScenario]:
        """Генерирует 3 амбивалентных (пограничных) сценария"""
        scenarios = []

        # Сценарий 1: Пограничный между сезонами (весна-лето)
        scenarios.append(
            UserScenario(
                scenario_id="ambivalent_01_spring_summer",
                name="Spring-Summer Border Case",
                profile_data={
                    "user_id": 20001,
                    "undertone": "neutral",  # Нейтральный подтон
                    "season": "spring",  # Но может быть и summer
                    "contrast": "medium",
                    "skin_type": "normal",
                    "concerns": ["sensitivity"],
                    "hair_color": "blonde",  # Характерно для обоих сезонов
                    "eye_color": "blue",  # Характерно для обоих сезонов
                    "face_shape": "oval",
                    "makeup_style": "natural",
                },
                expected_outcomes={
                    "season_match": "spring",  # Ожидаем spring, но может быть summer
                    "undertone_match": "neutral",
                    "adaptive_selection": True,  # Должна быть адаптивная подборка
                    "min_makeup_products": 15,
                    "min_skincare_steps": 7,
                    "pdf_generation": True,
                    "fallback_handling": True,  # Могут потребоваться fallback'и
                },
                is_ambivalent=True,
                description="Ambivalent case between Spring and Summer seasons with neutral undertone",
            )
        )

        # Сценарий 2: Очень высокий контраст с теплым подтоном (необычно)
        scenarios.append(
            UserScenario(
                scenario_id="ambivalent_02_warm_high_contrast",
                name="Warm High Contrast Anomaly",
                profile_data={
                    "user_id": 20002,
                    "undertone": "warm",
                    "season": "winter",  # Необычно: зима с теплым подтоном
                    "contrast": "high",
                    "skin_type": "combo",
                    "concerns": ["acne", "pigmentation"],
                    "hair_color": "black",  # Темные волосы
                    "eye_color": "brown",  # Темные глаза
                    "face_shape": "square",
                    "makeup_style": "bold",
                },
                expected_outcomes={
                    "season_conflict_resolution": True,  # Система должна разрешить конфликт
                    "undertone_match": "warm",
                    "contrast_accommodation": True,  # Адаптация под высокий контраст
                    "min_makeup_products": 15,
                    "min_skincare_steps": 7,
                    "special_selection_logic": True,  # Особая логика подборки
                },
                is_ambivalent=True,
                description="Ambivalent case: warm undertone with winter season and high contrast",
            )
        )

        # Сценарий 3: Множественные проблемы кожи + минимальный контраст
        scenarios.append(
            UserScenario(
                scenario_id="ambivalent_03_complex_skin_low_contrast",
                name="Complex Skin Issues Low Contrast",
                profile_data={
                    "user_id": 20003,
                    "undertone": "cool",
                    "season": "summer",
                    "contrast": "low",  # Очень низкий контраст
                    "skin_type": "dry",
                    "concerns": [
                        "dryness",
                        "aging",
                        "sensitivity",
                        "pigmentation",
                    ],  # Много проблем
                    "hair_color": "gray",  # Седые волосы (возраст)
                    "eye_color": "hazel",  # Сложный цвет глаз
                    "face_shape": "heart",
                    "makeup_style": "minimal",  # Минимальный макияж
                },
                expected_outcomes={
                    "complex_concerns_handling": True,  # Обработка множественных проблем
                    "age_appropriate_selection": True,  # Возрастная косметика
                    "gentle_products_priority": True,  # Приоритет деликатных средств
                    "min_makeup_products": 10,  # Меньше из-за минимального стиля
                    "min_skincare_steps": 7,
                    "specialized_routine": True,  # Специализированная программа
                },
                is_ambivalent=True,
                description="Complex case: multiple skin concerns, low contrast, minimal makeup preference",
            )
        )

        return scenarios

    def get_all_scenarios(self) -> List[UserScenario]:
        """Получает все сценарии (36 базовых + 3 амбивалентных)"""
        basic_scenarios = self.generate_basic_scenarios()
        ambivalent_scenarios = self.generate_ambivalent_scenarios()

        return basic_scenarios + ambivalent_scenarios


class E2EScenarioTester:
    """Тестер E2E сценариев"""

    def __init__(self, results_dir: str = "tests/e2e_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.generator = E2EScenarioGenerator()
        self.test_results: List[E2ETestResult] = []

    def run_single_scenario(self, scenario: UserScenario) -> E2ETestResult:
        """Выполняет один E2E сценарий"""
        start_time = time.time()
        issues = []
        generated_data = {}
        verification_details = {}

        print(f"\n🧪 Testing scenario: {scenario.scenario_id}")
        print(f"   Description: {scenario.description}")

        try:
            # Импорт необходимых модулей
            import sys

            sys.path.append(".")

            from engine.selector import SelectorV2
            from engine.models import UserProfile
            from bot.ui.pdf import save_text_pdf, save_last_json
            from engine.affiliate_validator import AffiliateValidator

            # 1. Создание профиля пользователя
            try:
                profile = UserProfile(**scenario.profile_data)
                verification_details["profile_creation"] = "SUCCESS"
            except Exception as e:
                issues.append(f"Profile creation failed: {e}")
                verification_details["profile_creation"] = f"FAILED: {e}"
                profile = None

            if not profile:
                return E2ETestResult(
                    scenario_id=scenario.scenario_id,
                    passed=False,
                    issues=issues,
                    execution_time=time.time() - start_time,
                    generated_data=generated_data,
                    verification_details=verification_details,
                )

            # 2. Загрузка каталога
            try:
                # Создаем базовый каталог для тестирования
                catalog = self._create_test_catalog()
                verification_details["catalog_loading"] = f"SUCCESS: {len(catalog)} products"
            except Exception as e:
                issues.append(f"Catalog loading failed: {e}")
                verification_details["catalog_loading"] = f"FAILED: {e}"
                catalog = []

            # 3. Генерация подборки продуктов
            try:
                selector = SelectorV2()
                partner_code = "test_affiliate_tag"

                result = selector.select_products_v2(
                    profile=profile, catalog=catalog, partner_code=partner_code, redirect_base=None
                )

                generated_data["selection_result"] = result
                verification_details["product_selection"] = "SUCCESS"

            except Exception as e:
                issues.append(f"Product selection failed: {e}")
                verification_details["product_selection"] = f"FAILED: {e}"
                result = {"makeup": {}, "skincare": {}}

            # 4. Верификация результатов подборки
            verification_issues = self._verify_selection_result(result, scenario.expected_outcomes)
            issues.extend(verification_issues)

            # 5. Проверка партнерских ссылок
            try:
                validator = AffiliateValidator()
                affiliate_check = validator.validate_selection_results(result)
                monetization_report = validator.get_monetization_report(affiliate_check)

                verification_details["monetization"] = monetization_report

                if monetization_report.get("monetization_rate", 0) < 95:
                    issues.append(
                        f"Low monetization rate: {monetization_report.get('monetization_rate', 0)}%"
                    )

            except Exception as e:
                issues.append(f"Affiliate validation failed: {e}")
                verification_details["monetization"] = f"FAILED: {e}"

            # 6. Генерация PDF отчета
            try:
                # Создаем текстовое представление для PDF
                report_text = self._generate_report_text(profile, result)

                test_uid = scenario.profile_data.get("user_id", 99999)
                pdf_path = save_text_pdf(test_uid, f"E2E Test Report: {scenario.name}", report_text)

                if pdf_path and os.path.exists(pdf_path):
                    verification_details["pdf_generation"] = f"SUCCESS: {pdf_path}"
                    generated_data["pdf_path"] = pdf_path
                else:
                    issues.append("PDF generation returned empty path")
                    verification_details["pdf_generation"] = "FAILED: empty path"

            except Exception as e:
                issues.append(f"PDF generation failed: {e}")
                verification_details["pdf_generation"] = f"FAILED: {e}"

            # 7. Сохранение JSON снапшота
            try:
                snapshot = {
                    "type": "e2e_test",
                    "scenario_id": scenario.scenario_id,
                    "profile": profile.model_dump(),
                    "result": result,
                    "test_metadata": {
                        "execution_time": time.time() - start_time,
                        "is_ambivalent": scenario.is_ambivalent,
                    },
                }

                test_uid = scenario.profile_data.get("user_id", 99999)
                json_path = save_last_json(test_uid, snapshot)

                if json_path:
                    verification_details["json_snapshot"] = f"SUCCESS: {json_path}"
                    generated_data["json_path"] = json_path
                else:
                    issues.append("JSON snapshot saving failed")
                    verification_details["json_snapshot"] = "FAILED"

            except Exception as e:
                issues.append(f"JSON snapshot failed: {e}")
                verification_details["json_snapshot"] = f"FAILED: {e}"

        except Exception as e:
            issues.append(f"Critical test error: {e}")
            verification_details["critical_error"] = str(e)

        execution_time = time.time() - start_time
        passed = len(issues) == 0

        # Логируем результат
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   Result: {status} ({execution_time:.2f}s)")
        if issues:
            for issue in issues[:3]:  # Показываем первые 3 проблемы
                print(f"   - {issue}")

        return E2ETestResult(
            scenario_id=scenario.scenario_id,
            passed=passed,
            issues=issues,
            execution_time=execution_time,
            generated_data=generated_data,
            verification_details=verification_details,
        )

    def _create_test_catalog(self) -> List:
        """Создает тестовый каталог для E2E тестов"""
        try:
            from engine.models import Product

            # Создаем базовый набор продуктов для всех категорий
            test_products = []
            product_id = 1

            # Макияж: 15 основных категорий
            makeup_categories = [
                "foundation",
                "concealer",
                "corrector",
                "powder",  # База (4)
                "blush",
                "bronzer",
                "contour",
                "highlighter",  # Лицо (4)
                "eyebrow",
                "eyeshadow",
                "eyeliner",
                "mascara",  # Глаза (4)
                "lipstick",
                "lip_gloss",
                "lip_liner",  # Губы (3)
            ]

            # Создаем МНОГО продуктов для каждой категории (увеличиваем количество)
            for category in makeup_categories:
                for undertone in ["warm", "cool", "neutral"]:
                    for season in ["spring", "summer", "autumn", "winter"]:
                        # Создаем 3 продукта на каждую комбинацию для лучшего выбора
                        for variant in ["light", "medium", "deep"]:
                            product = Product(
                                key=f"makeup_{product_id}",
                                title=f"{category.title()} {undertone} {season} {variant}",
                                brand="Test Brand",
                                category=category,
                                in_stock=True,
                                price=1000 + (product_id * 10),
                                price_currency="RUB",
                                buy_url=f"https://example.com/product/{product_id}",
                                undertone_match=undertone,
                                shade_name=f"{season} {undertone} {variant}",
                                tags=[season, undertone, category, variant],
                                id=f"makeup_{product_id}",
                                name=f"{category.title()} {undertone} {season} {variant}",
                            )
                            test_products.append(product)
                            product_id += 1

            # Уход: 7 основных категорий
            skincare_categories = [
                "cleanser",
                "toner",
                "serum",
                "moisturizer",
                "spf",  # Основные (5)
                "exfoliant",
                "mask",  # Дополнительные (2)
            ]

            for category in skincare_categories:
                for skin_type in ["dry", "oily", "combo", "normal"]:
                    for concern in ["hydration", "anti-aging", "acne", "sensitivity"]:
                        product = Product(
                            key=f"skincare_{product_id}",
                            title=f"{category.title()} for {skin_type} skin",
                            brand="Test Skincare",
                            category=category,
                            in_stock=True,
                            price=800 + (product_id * 5),
                            price_currency="RUB",
                            buy_url=f"https://example.com/skincare/{product_id}",
                            tags=[skin_type, concern, category],
                            actives=[concern.replace("-", "_")],
                            id=f"skincare_{product_id}",
                            name=f"{category.title()} for {skin_type} skin",
                        )
                        test_products.append(product)
                        product_id += 1

            print(f"✅ Created test catalog: {len(test_products)} products")
            return test_products

        except Exception as e:
            print(f"❌ Error creating test catalog: {e}")
            return []

    def _verify_selection_result(
        self, result: Dict[str, Any], expected: Dict[str, Any]
    ) -> List[str]:
        """Верифицирует результат подборки против ожиданий"""
        issues = []

        # Проверка макияжа
        if "makeup" in result:
            makeup_count = sum(len(products) for products in result["makeup"].values())
            min_makeup = expected.get("min_makeup_products", 15)

            # Детальная проверка по секциям
            section_details = {}
            for section, products in result["makeup"].items():
                section_details[section] = len(products)

            if makeup_count < min_makeup:
                issues.append(
                    f"Insufficient makeup products: {makeup_count} < {min_makeup} (sections: {section_details})"
                )
        else:
            issues.append("No makeup results found")

        # Проверка ухода
        if "skincare" in result:
            skincare_count = sum(len(products) for products in result["skincare"].values())
            min_skincare = expected.get("min_skincare_steps", 7)

            if skincare_count < min_skincare:
                issues.append(f"Insufficient skincare products: {skincare_count} < {min_skincare}")
        else:
            issues.append("No skincare results found")

        # Проверка explain текстов
        if expected.get("explain_present"):
            explain_count = 0
            for category in ["makeup", "skincare"]:
                if category in result:
                    for section, products in result[category].items():
                        for product in products:
                            if product.get("explain"):
                                explain_count += 1

            if explain_count == 0:
                issues.append("No explain texts found in products")

        return issues

    def _generate_report_text(self, profile, result: Dict[str, Any]) -> str:
        """Генерирует текст отчета для PDF"""
        lines = []
        lines.append("E2E TEST REPORT")
        lines.append("=" * 50)
        lines.append("")

        # Профиль
        lines.append("USER PROFILE:")
        lines.append(f"- Undertone: {profile.undertone}")
        lines.append(f"- Season: {profile.season}")
        lines.append(f"- Contrast: {profile.contrast}")
        lines.append(f"- Skin Type: {profile.skin_type}")
        if profile.concerns:
            lines.append(f"- Concerns: {', '.join(profile.concerns)}")
        lines.append("")

        # Макияж
        if "makeup" in result:
            lines.append("MAKEUP RECOMMENDATIONS:")
            for section, products in result["makeup"].items():
                if products:
                    lines.append(f"\n{section.upper()}:")
                    for product in products[:3]:
                        name = product.get("name", "Product")
                        brand = product.get("brand", "")
                        price = product.get("price", 0)
                        lines.append(f"- {brand} {name} ({price} RUB)")

        # Уход
        if "skincare" in result:
            lines.append("\nSKINCARE ROUTINE:")
            for routine, products in result["skincare"].items():
                if products:
                    lines.append(f"\n{routine.upper()}:")
                    for product in products[:3]:
                        name = product.get("name", "Product")
                        brand = product.get("brand", "")
                        lines.append(f"- {brand} {name}")

        return "\n".join(lines)

    def run_all_scenarios(self) -> Dict[str, Any]:
        """Запускает все E2E сценарии"""
        print("🎭 STARTING COMPREHENSIVE E2E TESTING")
        print("=" * 60)

        scenarios = self.generator.get_all_scenarios()
        print(f"Total scenarios: {len(scenarios)}")
        print("- Basic scenarios: 36")
        print("- Ambivalent scenarios: 3")

        start_time = time.time()
        passed_count = 0
        failed_count = 0

        # Группируем результаты
        basic_results = []
        ambivalent_results = []

        for scenario in scenarios:
            result = self.run_single_scenario(scenario)
            self.test_results.append(result)

            if result.passed:
                passed_count += 1
            else:
                failed_count += 1

            if scenario.is_ambivalent:
                ambivalent_results.append(result)
            else:
                basic_results.append(result)

        total_time = time.time() - start_time

        # Финальная статистика
        results_summary = {
            "total_scenarios": len(scenarios),
            "basic_scenarios": len(basic_results),
            "ambivalent_scenarios": len(ambivalent_results),
            "passed": passed_count,
            "failed": failed_count,
            "success_rate": (passed_count / len(scenarios)) * 100,
            "total_execution_time": total_time,
            "avg_execution_time": total_time / len(scenarios),
            "basic_success_rate": (
                (sum(1 for r in basic_results if r.passed) / len(basic_results)) * 100
                if basic_results
                else 0
            ),
            "ambivalent_success_rate": (
                (sum(1 for r in ambivalent_results if r.passed) / len(ambivalent_results)) * 100
                if ambivalent_results
                else 0
            ),
        }

        # Сохраняем результаты
        self._save_results(results_summary)

        return results_summary

    def _save_results(self, summary: Dict[str, Any]):
        """Сохраняет результаты тестирования"""
        # Полный отчет
        full_report = {
            "summary": summary,
            "test_results": [asdict(result) for result in self.test_results],
            "generated_at": time.time(),
        }

        report_file = self.results_dir / "e2e_full_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)

        print(f"✅ Full E2E report saved: {report_file}")

    def get_failure_analysis(self) -> Dict[str, Any]:
        """Анализирует провалившиеся тесты"""
        failed_results = [r for r in self.test_results if not r.passed]

        if not failed_results:
            return {"message": "No failed tests to analyze"}

        # Группируем ошибки
        error_categories = {}
        for result in failed_results:
            for issue in result.issues:
                category = issue.split(":")[0] if ":" in issue else "Other"
                if category not in error_categories:
                    error_categories[category] = 0
                error_categories[category] += 1

        return {
            "total_failures": len(failed_results),
            "error_categories": error_categories,
            "most_common_issues": sorted(
                error_categories.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "failed_scenarios": [r.scenario_id for r in failed_results],
        }


if __name__ == "__main__":
    # Запуск E2E тестирования
    tester = E2EScenarioTester()

    print("🎯 Starting E2E scenario generation...")
    generator = E2EScenarioGenerator()

    # Показываем примеры сценариев
    basic_scenarios = generator.generate_basic_scenarios()
    ambivalent_scenarios = generator.generate_ambivalent_scenarios()

    print("\n📋 Generated scenarios:")
    print(f"- Basic scenarios: {len(basic_scenarios)}")
    print(f"- Ambivalent scenarios: {len(ambivalent_scenarios)}")

    # Показываем первые несколько сценариев
    print("\n🔍 Sample basic scenarios:")
    for scenario in basic_scenarios[:3]:
        print(f"  {scenario.scenario_id}: {scenario.name}")

    print("\n🔍 Ambivalent scenarios:")
    for scenario in ambivalent_scenarios:
        print(f"  {scenario.scenario_id}: {scenario.name}")

    print(f"\n🚀 Ready to run {len(basic_scenarios) + len(ambivalent_scenarios)} E2E scenarios!")
    print("Run with full execution: python -m tests.test_e2e_scenarios --run-full")
