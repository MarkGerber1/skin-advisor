"""
🧪 A/B Testing Framework - Фреймворк для A/B тестирования текстов и UX
Позволяет тестировать разные варианты подсказок, explain и интерфейса
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

class ABTestStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

@dataclass
class ABVariant:
    """Вариант A/B теста"""
    id: str
    name: str
    content: Dict[str, Any]  # Содержимое варианта
    weight: float = 0.5  # Вес для распределения трафика (0.0-1.0)

@dataclass
class ABTest:
    """Конфигурация A/B теста"""
    id: str
    name: str
    description: str
    status: ABTestStatus
    variants: List[ABVariant]
    start_date: Optional[float] = None
    end_date: Optional[float] = None
    target_metric: str = "completion_rate"  # Какую метрику оптимизируем
    min_sample_size: int = 100  # Минимальный размер выборки
    created_at: float = None

@dataclass
class ABTestAssignment:
    """Назначение пользователя в A/B тест"""
    user_id: int
    test_id: str
    variant_id: str
    assigned_at: float

@dataclass
class ABTestResult:
    """Результат A/B теста"""
    test_id: str
    variant_id: str
    metric_name: str
    metric_value: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    statistical_significance: bool

class ABTestingFramework:
    """Фреймворк для A/B тестирования"""
    
    def __init__(self, tests_dir: str = "data/ab_tests"):
        self.tests_dir = Path(tests_dir)
        self.tests_dir.mkdir(parents=True, exist_ok=True)
        
        # Файлы для хранения
        self.tests_file = self.tests_dir / "tests.json"
        self.assignments_file = self.tests_dir / "assignments.jsonl"
        self.results_file = self.tests_dir / "results.jsonl"
        
        # Загрузка активных тестов
        self.active_tests = self._load_tests()
        
        # Кеш назначений пользователей
        self.user_assignments = self._load_user_assignments()
    
    def create_test(self, test_id: str, name: str, description: str, variants: List[ABVariant]) -> ABTest:
        """Создает новый A/B тест"""
        
        test = ABTest(
            id=test_id,
            name=name,
            description=description,
            status=ABTestStatus.DRAFT,
            variants=variants,
            created_at=time.time()
        )
        
        self.active_tests[test_id] = test
        self._save_tests()
        
        return test
    
    def start_test(self, test_id: str) -> bool:
        """Запускает A/B тест"""
        if test_id not in self.active_tests:
            return False
        
        test = self.active_tests[test_id]
        test.status = ABTestStatus.ACTIVE
        test.start_date = time.time()
        
        self._save_tests()
        return True
    
    def stop_test(self, test_id: str) -> bool:
        """Останавливает A/B тест"""
        if test_id not in self.active_tests:
            return False
        
        test = self.active_tests[test_id]
        test.status = ABTestStatus.COMPLETED
        test.end_date = time.time()
        
        self._save_tests()
        return True
    
    def assign_user_to_variant(self, user_id: int, test_id: str) -> Optional[str]:
        """Назначает пользователя в вариант A/B теста"""
        
        # Проверяем есть ли уже назначение
        user_key = f"{user_id}_{test_id}"
        if user_key in self.user_assignments:
            return self.user_assignments[user_key]
        
        # Проверяем что тест активен
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        if test.status != ABTestStatus.ACTIVE:
            return None
        
        # Назначаем вариант на основе хеша user_id
        variant_id = self._deterministic_variant_assignment(user_id, test)
        
        # Сохраняем назначение
        assignment = ABTestAssignment(
            user_id=user_id,
            test_id=test_id,
            variant_id=variant_id,
            assigned_at=time.time()
        )
        
        self._save_assignment(assignment)
        self.user_assignments[user_key] = variant_id
        
        return variant_id
    
    def get_variant_content(self, user_id: int, test_id: str, content_key: str, default_value: Any = None) -> Any:
        """Получает контент варианта для пользователя"""
        
        variant_id = self.assign_user_to_variant(user_id, test_id)
        if not variant_id:
            return default_value
        
        test = self.active_tests.get(test_id)
        if not test:
            return default_value
        
        # Находим вариант
        variant = next((v for v in test.variants if v.id == variant_id), None)
        if not variant:
            return default_value
        
        return variant.content.get(content_key, default_value)
    
    def record_conversion(self, user_id: int, test_id: str, metric_name: str, metric_value: float):
        """Записывает конверсию для A/B теста"""
        
        variant_id = self.user_assignments.get(f"{user_id}_{test_id}")
        if not variant_id:
            return
        
        result = ABTestResult(
            test_id=test_id,
            variant_id=variant_id,
            metric_name=metric_name,
            metric_value=metric_value,
            sample_size=1,
            confidence_interval=(0.0, 0.0),  # Будет вычислено при анализе
            statistical_significance=False
        )
        
        self._save_result(result)
    
    def analyze_test_results(self, test_id: str) -> Dict[str, Any]:
        """Анализирует результаты A/B теста"""
        
        results = self._load_test_results(test_id)
        if not results:
            return {"error": "No results found"}
        
        # Группируем по вариантам
        variant_stats = {}
        for result in results:
            variant_id = result.variant_id
            if variant_id not in variant_stats:
                variant_stats[variant_id] = {"values": [], "conversions": 0, "total": 0}
            
            variant_stats[variant_id]["values"].append(result.metric_value)
            variant_stats[variant_id]["total"] += 1
            if result.metric_value > 0:
                variant_stats[variant_id]["conversions"] += 1
        
        # Вычисляем статистики
        analysis = {}
        for variant_id, stats in variant_stats.items():
            values = stats["values"]
            total = stats["total"]
            conversions = stats["conversions"]
            
            if total > 0:
                mean_value = sum(values) / len(values)
                conversion_rate = conversions / total
                
                analysis[variant_id] = {
                    "sample_size": total,
                    "conversion_rate": conversion_rate,
                    "mean_value": mean_value,
                    "conversions": conversions
                }
            else:
                analysis[variant_id] = {
                    "sample_size": 0,
                    "conversion_rate": 0.0,
                    "mean_value": 0.0,
                    "conversions": 0
                }
        
        # Определяем победителя (упрощенно)
        if len(analysis) >= 2:
            best_variant = max(analysis.keys(), key=lambda v: analysis[v]["conversion_rate"])
            
            # Простая проверка статистической значимости
            best_sample = analysis[best_variant]["sample_size"]
            best_rate = analysis[best_variant]["conversion_rate"]
            
            # Считаем значимым если sample size >= min_sample_size и разница > 5%
            test = self.active_tests.get(test_id)
            min_sample = test.min_sample_size if test else 100
            
            is_significant = (best_sample >= min_sample and 
                            best_rate > max(analysis[v]["conversion_rate"] for v in analysis.keys() if v != best_variant) + 0.05)
            
            return {
                "test_id": test_id,
                "variants": analysis,
                "winner": best_variant if is_significant else None,
                "statistical_significance": is_significant,
                "total_participants": sum(stats["sample_size"] for stats in analysis.values())
            }
        
        return {"test_id": test_id, "variants": analysis}
    
    def _deterministic_variant_assignment(self, user_id: int, test: ABTest) -> str:
        """Детерминированное назначение варианта на основе хеша"""
        
        # Создаем хеш от user_id + test_id для стабильности
        hash_input = f"{user_id}_{test.id}".encode('utf-8')
        hash_value = int(hashlib.md5(hash_input).hexdigest()[:8], 16)
        
        # Нормализуем к [0, 1]
        normalized = (hash_value % 10000) / 10000.0
        
        # Назначаем вариант на основе весов
        cumulative_weight = 0.0
        for variant in test.variants:
            cumulative_weight += variant.weight
            if normalized <= cumulative_weight:
                return variant.id
        
        # Fallback на первый вариант
        return test.variants[0].id if test.variants else "default"
    
    def _load_tests(self) -> Dict[str, ABTest]:
        """Загружает тесты из файла"""
        if not self.tests_file.exists():
            return {}
        
        try:
            with open(self.tests_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            tests = {}
            for test_data in data.get('tests', []):
                test_data['status'] = ABTestStatus(test_data['status'])
                variants = [ABVariant(**v) for v in test_data['variants']]
                test_data['variants'] = variants
                
                test = ABTest(**test_data)
                tests[test.id] = test
            
            return tests
        except Exception:
            return {}
    
    def _save_tests(self):
        """Сохраняет тесты в файл"""
        tests_data = []
        for test in self.active_tests.values():
            test_dict = asdict(test)
            test_dict['status'] = test.status.value
            tests_data.append(test_dict)
        
        with open(self.tests_file, 'w', encoding='utf-8') as f:
            json.dump({"tests": tests_data}, f, indent=2, ensure_ascii=False)
    
    def _load_user_assignments(self) -> Dict[str, str]:
        """Загружает назначения пользователей"""
        assignments = {}
        
        if not self.assignments_file.exists():
            return assignments
        
        with open(self.assignments_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    assignment = ABTestAssignment(**data)
                    key = f"{assignment.user_id}_{assignment.test_id}"
                    assignments[key] = assignment.variant_id
                except Exception:
                    continue
        
        return assignments
    
    def _save_assignment(self, assignment: ABTestAssignment):
        """Сохраняет назначение пользователя"""
        with open(self.assignments_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(assignment), ensure_ascii=False) + '\n')
    
    def _save_result(self, result: ABTestResult):
        """Сохраняет результат теста"""
        with open(self.results_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(result), ensure_ascii=False) + '\n')
    
    def _load_test_results(self, test_id: str) -> List[ABTestResult]:
        """Загружает результаты теста"""
        results = []
        
        if not self.results_file.exists():
            return results
        
        with open(self.results_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get('test_id') == test_id:
                        results.append(ABTestResult(**data))
                except Exception:
                    continue
        
        return results


# Глобальный экземпляр
_ab_framework = None

def get_ab_testing_framework() -> ABTestingFramework:
    """Получить глобальный экземпляр A/B testing framework"""
    global _ab_framework
    if _ab_framework is None:
        _ab_framework = ABTestingFramework()
    return _ab_framework


def setup_default_ab_tests():
    """Настраивает дефолтные A/B тесты для подсказок и explain"""
    
    framework = get_ab_testing_framework()
    
    # Тест 1: Подсказки в шагах
    hints_variants = [
        ABVariant(
            id="hints_detailed",
            name="Detailed Hints",
            content={
                "Q1_HAIR_COLOR": "🔍 Посмотрите на корни волос при естественном освещении. Учитываем только натуральный цвет без окрашивания.",
                "Q3_SKIN_UNDERTONE": "🩸 Посмотрите на вены на внутренней стороне запястья: синие вены = холодный подтон, зеленые = теплый подтон.",
                "B1_TYPE": "💧 Ощущения после умывания водой без средств: стянутость = сухая кожа, жирный блеск = жирная кожа."
            },
            weight=0.5
        ),
        ABVariant(
            id="hints_simple",
            name="Simple Hints", 
            content={
                "Q1_HAIR_COLOR": "💇 Выберите естественный цвет волос",
                "Q3_SKIN_UNDERTONE": "🎨 Определим ваш подтон кожи",
                "B1_TYPE": "🧴 Какой у вас тип кожи?"
            },
            weight=0.5
        )
    ]
    
    framework.create_test(
        test_id="hints_experiment",
        name="Step Hints Effectiveness",
        description="Тестируем влияние подробности подсказок на completion rate",
        variants=hints_variants
    )
    
    # Тест 2: Explain тексты на карточках
    explain_variants = [
        ABVariant(
            id="explain_technical",
            name="Technical Explains",
            content={
                "prefix": "Подойдет:",
                "undertone_warm": "теплый подтон кожи",
                "season_autumn": "глубокие осенние оттенки", 
                "contrast_medium": "средняя интенсивность цвета"
            },
            weight=0.5
        ),
        ABVariant(
            id="explain_emotional",
            name="Emotional Explains",
            content={
                "prefix": "Идеально для вас:",
                "undertone_warm": "теплота вашей кожи",
                "season_autumn": "ваша осенняя палитра",
                "contrast_medium": "гармоничная яркость"
            },
            weight=0.5
        )
    ]
    
    framework.create_test(
        test_id="explain_experiment", 
        name="Product Explain Wording",
        description="Тестируем эмоциональность vs техничность в объяснениях товаров",
        variants=explain_variants
    )
    
    print("✅ Default A/B tests created")
    return framework


if __name__ == "__main__":
    # Тест A/B framework
    print("🧪 A/B TESTING FRAMEWORK TEST")
    print("=" * 50)
    
    # Создаем фреймворк и дефолтные тесты
    framework = setup_default_ab_tests()
    
    # Запускаем тесты
    framework.start_test("hints_experiment")
    framework.start_test("explain_experiment")
    
    # Тестируем назначение пользователей
    test_users = [12345, 12346, 12347, 12348, 12349]
    
    print("\nUser assignments for hints_experiment:")
    for user_id in test_users:
        variant = framework.assign_user_to_variant(user_id, "hints_experiment")
        hint = framework.get_variant_content(user_id, "hints_experiment", "Q1_HAIR_COLOR", "default hint")
        print(f"  User {user_id}: variant {variant}")
        print(f"    Hint: {hint}")
    
    # Имитируем конверсии
    print(f"\nSimulating conversions...")
    for user_id in test_users:
        # Имитируем completion rate: detailed hints = 80%, simple hints = 70%
        variant = framework.assign_user_to_variant(user_id, "hints_experiment")
        completion_rate = 0.8 if variant == "hints_detailed" else 0.7
        
        framework.record_conversion(user_id, "hints_experiment", "completion_rate", completion_rate)
    
    # Анализируем результаты
    print(f"\nAnalysis:")
    results = framework.analyze_test_results("hints_experiment")
    for key, value in results.items():
        print(f"  {key}: {value}")
    
    print(f"\n✅ A/B testing framework ready!")






