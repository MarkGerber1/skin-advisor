"""
📸 PDF Snapshot Tests Working - Тесты для существующего PDF генератора
Использует bot/ui/pdf.py (рабочую версию) для snapshot тестирования
"""

import os
import json
import hashlib
from typing import Dict, Any
from pathlib import Path


class WorkingPDFSnapshotTester:
    """Snapshot тестер для рабочего PDF генератора"""

    def __init__(self, snapshots_dir: str = "tests/snapshots"):
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.snapshots_dir / "working_pdf_snapshots.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Загружает метаданные снапшотов"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_metadata(self):
        """Сохраняет метаданные"""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def _get_file_signature(self, file_path: str) -> Dict[str, Any]:
        """Получает сигнатуру файла для сравнения"""
        if not os.path.exists(file_path):
            return {"exists": False}

        file_size = os.path.getsize(file_path)

        # Читаем начало и конец файла для хеша
        with open(file_path, "rb") as f:
            header = f.read(min(512, file_size))
            if file_size > 512:
                f.seek(-256, 2)
                footer = f.read()
            else:
                footer = b""

        content_hash = hashlib.md5(header + footer).hexdigest()

        return {
            "exists": True,
            "file_size": file_size,
            "content_hash": content_hash,
            "size_category": self._categorize_size(file_size),
        }

    def _categorize_size(self, size: int) -> str:
        """Категоризирует размер файла"""
        if size < 5000:
            return "small"
        elif size < 20000:
            return "medium"
        elif size < 100000:
            return "large"
        else:
            return "very_large"

    def create_snapshot(self, test_name: str, pdf_path: str) -> Dict[str, Any]:
        """Создает снапшот PDF"""
        signature = self._get_file_signature(pdf_path)

        if not signature.get("exists"):
            return {"error": "PDF file does not exist"}

        snapshot = {
            "test_name": test_name,
            "signature": signature,
            "created_at": self._get_timestamp(),
            "tolerances": {"size_tolerance": 0.2, "allow_size_category_change": False},  # ±20%
        }

        self.metadata[test_name] = snapshot
        self._save_metadata()

        print(
            f"✅ Created snapshot '{test_name}': {signature['file_size']} bytes, {signature['size_category']}"
        )
        return snapshot

    def verify_snapshot(self, test_name: str, pdf_path: str) -> Dict[str, Any]:
        """Проверяет PDF против снапшота"""
        if test_name not in self.metadata:
            return self.create_snapshot(test_name, pdf_path)

        expected = self.metadata[test_name]
        expected_sig = expected.get("signature", {})
        tolerances = expected.get("tolerances", {})

        current_sig = self._get_file_signature(pdf_path)

        result = {
            "test_name": test_name,
            "passed": True,
            "issues": [],
            "current": current_sig,
            "expected": expected_sig,
        }

        if not current_sig.get("exists"):
            result["passed"] = False
            result["issues"].append("PDF file does not exist")
            return result

        # Проверка размера файла
        expected_size = expected_sig.get("file_size", 0)
        current_size = current_sig.get("file_size", 0)
        size_tolerance = tolerances.get("size_tolerance", 0.2)

        if expected_size > 0:
            size_diff = abs(current_size - expected_size) / expected_size
            if size_diff > size_tolerance:
                result["passed"] = False
                result["issues"].append(
                    f"Size difference too large: {size_diff:.1%} > {size_tolerance:.1%}"
                )

        # Проверка категории размера
        if not tolerances.get("allow_size_category_change", False):
            expected_category = expected_sig.get("size_category")
            current_category = current_sig.get("size_category")

            if expected_category and current_category != expected_category:
                result["passed"] = False
                result["issues"].append(
                    f"Size category changed: {current_category} != {expected_category}"
                )

        return result

    def _get_timestamp(self) -> float:
        """Получает текущий timestamp"""
        try:
            import time

            return time.time()
        except:
            return 0

    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Запускает комплексные тесты PDF генерации"""

        print("📸 RUNNING WORKING PDF SNAPSHOT TESTS")
        print("=" * 50)

        # Импорт рабочего PDF генератора
        try:
            import sys

            sys.path.append(".")
            from bot.ui.pdf import save_text_pdf, save_last_json
        except ImportError as e:
            print(f"❌ Cannot import working PDF generator: {e}")
            return {"error": "Import failed"}

        # Тестовые сценарии
        test_scenarios = [
            {
                "name": "simple_text_report",
                "title": "Simple Report",
                "content": "This is a simple test report with basic text content. Testing PDF generation stability.",
            },
            {
                "name": "medium_text_report",
                "title": "Medium Report with Sections",
                "content": """SECTION 1: PROFILE ANALYSIS
                
Your color profile has been analyzed based on your responses.

SECTION 2: MAKEUP RECOMMENDATIONS

Here are the recommended makeup products:
- Foundation: Perfect Match
- Blush: Natural Glow
- Lipstick: Classic Red

SECTION 3: SKINCARE ROUTINE

Morning routine:
- Gentle Cleanser
- Moisturizer with SPF

Evening routine:
- Deep Cleanser
- Night Cream""",
            },
            {
                "name": "large_report_with_products",
                "title": "Comprehensive Beauty Report",
                "content": """COMPREHENSIVE BEAUTY ANALYSIS REPORT

PROFILE SUMMARY:
- Undertone: Warm
- Season: Autumn
- Contrast: Medium
- Skin Type: Combination

MAKEUP RECOMMENDATIONS (15 CATEGORIES):

1. BASE MAKEUP:
   - Foundation: Brand A Perfect Foundation (1500 RUB)
   - Concealer: Brand B Light Concealer (800 RUB)
   - Powder: Brand C Setting Powder (1200 RUB)

2. FACE CONTOURING:
   - Blush: Brand D Warm Peach (900 RUB)
   - Bronzer: Brand E Matte Bronze (1100 RUB)
   - Highlighter: Brand F Golden Glow (1300 RUB)

3. EYE MAKEUP:
   - Eyeshadow: Brand G Autumn Palette (1800 RUB)
   - Eyeliner: Brand H Brown Liner (600 RUB)
   - Mascara: Brand I Volume Mascara (1000 RUB)

4. LIP MAKEUP:
   - Lipstick: Brand J Warm Red (1200 RUB)
   - Lip Gloss: Brand K Natural Gloss (800 RUB)

SKINCARE ROUTINE (7 STEPS):

MORNING ROUTINE:
1. Cleanser: Gentle Foam Cleanser
2. Toner: Hydrating Toner
3. Serum: Vitamin C Serum
4. Moisturizer: Day Cream
5. SPF: Sunscreen SPF 30

EVENING ROUTINE:
1. Cleanser: Oil Cleanser
2. Treatment: Retinol Serum
3. Moisturizer: Night Cream

WEEKLY CARE:
1. Exfoliant: Gentle Scrub (2x week)
2. Mask: Hydrating Mask (1x week)

STATISTICS:
- Total makeup products: 11
- Total skincare products: 8
- Products in stock: 18/19 (95%)

This report is generated based on your personal color analysis and skin assessment.""",
            },
        ]

        results = {"total_tests": len(test_scenarios), "passed": 0, "failed": 0, "test_details": []}

        for scenario in test_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")

            try:
                # Генерируем PDF с использованием рабочего генератора
                test_uid = 77777
                pdf_path = save_text_pdf(test_uid, scenario["title"], scenario["content"])

                if pdf_path and os.path.exists(pdf_path):
                    # Проверяем снапшот
                    verification = self.verify_snapshot(scenario["name"], pdf_path)
                    results["test_details"].append(verification)

                    if verification.get("passed", False):
                        results["passed"] += 1
                        current_size = verification.get("current", {}).get("file_size", 0)
                        print(f"✅ {scenario['name']}: PASSED ({current_size} bytes)")
                    else:
                        results["failed"] += 1
                        print(f"❌ {scenario['name']}: FAILED")
                        issues = verification.get("issues", [])
                        for issue in issues:
                            print(f"  - {issue}")
                else:
                    results["failed"] += 1
                    print(f"❌ {scenario['name']}: PDF generation failed")
                    results["test_details"].append(
                        {
                            "test_name": scenario["name"],
                            "passed": False,
                            "issues": ["PDF generation returned empty path"],
                        }
                    )

            except Exception as e:
                results["failed"] += 1
                print(f"❌ {scenario['name']}: Exception: {e}")
                results["test_details"].append(
                    {
                        "test_name": scenario["name"],
                        "passed": False,
                        "issues": [f"Exception: {str(e)}"],
                    }
                )

        # Итоги
        success_rate = (results["passed"] / results["total_tests"]) * 100
        print("\n📊 FINAL SNAPSHOT TEST RESULTS:")
        print(f"Total tests: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Success rate: {success_rate:.1f}%")

        if results["passed"] == results["total_tests"]:
            print("🎉 ALL PDF SNAPSHOT TESTS PASSED!")

        return results

    def get_snapshot_summary(self) -> Dict[str, Any]:
        """Получает сводку по всем снапшотам"""
        if not self.metadata:
            return {"total_snapshots": 0}

        total_snapshots = len(self.metadata)
        size_distribution = {}

        for snapshot_name, snapshot_data in self.metadata.items():
            category = snapshot_data.get("signature", {}).get("size_category", "unknown")
            size_distribution[category] = size_distribution.get(category, 0) + 1

        return {
            "total_snapshots": total_snapshots,
            "size_distribution": size_distribution,
            "snapshot_names": list(self.metadata.keys()),
        }


if __name__ == "__main__":
    # Запуск тестирования
    tester = WorkingPDFSnapshotTester()

    print("📋 Current snapshots summary:")
    summary = tester.get_snapshot_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Запуск тестов
    results = tester.run_comprehensive_tests()

    # Финальная сводка
    print("\n📋 Updated snapshots summary:")
    summary = tester.get_snapshot_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Выход с кодом
    if results.get("passed", 0) == results.get("total_tests", 1):
        exit(0)
    else:
        exit(1)
