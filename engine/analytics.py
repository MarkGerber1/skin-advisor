#!/usr/bin/env python3
"""
📊 Analytics - Система аналитики ключевых событий пользовательской воронки
Отслеживает полный путь: тест → рекомендации → корзина → покупка
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from engine.business_metrics import get_metrics_tracker

# Настройка логгера для аналитики
logger = logging.getLogger("analytics")
logger.setLevel(logging.INFO)

# Если хэндлер не настроен, добавляем вывод в консоль
if not logger.handlers:
    handler = logging.StreamHandler()
    # Исправленный formatter без [err] префикса
    formatter = logging.Formatter("%(asctime)s | ANALYTICS | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@dataclass
class AnalyticsEvent:
    """Структура события аналитики"""

    event_type: str
    user_id: int
    timestamp: float
    payload: Dict[str, Any]
    session_id: Optional[str] = None


class AnalyticsTracker:
    """Трекер аналитики ключевых событий воронки"""

    def __init__(self, analytics_dir: str = "data/analytics"):
        self.analytics_dir = Path(analytics_dir)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)

        # Файл для хранения событий аналитики
        self.events_file = self.analytics_dir / "events.jsonl"

        # Интеграция с существующей системой метрик
        self.metrics_tracker = get_metrics_tracker()

        # События инлайн-потока подбора ухода
        self.skincare_events = {
            "recommendations_viewed": "branch=skincare",
            "category_opened": "name",
            "product_opened": "pid,source",
            "variant_selected": "pid,vid",
            "product_added_to_cart": "pid,vid,source,price",
            "oos_shown": "pid",
            "alternatives_shown": "pid,base_category,alternatives_count",
            "error_shown": "code,place",
        }

    def emit(
        self,
        event_type: str,
        user_id: int,
        payload: Dict[str, Any] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Отправить событие аналитики

        Args:
            event_type: Тип события (user_started_test, product_added_to_cart, etc.)
            user_id: ID пользователя
            payload: Данные события
            session_id: ID сессии (опционально)
        """
        try:
            event = AnalyticsEvent(
                event_type=event_type,
                user_id=user_id,
                timestamp=time.time(),
                payload=payload or {},
                session_id=session_id,
            )

            # Сохраняем в файл событий
            self._save_event(event)

            # Логируем событие
            logger.info(
                f"Analytics: {event_type}",
                extra={
                    "event_type": event_type,
                    "user_id": user_id,
                    "payload": payload,
                    "session_id": session_id,
                },
            )

            # Интегрируем с существующей системой метрик если применимо
            self._integrate_with_business_metrics(event)

        except Exception as e:
            logger.error(f"Failed to emit analytics event {event_type}: {e}")

    def user_started_test(
        self, user_id: int, test_type: str, session_id: Optional[str] = None
    ) -> None:
        """Пользователь начал тест (palette|skin)"""
        self.emit(
            "user_started_test",
            user_id,
            {"test_type": test_type, "started_at": time.time()},
            session_id,
        )

    def user_completed_test(
        self,
        user_id: int,
        test_type: str,
        duration_seconds: Optional[float] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Пользователь завершил тест"""
        payload = {"test_type": test_type, "completed_at": time.time()}
        if duration_seconds is not None:
            payload["duration_seconds"] = duration_seconds

        self.emit("user_completed_test", user_id, payload, session_id)

    def recommendations_viewed(
        self, user_id: int, branch: str, products_count: int = 0, session_id: Optional[str] = None
    ) -> None:
        """Пользователь просмотрел рекомендации (makeup|skincare)"""
        self.emit(
            "recommendations_viewed",
            user_id,
            {"branch": branch, "products_count": products_count, "viewed_at": time.time()},
            session_id,
        )

    def product_added_to_cart(
        self,
        user_id: int,
        product_id: str,
        variant_id: Optional[str] = None,
        source: Optional[str] = None,
        price: Optional[float] = None,
        category: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Товар добавлен в корзину"""
        payload = {"product_id": product_id, "added_at": time.time()}

        if variant_id:
            payload["variant_id"] = variant_id
        if source:
            payload["source"] = source
        if price is not None:
            payload["price"] = price
        if category:
            payload["category"] = category

        self.emit("product_added_to_cart", user_id, payload, session_id)

    def cart_viewed(
        self,
        user_id: int,
        items_count: int,
        total_value: float,
        currency: str = "RUB",
        session_id: Optional[str] = None,
    ) -> None:
        """Пользователь просмотрел корзину"""
        self.emit(
            "cart_viewed",
            user_id,
            {
                "items_count": items_count,
                "total_value": total_value,
                "currency": currency,
                "viewed_at": time.time(),
            },
            session_id,
        )

    def cart_item_updated(
        self,
        user_id: int,
        product_id: str,
        variant_id: Optional[str] = None,
        qty_before: int = 0,
        qty_after: int = 0,
        session_id: Optional[str] = None,
    ) -> None:
        """Количество товара в корзине изменено"""
        payload = {
            "product_id": product_id,
            "qty_before": qty_before,
            "qty_after": qty_after,
            "updated_at": time.time(),
        }

        if variant_id:
            payload["variant_id"] = variant_id

        self.emit("cart_item_updated", user_id, payload, session_id)

    def cart_item_removed(
        self,
        user_id: int,
        product_id: str,
        variant_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Товар удален из корзины"""
        payload = {"product_id": product_id, "removed_at": time.time()}

        if variant_id:
            payload["variant_id"] = variant_id

        self.emit("cart_item_removed", user_id, payload, session_id)

    def checkout_clicked(
        self,
        user_id: int,
        items_count: int,
        total_value: float,
        currency: str = "RUB",
        session_id: Optional[str] = None,
    ) -> None:
        """Пользователь нажал на оформление заказа"""
        self.emit(
            "checkout_clicked",
            user_id,
            {
                "items_count": items_count,
                "total_value": total_value,
                "currency": currency,
                "clicked_at": time.time(),
            },
            session_id,
        )

    def external_checkout_opened(
        self,
        user_id: int,
        partner: str,
        product_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Открыт внешний сайт партнера для покупки"""
        payload = {"partner": partner, "opened_at": time.time()}

        if product_id:
            payload["product_id"] = product_id

        self.emit("external_checkout_opened", user_id, payload, session_id)

    def error_shown(
        self,
        user_id: int,
        error_code: str,
        place: str,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Пользователю показана ошибка"""
        payload = {"error_code": error_code, "place": place, "shown_at": time.time()}

        if error_message:
            payload["error_message"] = error_message

        self.emit("error_shown", user_id, payload, session_id)

    def page_viewed(
        self,
        user_id: int,
        page_name: str,
        source: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Пользователь просмотрел страницу/экран"""
        payload = {"page_name": page_name, "viewed_at": time.time()}

        if source:
            payload["source"] = source

        self.emit("page_viewed", user_id, payload, session_id)

    def user_action(
        self,
        user_id: int,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Универсальное действие пользователя"""
        payload = {"action": action, "performed_at": time.time()}

        if context:
            payload["context"] = context

        self.emit("user_action", user_id, payload, session_id)

    def get_events_summary(self, days: int = 7) -> Dict[str, Any]:
        """Получить сводку событий за период"""
        cutoff_time = time.time() - (days * 24 * 3600)
        events = self._load_recent_events(cutoff_time)

        if not events:
            return {"error": "No events found", "period_days": days}

        # Подсчет по типам событий
        event_counts = {}
        user_counts = set()

        for event in events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            user_counts.add(event.user_id)

        # Воронка конверсии
        funnel_events = {
            "test_starts": event_counts.get("user_started_test", 0),
            "test_completions": event_counts.get("user_completed_test", 0),
            "recommendations_views": event_counts.get("recommendations_viewed", 0),
            "cart_additions": event_counts.get("product_added_to_cart", 0),
            "cart_views": event_counts.get("cart_viewed", 0),
            "checkout_clicks": event_counts.get("checkout_clicked", 0),
            "external_checkouts": event_counts.get("external_checkout_opened", 0),
        }

        # Расчет конверсий
        test_completion_rate = (
            (funnel_events["test_completions"] / funnel_events["test_starts"])
            if funnel_events["test_starts"] > 0
            else 0
        )
        cart_conversion_rate = (
            (funnel_events["cart_additions"] / funnel_events["recommendations_views"])
            if funnel_events["recommendations_views"] > 0
            else 0
        )
        checkout_conversion_rate = (
            (funnel_events["checkout_clicks"] / funnel_events["cart_views"])
            if funnel_events["cart_views"] > 0
            else 0
        )

        return {
            "period_days": days,
            "total_events": len(events),
            "unique_users": len(user_counts),
            "event_breakdown": event_counts,
            "funnel_metrics": {
                **funnel_events,
                "test_completion_rate": test_completion_rate,
                "cart_conversion_rate": cart_conversion_rate,
                "checkout_conversion_rate": checkout_conversion_rate,
            },
        }

    def _save_event(self, event: AnalyticsEvent) -> None:
        """Сохранить событие в JSONL файл"""
        try:
            with open(self.events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to save analytics event: {e}")

    def _load_recent_events(self, cutoff_time: float) -> List[AnalyticsEvent]:
        """Загрузить события за период"""
        events = []

        if not self.events_file.exists():
            return events

        try:
            with open(self.events_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if data.get("timestamp", 0) >= cutoff_time:
                            events.append(AnalyticsEvent(**data))
                    except (json.JSONDecodeError, TypeError):
                        continue
        except Exception as e:
            logger.error(f"Failed to load analytics events: {e}")

        return events

    def _integrate_with_business_metrics(self, event: AnalyticsEvent) -> None:
        """Интеграция с существующей системой бизнес-метрик"""
        try:
            # Мапим события аналитики на существующие метрики
            if event.event_type == "product_added_to_cart":
                # Используем существующий track_event для корзины
                self.metrics_tracker.track_event(
                    "cart_add_success",
                    event.user_id,
                    {
                        "product_id": event.payload.get("product_id"),
                        "category": event.payload.get("category", "unknown"),
                        "price": event.payload.get("price", 0),
                        "source": event.payload.get("source"),
                    },
                )

            elif event.event_type == "recommendations_viewed":
                # Создаем взаимодействие просмотра
                session_id = event.session_id or f"analytics_{event.user_id}_{int(event.timestamp)}"
                self.metrics_tracker.track_interaction(
                    user_id=event.user_id,
                    session_id=session_id,
                    product_id="recommendations_page",
                    product_category=event.payload.get("branch", "unknown"),
                    interaction_type="view",
                    additional_data=event.payload,
                )

            elif event.event_type == "external_checkout_opened":
                # Отслеживаем как клик по партнерской ссылке
                session_id = event.session_id or f"analytics_{event.user_id}_{int(event.timestamp)}"
                self.metrics_tracker.track_interaction(
                    user_id=event.user_id,
                    session_id=session_id,
                    product_id=event.payload.get("product_id", "unknown"),
                    product_category="checkout",
                    interaction_type="click",
                    additional_data=event.payload,
                )

        except Exception as e:
            logger.warning(f"Failed to integrate with business metrics: {e}")


# Глобальный экземпляр трекера аналитики
_analytics_tracker = None


def get_analytics_tracker() -> AnalyticsTracker:
    """Получить глобальный экземпляр трекера аналитики"""
    global _analytics_tracker
    if _analytics_tracker is None:
        _analytics_tracker = AnalyticsTracker()
    return _analytics_tracker


# Удобные функции для быстрого доступа
def emit_event(
    event_type: str, user_id: int, payload: Dict[str, Any] = None, session_id: Optional[str] = None
) -> None:
    """Быстрая отправка события аналитики"""
    tracker = get_analytics_tracker()
    tracker.emit(event_type, user_id, payload, session_id)


def track_user_started_test(user_id: int, test_type: str, session_id: Optional[str] = None) -> None:
    """Отследить начало теста"""
    tracker = get_analytics_tracker()
    tracker.user_started_test(user_id, test_type, session_id)


def track_user_completed_test(
    user_id: int,
    test_type: str,
    duration_seconds: Optional[float] = None,
    session_id: Optional[str] = None,
) -> None:
    """Отследить завершение теста"""
    tracker = get_analytics_tracker()
    tracker.user_completed_test(user_id, test_type, duration_seconds, session_id)


def track_recommendations_viewed(
    user_id: int, branch: str, products_count: int = 0, session_id: Optional[str] = None
) -> None:
    """Отследить просмотр рекомендаций"""
    tracker = get_analytics_tracker()
    tracker.recommendations_viewed(user_id, branch, products_count, session_id)


def track_cart_event(event_type: str, user_id: int, **kwargs) -> None:
    """Отследить событие корзины"""
    tracker = get_analytics_tracker()
    method_name = event_type.replace("cart_", "").replace("product_added_to_", "product_added_to_")


# События инлайн-потока подбора ухода
def track_skincare_recommendations_viewed(user_id: int, session_id: Optional[str] = None) -> None:
    """Отследить просмотр подбора ухода"""
    tracker = get_analytics_tracker()
    tracker.emit("recommendations_viewed", user_id, {"branch": "skincare"}, session_id)


def track_category_opened(
    user_id: int, category_name: str, session_id: Optional[str] = None
) -> None:
    """Отследить открытие категории товаров"""
    tracker = get_analytics_tracker()
    tracker.emit("category_opened", user_id, {"name": category_name}, session_id)


def track_product_opened(
    user_id: int, product_id: str, source: str, session_id: Optional[str] = None
) -> None:
    """Отследить открытие карточки товара"""
    tracker = get_analytics_tracker()
    tracker.emit("product_opened", user_id, {"pid": product_id, "source": source}, session_id)


def track_variant_selected(
    user_id: int, product_id: str, variant_id: str, session_id: Optional[str] = None
) -> None:
    """Отследить выбор варианта товара"""
    tracker = get_analytics_tracker()
    tracker.emit("variant_selected", user_id, {"pid": product_id, "vid": variant_id}, session_id)


def track_oos_shown(user_id: int, product_id: str, session_id: Optional[str] = None) -> None:
    """Отследить показ товара 'нет в наличии'"""
    tracker = get_analytics_tracker()
    tracker.emit("oos_shown", user_id, {"pid": product_id}, session_id)


def track_alternatives_shown(
    user_id: int,
    product_id: str,
    base_category: str,
    alternatives_count: int,
    session_id: Optional[str] = None,
) -> None:
    """Отследить показ альтернатив для товара"""
    tracker = get_analytics_tracker()
    tracker.emit(
        "alternatives_shown",
        user_id,
        {
            "pid": product_id,
            "base_category": base_category,
            "alternatives_count": alternatives_count,
        },
        session_id,
    )


def track_skincare_error(
    user_id: int, error_code: str, place: str, session_id: Optional[str] = None
) -> None:
    """Отследить ошибку в инлайн-потоке ухода"""
    tracker = get_analytics_tracker()
    tracker.emit("error_shown", user_id, {"code": error_code, "place": place}, session_id)


if __name__ == "__main__":
    # Тест системы аналитики
    print("📊 ANALYTICS TEST")
    print("=" * 40)

    tracker = AnalyticsTracker("data/test_analytics")

    # Имитация пользовательского пути
    user_id = 12345
    session_id = "test_session_123"

    # Пользователь начал тест
    tracker.user_started_test(user_id, "palette", session_id)

    # Завершил тест
    tracker.user_completed_test(user_id, "palette", 120.5, session_id)

    # Просмотрел рекомендации
    tracker.recommendations_viewed(user_id, "makeup", 5, session_id)

    # Добавил товар в корзину
    tracker.product_added_to_cart(
        user_id, "product_123", "shade_01", "goldapple", 2500.0, "foundation", session_id
    )

    # Просмотрел корзину
    tracker.cart_viewed(user_id, 1, 2500.0, "RUB", session_id)

    # Нажал оформить
    tracker.checkout_clicked(user_id, 1, 2500.0, "RUB", session_id)

    # Открыл внешний сайт
    tracker.external_checkout_opened(user_id, "goldapple", "product_123", session_id)

    # Получение статистики
    print("\nAnalytics Summary:")
    summary = tracker.get_events_summary(1)
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("\n✅ Analytics test completed!")
