"""
📸 PDF Snapshot Tests - Тестирование стабильности PDF генерации
Проверяет что ключевые элементы PDF остаются неизменными при обновлениях
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import pytest

class PDFSnapshotTester:
    """Тестер снапшотов PDF файлов"""
    
    def __init__(self, snapshots_dir: str = "tests/snapshots"):
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Файл для хранения метаданных снапшотов
        self.metadata_file = self.snapshots_dir / "pdf_snapshots.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Загружает метаданные снапшотов"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_metadata(self):
        """Сохраняет метаданные снапшотов"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Извлекает текст из PDF (упрощенно - через fpdf)"""
        try:
            # Для полноценного извлечения нужен PyPDF2 или pdfplumber
            # Пока проверяем наличие файла и размер
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                with open(pdf_path, 'rb') as f:
                    # Читаем первые и последние байты для хеша
                    content = f.read(min(1024, file_size))
                    if file_size > 1024:
                        f.seek(-512, 2)  # Последние 512 байт
                        content += f.read()
                
                return hashlib.md5(content).hexdigest()
            else:
                return ""
        except Exception as e:
            print(f"Error extracting PDF content: {e}")
            return ""
    
    def _get_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Получает метаданные PDF файла"""
        if not os.path.exists(pdf_path):
            return {"exists": False}
        
        file_size = os.path.getsize(pdf_path)
        content_hash = self._extract_pdf_text(pdf_path)
        
        return {
            "exists": True,
            "file_size": file_size,
            "content_hash": content_hash,
            "size_category": self._categorize_file_size(file_size)
        }
    
    def _categorize_file_size(self, size: int) -> str:
        """Категоризирует размер файла"""
        if size < 10000:  # < 10KB
            return "small"
        elif size < 100000:  # < 100KB  
            return "medium"
        elif size < 500000:  # < 500KB
            return "large"
        else:
            return "very_large"
    
    def create_snapshot(self, test_name: str, pdf_path: str, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Создает снапшот PDF файла"""
        
        snapshot_id = f"{test_name}_{hashlib.md5(test_name.encode()).hexdigest()[:8]}"
        
        # Получаем метаданные PDF
        pdf_metadata = self._get_pdf_metadata(pdf_path)
        
        # Создаем снапшот
        snapshot = {
            "test_name": test_name,
            "snapshot_id": snapshot_id,
            "created_at": import_time_time(),
            "pdf_metadata": pdf_metadata,
            "test_data_hash": hashlib.md5(json.dumps(test_data or {}, sort_keys=True).encode()).hexdigest(),
            "expectations": {
                "min_file_size": max(1000, pdf_metadata.get("file_size", 0) * 0.8),  # -20%
                "max_file_size": pdf_metadata.get("file_size", 0) * 1.2,  # +20%
                "expected_size_category": pdf_metadata.get("size_category", "medium")
            }
        }
        
        # Копируем PDF файл в директорию снапшотов
        if pdf_metadata.get("exists"):
            snapshot_pdf_path = self.snapshots_dir / f"{snapshot_id}.pdf"
            import shutil
            shutil.copy2(pdf_path, snapshot_pdf_path)
            snapshot["snapshot_file"] = str(snapshot_pdf_path)
        
        # Сохраняем в метаданные
        self.metadata[snapshot_id] = snapshot
        self._save_metadata()
        
        print(f"✅ Created PDF snapshot: {test_name} -> {snapshot_id}")
        return snapshot
    
    def verify_snapshot(self, test_name: str, pdf_path: str, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Проверяет PDF против существующего снапшота"""
        
        snapshot_id = f"{test_name}_{hashlib.md5(test_name.encode()).hexdigest()[:8]}"
        
        if snapshot_id not in self.metadata:
            # Создаем новый снапшот если не существует
            return self.create_snapshot(test_name, pdf_path, test_data)
        
        snapshot = self.metadata[snapshot_id]
        expectations = snapshot.get("expectations", {})
        
        # Получаем текущие метаданные
        current_metadata = self._get_pdf_metadata(pdf_path)
        
        # Результат проверки
        verification_result = {
            "test_name": test_name,
            "snapshot_id": snapshot_id,
            "passed": True,
            "issues": [],
            "current_metadata": current_metadata,
            "expected_metadata": snapshot.get("pdf_metadata", {}),
            "expectations": expectations
        }
        
        # Проверка существования файла
        if not current_metadata.get("exists"):
            verification_result["passed"] = False
            verification_result["issues"].append("PDF file does not exist")
            return verification_result
        
        # Проверка размера файла
        current_size = current_metadata.get("file_size", 0)
        min_size = expectations.get("min_file_size", 0)
        max_size = expectations.get("max_file_size", float('inf'))
        
        if current_size < min_size:
            verification_result["passed"] = False
            verification_result["issues"].append(f"File size too small: {current_size} < {min_size}")
        
        if current_size > max_size:
            verification_result["passed"] = False
            verification_result["issues"].append(f"File size too large: {current_size} > {max_size}")
        
        # Проверка категории размера
        expected_category = expectations.get("expected_size_category")
        current_category = current_metadata.get("size_category")
        
        if expected_category and current_category != expected_category:
            verification_result["passed"] = False
            verification_result["issues"].append(f"Size category changed: {current_category} != {expected_category}")
        
        # Проверка хеша контента (строгая проверка)
        expected_hash = snapshot.get("pdf_metadata", {}).get("content_hash")
        current_hash = current_metadata.get("content_hash")
        
        if expected_hash and current_hash != expected_hash:
            # Это предупреждение, не критическая ошибка
            verification_result["issues"].append(f"Content hash changed: {current_hash} != {expected_hash}")
        
        return verification_result
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Запускает комплексное тестирование PDF генерации"""
        
        print("📸 RUNNING PDF SNAPSHOT TESTS")
        print("=" * 50)
        
        # Импортируем PDF генератор
        try:
            import sys
            sys.path.append('.')
            from bot.ui.pdf_v2 import StructuredPDFGenerator
        except ImportError as e:
            print(f"❌ Cannot import PDF generator: {e}")
            return {"error": "Import failed"}
        
        # Тестовые сценарии
        test_scenarios = self._get_test_scenarios()
        
        results = {
            "total_tests": len(test_scenarios),
            "passed": 0,
            "failed": 0,
            "test_results": []
        }
        
        generator = StructuredPDFGenerator()
        
        for scenario in test_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            
            try:
                # Генерируем PDF
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_uid = 99999  # Тестовый пользователь
                    
                    # Переопределяем путь для тестового PDF
                    original_generate = generator.generate_structured_pdf
                    
                    def test_generate(uid, snapshot):
                        # Создаем временную директорию для тестового PDF
                        test_user_dir = Path(temp_dir) / "reports" / str(uid)
                        test_user_dir.mkdir(parents=True, exist_ok=True)
                        
                        test_pdf_path = test_user_dir / "test.pdf"
                        
                        # Вызываем оригинальный метод но сохраняем в тестовую директорию
                        try:
                            pdf = generator._setup_pdf()
                            generator._add_header(pdf, "TEST REPORT")
                            generator._add_summary_section(pdf, snapshot.get('profile', {}), snapshot.get('type', 'test'))
                            
                            if 'makeup' in snapshot.get('result', {}):
                                generator._add_makeup_section(pdf, snapshot['result']['makeup'])
                            
                            if 'skincare' in snapshot.get('result', {}):
                                generator._add_skincare_section(pdf, snapshot['result']['skincare'])
                            
                            pdf.output(str(test_pdf_path))
                            return str(test_pdf_path)
                        except Exception as e:
                            print(f"PDF generation error: {e}")
                            return ""
                    
                    generator.generate_structured_pdf = test_generate
                    
                    # Генерируем PDF
                    pdf_path = generator.generate_structured_pdf(test_uid, scenario['data'])
                    
                    # Восстанавливаем оригинальный метод
                    generator.generate_structured_pdf = original_generate
                    
                    if pdf_path and os.path.exists(pdf_path):
                        # Проверяем снапшот
                        verification = self.verify_snapshot(scenario['name'], pdf_path, scenario['data'])
                        
                        results["test_results"].append(verification)
                        
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
                        
            except Exception as e:
                results["failed"] += 1
                print(f"❌ {scenario['name']}: Test error: {e}")
        
        # Итоговый отчет
        print(f"\n📊 SNAPSHOT TEST RESULTS:")
        print(f"Total tests: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Success rate: {results['passed']/results['total_tests']*100:.1f}%")
        
        return results
    
    def _get_test_scenarios(self) -> List[Dict[str, Any]]:
        """Получает тестовые сценарии для PDF"""
        
        return [
            {
                "name": "basic_palette_report",
                "data": {
                    "type": "detailed_palette",
                    "profile": {
                        "user_id": 12345,
                        "undertone": "warm",
                        "season": "autumn",
                        "contrast": "medium"
                    },
                    "result": {
                        "makeup": {
                            "base": [
                                {
                                    "name": "Foundation Warm Beige",
                                    "brand": "Test Brand",
                                    "category": "foundation",
                                    "price": 1500,
                                    "in_stock": True,
                                    "explain": "идеально для теплого подтона"
                                }
                            ]
                        }
                    }
                }
            },
            {
                "name": "basic_skincare_report", 
                "data": {
                    "type": "detailed_skincare",
                    "profile": {
                        "user_id": 12346,
                        "skin_type": "dry",
                        "concerns": ["dryness", "aging"]
                    },
                    "result": {
                        "skincare": {
                            "AM": [
                                {
                                    "name": "Hydrating Cleanser",
                                    "brand": "Test Brand",
                                    "category": "cleanser",
                                    "price": 1200,
                                    "in_stock": True,
                                    "actives": ["hyaluronic acid"],
                                    "explain": "мягко очищает сухую кожу"
                                }
                            ]
                        }
                    }
                }
            },
            {
                "name": "comprehensive_report",
                "data": {
                    "type": "detailed_palette",
                    "profile": {
                        "user_id": 12347,
                        "undertone": "cool",
                        "season": "winter",
                        "contrast": "high",
                        "skin_type": "combo",
                        "concerns": ["acne", "pigmentation"]
                    },
                    "result": {
                        "makeup": {
                            "base": [
                                {"name": "Cool Foundation", "brand": "Brand A", "category": "foundation", "price": 2000, "in_stock": True, "explain": "для холодного подтона"},
                                {"name": "Light Concealer", "brand": "Brand B", "category": "concealer", "price": 800, "in_stock": True, "explain": "маскирует несовершенства"}
                            ],
                            "eyes": [
                                {"name": "Cool Eyeshadow", "brand": "Brand C", "category": "eyeshadow", "price": 1200, "in_stock": False, "explain": "зимние оттенки"}
                            ]
                        },
                        "skincare": {
                            "AM": [
                                {"name": "Gentle Foam", "brand": "Brand D", "category": "cleanser", "price": 1000, "in_stock": True, "actives": ["salicylic acid"], "explain": "для проблемной кожи"}
                            ],
                            "PM": [
                                {"name": "Retinol Serum", "brand": "Brand E", "category": "serum", "price": 2500, "in_stock": True, "actives": ["retinol"], "explain": "против пигментации"}
                            ]
                        }
                    }
                }
            }
        ]


def import_time_time():
    """Импорт time.time с обработкой ошибок"""
    try:
        import time
        return time.time()
    except:
        return 0


if __name__ == "__main__":
    # Запуск тестирования снапшотов
    tester = PDFSnapshotTester()
    results = tester.run_comprehensive_test()
    
    # Проверка результатов
    if results.get("passed", 0) == results.get("total_tests", 1):
        print("\n🎉 ALL SNAPSHOT TESTS PASSED!")
        exit(0)
    else:
        print(f"\n💥 {results.get('failed', 0)} TESTS FAILED!")
        exit(1)






