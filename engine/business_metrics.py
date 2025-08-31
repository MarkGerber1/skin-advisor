"""
📈 Business Metrics Tracker - Отслеживание бизнес-метрик для оптимизации
Собирает CTR карточек, CR покупок, %OOS, время до отчета и другие KPI
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class UserInteraction:
    """Взаимодействие пользователя с продуктом"""
    user_id: int
    session_id: str
    product_id: str
    product_category: str
    interaction_type: str  # "view", "click", "add_to_cart", "purchase_intent"
    timestamp: float
    additional_data: Dict[str, Any]

@dataclass
class SessionMetrics:
    """Метрики пользовательского сеанса"""
    user_id: int
    session_id: str
    flow_type: str  # "detailed_palette", "detailed_skincare"
    started_at: float
    completed_at: Optional[float]
    steps_completed: int
    total_steps: int
    completion_rate: float
    time_to_complete: Optional[float]
    products_shown: int
    products_clicked: int
    products_added_to_cart: int
    oos_products_encountered: int

class BusinessMetricsTracker:
    """Трекер бизнес-метрик для оптимизации конверсии"""
    
    def __init__(self, metrics_dir: str = "data/metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Файлы для хранения метрик
        self.interactions_file = self.metrics_dir / "interactions.jsonl"
        self.sessions_file = self.metrics_dir / "sessions.jsonl"
        self.daily_stats_file = self.metrics_dir / "daily_stats.json"
        
        # Временные хранилища для активных сеансов
        self.active_sessions: Dict[str, SessionMetrics] = {}
        
    def start_session(self, user_id: int, flow_type: str, total_steps: int) -> str:
        """Начинает отслеживание сеанса"""
        session_id = f"{user_id}_{int(time.time())}"
        
        session = SessionMetrics(
            user_id=user_id,
            session_id=session_id,
            flow_type=flow_type,
            started_at=time.time(),
            completed_at=None,
            steps_completed=0,
            total_steps=total_steps,
            completion_rate=0.0,
            time_to_complete=None,
            products_shown=0,
            products_clicked=0,
            products_added_to_cart=0,
            oos_products_encountered=0
        )
        
        self.active_sessions[session_id] = session
        return session_id
    
    def update_session_progress(self, session_id: str, steps_completed: int):
        """Обновляет прогресс сеанса"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.steps_completed = steps_completed
            session.completion_rate = steps_completed / session.total_steps
    
    def complete_session(self, session_id: str, products_data: List[Dict[str, Any]]):
        """Завершает сеанс и сохраняет метрики"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.completed_at = time.time()
        session.time_to_complete = session.completed_at - session.started_at
        session.completion_rate = 1.0
        
        # Подсчитываем продукты
        session.products_shown = len(products_data)
        session.oos_products_encountered = sum(1 for p in products_data if not p.get('in_stock', True))
        
        # Сохраняем в файл
        self._save_session_metrics(session)
        
        # Удаляем из активных
        del self.active_sessions[session_id]
    
    def track_interaction(self, user_id: int, session_id: str, product_id: str, 
                         product_category: str, interaction_type: str, 
                         additional_data: Dict[str, Any] = None):
        """Отслеживает взаимодействие с продуктом"""
        
        interaction = UserInteraction(
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            product_category=product_category,
            interaction_type=interaction_type,
            timestamp=time.time(),
            additional_data=additional_data or {}
        )
        
        # Сохраняем взаимодействие
        self._save_interaction(interaction)
        
        # Обновляем метрики активного сеанса
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            if interaction_type == "click":
                session.products_clicked += 1
            elif interaction_type == "add_to_cart":
                session.products_added_to_cart += 1
    
    def get_session_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получает статистику сеансов за период"""
        
        cutoff_time = time.time() - (days * 24 * 3600)
        sessions = self._load_recent_sessions(cutoff_time)
        
        if not sessions:
            return {"error": "No sessions found"}
        
        total_sessions = len(sessions)
        completed_sessions = [s for s in sessions if s.completion_rate >= 0.99]
        
        # Основные метрики
        completion_rate = len(completed_sessions) / total_sessions if total_sessions > 0 else 0
        avg_time_to_complete = sum(s.time_to_complete for s in completed_sessions if s.time_to_complete) / len(completed_sessions) if completed_sessions else 0
        avg_steps_completed = sum(s.steps_completed for s in sessions) / total_sessions
        
        # Метрики по потокам
        flow_stats = {}
        for flow_type in ["detailed_palette", "detailed_skincare"]:
            flow_sessions = [s for s in sessions if s.flow_type == flow_type]
            if flow_sessions:
                flow_completed = [s for s in flow_sessions if s.completion_rate >= 0.99]
                flow_stats[flow_type] = {
                    "total_sessions": len(flow_sessions),
                    "completion_rate": len(flow_completed) / len(flow_sessions),
                    "avg_time": sum(s.time_to_complete for s in flow_completed if s.time_to_complete) / len(flow_completed) if flow_completed else 0
                }
        
        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "completion_rate": completion_rate,
            "avg_time_to_complete_minutes": avg_time_to_complete / 60,
            "avg_steps_completed": avg_steps_completed,
            "flow_breakdown": flow_stats
        }
    
    def get_product_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Получает метрики по продуктам"""
        
        cutoff_time = time.time() - (days * 24 * 3600)
        interactions = self._load_recent_interactions(cutoff_time)
        
        if not interactions:
            return {"error": "No interactions found"}
        
        # Подсчет по типам взаимодействий
        views = [i for i in interactions if i.interaction_type == "view"]
        clicks = [i for i in interactions if i.interaction_type == "click"]
        cart_adds = [i for i in interactions if i.interaction_type == "add_to_cart"]
        
        # CTR (Click-Through Rate)
        ctr = len(clicks) / len(views) if views else 0
        
        # Add-to-Cart Rate
        cart_rate = len(cart_adds) / len(clicks) if clicks else 0
        
        # Популярные категории
        category_stats = {}
        for interaction in interactions:
            category = interaction.product_category
            if category not in category_stats:
                category_stats[category] = {"views": 0, "clicks": 0, "cart_adds": 0}
            
            category_stats[category][f"{interaction.interaction_type}s"] += 1
        
        # Добавляем CTR по категориям
        for category, stats in category_stats.items():
            stats["ctr"] = stats["clicks"] / stats["views"] if stats["views"] > 0 else 0
            stats["cart_rate"] = stats["cart_adds"] / stats["clicks"] if stats["clicks"] > 0 else 0
        
        return {
            "period_days": days,
            "total_views": len(views),
            "total_clicks": len(clicks),
            "total_cart_adds": len(cart_adds),
            "overall_ctr": ctr,
            "overall_cart_rate": cart_rate,
            "category_breakdown": category_stats
        }
    
    def get_oos_impact(self, days: int = 7) -> Dict[str, Any]:
        """Анализирует влияние OOS (Out of Stock) на метрики"""
        
        cutoff_time = time.time() - (days * 24 * 3600)
        sessions = self._load_recent_sessions(cutoff_time)
        
        if not sessions:
            return {"error": "No sessions found"}
        
        sessions_with_oos = [s for s in sessions if s.oos_products_encountered > 0]
        sessions_without_oos = [s for s in sessions if s.oos_products_encountered == 0]
        
        def calc_avg_completion(session_list):
            return sum(s.completion_rate for s in session_list) / len(session_list) if session_list else 0
        
        oos_completion = calc_avg_completion(sessions_with_oos)
        no_oos_completion = calc_avg_completion(sessions_without_oos)
        
        return {
            "period_days": days,
            "sessions_with_oos": len(sessions_with_oos),
            "sessions_without_oos": len(sessions_without_oos),
            "oos_completion_rate": oos_completion,
            "no_oos_completion_rate": no_oos_completion,
            "oos_impact": no_oos_completion - oos_completion,
            "avg_oos_products_per_session": sum(s.oos_products_encountered for s in sessions_with_oos) / len(sessions_with_oos) if sessions_with_oos else 0
        }
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Генерирует ежедневный отчет метрик"""
        
        session_stats = self.get_session_stats(1)  # За сегодня
        product_stats = self.get_product_metrics(1)
        oos_stats = self.get_oos_impact(1)
        
        report = {
            "date": time.strftime("%Y-%m-%d"),
            "session_metrics": session_stats,
            "product_metrics": product_stats,
            "oos_metrics": oos_stats,
            "generated_at": time.time()
        }
        
        # Сохраняем отчет
        daily_file = self.metrics_dir / f"daily_report_{time.strftime('%Y%m%d')}.json"
        with open(daily_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def _save_interaction(self, interaction: UserInteraction):
        """Сохраняет взаимодействие в JSONL файл"""
        with open(self.interactions_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(interaction), ensure_ascii=False) + '\n')
    
    def _save_session_metrics(self, session: SessionMetrics):
        """Сохраняет метрики сеанса в JSONL файл"""
        with open(self.sessions_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(session), ensure_ascii=False) + '\n')
    
    def _load_recent_sessions(self, cutoff_time: float) -> List[SessionMetrics]:
        """Загружает сеансы за период"""
        sessions = []
        
        if not self.sessions_file.exists():
            return sessions
        
        with open(self.sessions_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get('started_at', 0) >= cutoff_time:
                        sessions.append(SessionMetrics(**data))
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return sessions
    
    def _load_recent_interactions(self, cutoff_time: float) -> List[UserInteraction]:
        """Загружает взаимодействия за период"""
        interactions = []
        
        if not self.interactions_file.exists():
            return interactions
        
        with open(self.interactions_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get('timestamp', 0) >= cutoff_time:
                        interactions.append(UserInteraction(**data))
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return interactions


# Глобальный трекер метрик
_metrics_tracker = None

def get_metrics_tracker() -> BusinessMetricsTracker:
    """Получить глобальный экземпляр трекера метрик"""
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = BusinessMetricsTracker()
    return _metrics_tracker


if __name__ == "__main__":
    # Тест системы метрик
    print("📈 BUSINESS METRICS TEST")
    print("=" * 40)
    
    tracker = BusinessMetricsTracker("data/test_metrics")
    
    # Имитация сеанса
    session_id = tracker.start_session(12345, "detailed_palette", 8)
    print(f"Started session: {session_id}")
    
    # Имитация прогресса
    for step in range(1, 9):
        tracker.update_session_progress(session_id, step)
        
        # Имитация просмотра продуктов
        if step >= 7:  # На последних шагах показываем продукты
            for i in range(3):
                product_id = f"product_{i}"
                tracker.track_interaction(12345, session_id, product_id, "foundation", "view")
                
                if i == 0:  # Первый продукт кликаем
                    tracker.track_interaction(12345, session_id, product_id, "foundation", "click")
    
    # Завершение сеанса
    test_products = [
        {"id": "product_0", "in_stock": True},
        {"id": "product_1", "in_stock": False},
        {"id": "product_2", "in_stock": True}
    ]
    tracker.complete_session(session_id, test_products)
    
    # Получение статистики
    print("\nSession Stats:")
    stats = tracker.get_session_stats(1)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nProduct Metrics:")
    product_metrics = tracker.get_product_metrics(1)
    for key, value in product_metrics.items():
        print(f"  {key}: {value}")
    
    print("\nOOS Impact:")
    oos_impact = tracker.get_oos_impact(1)
    for key, value in oos_impact.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Business metrics test completed!")





