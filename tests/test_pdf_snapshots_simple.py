"""
📸 PDF Snapshot Tests Simple - Упрощенные snapshot тесты
Проверяет базовые характеристики PDF файлов
"""

import os
import json
import hashlib
from typing import Dict, Any, List
from pathlib import Path
import tempfile


class SimplePDFSnapshotTester:
    """Упрощенный тестер снапшотов PDF"""

    def __init__(self, snapshots_dir: str = "tests/snapshots"):
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Файл для метаданных
        self.metadata_file = self.snapshots_dir / "simple_snapshots.json"
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

    def _get_file_hash(self, file_path: str, sample_size: int = 1024) -> str:
        """Получает хеш части файла для сравнения"""
        try:
            if not os.path.exists(file_path):
                return ""

            with open(file_path, "rb") as f:
                content = f.read(sample_size)
                return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def create_snapshot(self, test_name: str, pdf_path: str) -> Dict[str, Any]:
        """Создает снапшот PDF файла"""

        if not os.path.exists(pdf_path):
            return {"error": "PDF file does not exist"}

        file_size = os.path.getsize(pdf_path)
        file_hash = self._get_file_hash(pdf_path)

        snapshot = {
            "test_name": test_name,
            "file_size": file_size,
            "file_hash": file_hash,
            "created_at": self._get_timestamp(),
            "expectations": {
                "min_size": max(1000, file_size * 0.7),  # -30%
                "max_size": file_size * 1.3,  # +30%
                "size_category": self._get_size_category(file_size),
            },
        }

        # Сохраняем снапшот
        self.metadata[test_name] = snapshot
        self._save_metadata()

        print(f"✅ Created snapshot: {test_name} (size: {file_size} bytes)")
        return snapshot

    def verify_snapshot(self, test_name: str, pdf_path: str) -> Dict[str, Any]:
        """Проверяет PDF против снапшота"""

        if test_name not in self.metadata:
            return self.create_snapshot(test_name, pdf_path)

        snapshot = self.metadata[test_name]
        expectations = snapshot.get("expectations", {})

        # Текущие характеристики файла
        if not os.path.exists(pdf_path):
            return {"test_name": test_name, "passed": False, "issues": ["PDF file does not exist"]}

        current_size = os.path.getsize(pdf_path)
        current_hash = self._get_file_hash(pdf_path)

        # Проверка
        issues = []

        # Размер файла
        min_size = expectations.get("min_size", 0)
        max_size = expectations.get("max_size", float("inf"))

        if current_size < min_size:
            issues.append(f"File too small: {current_size} < {min_size}")

        if current_size > max_size:
            issues.append(f"File too large: {current_size} > {max_size}")

        # Категория размера
        expected_category = expectations.get("size_category")
        current_category = self._get_size_category(current_size)

        if expected_category and current_category != expected_category:
            issues.append(f"Size category changed: {current_category} != {expected_category}")

        return {
            "test_name": test_name,
            "passed": len(issues) == 0,
            "issues": issues,
            "current_size": current_size,
            "expected_size": snapshot.get("file_size", 0),
            "current_hash": current_hash,
            "expected_hash": snapshot.get("file_hash", ""),
        }

    def _get_size_category(self, size: int) -> str:
        """Категоризирует размер файла"""
        if size < 5000:
            return "tiny"
        elif size < 20000:
            return "small"
        elif size < 100000:
            return "medium"
        else:
            return "large"

    def _get_timestamp(self) -> float:
        """Получает текущий timestamp"""
        try:
            import time

            return time.time()
        except:
            return 0

    def run_pdf_tests(self) -> Dict[str, Any]:
        """Запускает тесты PDF генерации"""

        print("📸 RUNNING SIMPLE PDF SNAPSHOT TESTS")
        print("=" * 50)

        # Импортируем минимальный PDF генератор
        try:
            import sys

            sys.path.append(".")
            from bot.ui.pdf_v2_minimal import generate_minimal_pdf
        except ImportError as e:
            print(f"❌ Cannot import PDF generator: {e}")
            return {"error": "Import failed"}

        # Тестовые сценарии
        test_scenarios = [
            {
                "name": "basic_palette",
                "data": {
                    "type": "detailed_palette",
                    "profile": {"undertone": "warm", "season": "autumn"},
                    "result": {
                        "makeup": {
                            "base": [
                                {
                                    "name": "Foundation",
                                    "brand": "Test",
                                    "price": 1500,
                                    "in_stock": True,
                                }
                            ]
                        }
                    },
                },
            },
            {
                "name": "basic_skincare",
                "data": {
                    "type": "detailed_skincare",
                    "profile": {"skin_type": "dry"},
                    "result": {
                        "skincare": {
                            "AM": [
                                {
                                    "name": "Cleanser",
                                    "brand": "Test",
                                    "price": 1200,
                                    "in_stock": True,
                                }
                            ]
                        }
                    },
                },
            },
            {
                "name": "comprehensive",
                "data": {
                    "type": "detailed_palette",
                    "profile": {"undertone": "cool", "season": "winter", "skin_type": "combo"},
                    "result": {
                        "makeup": {
                            "base": [
                                {
                                    "name": "Foundation Cool",
                                    "brand": "Brand A",
                                    "price": 2000,
                                    "in_stock": True,
                                }
                            ],
                            "eyes": [
                                {
                                    "name": "Eyeshadow",
                                    "brand": "Brand B",
                                    "price": 1200,
                                    "in_stock": False,
                                }
                            ],
                        },
                        "skincare": {
                            "AM": [
                                {
                                    "name": "Foam Cleanser",
                                    "brand": "Brand C",
                                    "price": 1000,
                                    "in_stock": True,
                                }
                            ],
                            "PM": [
                                {
                                    "name": "Night Cream",
                                    "brand": "Brand D",
                                    "price": 2500,
                                    "in_stock": True,
                                }
                            ],
                        },
                    },
                },
            },
        ]

        results = {"total_tests": len(test_scenarios), "passed": 0, "failed": 0, "details": []}

        for scenario in test_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")

            try:
                # Генерируем PDF во временной директории
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_uid = 88888

                    # Создаем структуру директорий для тестов
                    original_path = Path("data/reports").resolve()
                    test_path = Path(temp_dir) / "data" / "reports"
                    test_path.mkdir(parents=True, exist_ok=True)

                    # Временно меняем базовую директорию
                    os.chdir(temp_dir)

                    try:
                        pdf_path = generate_minimal_pdf(test_uid, scenario["data"])

                        if pdf_path and os.path.exists(pdf_path):
                            # Копируем PDF в постоянную директорию для снапшота
                            permanent_pdf = self.snapshots_dir / f"{scenario['name']}_test.pdf"
                            import shutil

                            shutil.copy2(pdf_path, permanent_pdf)

                            # Проверяем снапшот
                            verification = self.verify_snapshot(
                                scenario["name"], str(permanent_pdf)
                            )
                            results["details"].append(verification)

                            if verification["passed"]:
                                results["passed"] += 1
                                print(f"✅ {scenario['name']}: PASSED")
                            else:
                                results["failed"] += 1
                                print(f"❌ {scenario['name']}: FAILED")
                                for issue in verification["issues"]:
                                    print(f"  - {issue}")
                        else:
                            results["failed"] += 1
                            print(f"❌ {scenario['name']}: PDF generation failed")

                    finally:
                        # Возвращаемся в оригинальную директорию
                        os.chdir(original_path.parent)

            except Exception as e:
                results["failed"] += 1
                print(f"❌ {scenario['name']}: Test error: {e}")

        # Итоги
        success_rate = (results["passed"] / results["total_tests"]) * 100
        print(f"\n📊 SNAPSHOT TEST RESULTS:")
        print(f"Total: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Success rate: {success_rate:.1f}%")

        return results


if __name__ == "__main__":
    # Запуск тестирования
    tester = SimplePDFSnapshotTester()
    results = tester.run_pdf_tests()

    # Проверка результатов
    if results.get("passed", 0) == results.get("total_tests", 1):
        print("\n🎉 ALL SNAPSHOT TESTS PASSED!")
        exit(0)
    else:
        print(f"\n💥 {results.get('failed', 0)} TESTS FAILED!")
        exit(1)
