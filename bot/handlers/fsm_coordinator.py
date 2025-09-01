"""
🎯 FSM Coordinator - Управление состояниями и предотвращение параллельных потоков
Обеспечивает устойчивость UX и восстановление сеансов
"""

import json
import time
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State

@dataclass
class SessionData:
    """Данные пользовательского сеанса"""
    user_id: int
    current_flow: str  # "palette", "skincare", "detailed_palette", "detailed_skincare", None
    current_step: str  # Текущий State
    flow_data: Dict[str, Any]  # Промежуточные данные
    started_at: float  # timestamp
    last_activity: float  # timestamp
    step_count: int
    flow_progress: float  # 0.0 - 1.0

class FSMCoordinator:
    """Координатор FSM состояний для предотвращения параллельных потоков"""
    
    def __init__(self):
        self._active_sessions: Dict[int, SessionData] = {}
        self._session_timeout = 1800  # 30 минут
        
        # Определение потоков и их шагов
        self.flow_definitions = {
            "palette": {
                "name": "Цветотип",
                "steps": ["A1_UNDERTONE", "A2_VALUE", "A3_HAIR", "A4_BROWS", "A5_EYES", "A6_CONTRAST", "A7_CONFIRM", "A8_REPORT"],
                "description": "Определение вашего цветотипа внешности",
                "duration_estimate": "5-7 минут"
            },
            "skincare": {
                "name": "Уход за кожей", 
                "steps": ["B1_TYPE", "B2_CONCERNS", "B3_CONFIRM", "B4_REPORT"],
                "description": "Подбор ухода под ваш тип кожи",
                "duration_estimate": "3-5 минут"
            },
            "detailed_palette": {
                "name": "Детальный цветотип",
                "steps": ["Q1_HAIR_COLOR", "Q2_EYE_COLOR", "Q3_SKIN_UNDERTONE", "Q4_CONTRAST", "Q5_SUN_REACTION", "Q6_FACE_SHAPE", "Q7_MAKEUP_STYLE", "Q8_LIP_COLOR", "RESULT"],
                "description": "Углубленный анализ вашего цветотипа",
                "duration_estimate": "10-12 минут"
            },
            "detailed_skincare": {
                "name": "Детальный уход",
                "steps": ["Q1_TIGHTNESS", "Q2_SUN_REACTION", "Q3_IMPERFECTIONS", "Q4_EYE_AREA", "Q5_COUPEROSE", "Q6_CURRENT_CARE", "Q7_ALLERGIES", "Q8_DESIRED_EFFECT", "RESULT"],
                "description": "Комплексная диагностика кожи",
                "duration_estimate": "10-15 минут"
            }
        }
    
    async def can_start_flow(self, user_id: int, requested_flow: str) -> Tuple[bool, Optional[str]]:
        """Проверяет можно ли запустить новый поток"""
        
        # Очистка истекших сеансов
        await self._cleanup_expired_sessions()
        
        # Проверка активного сеанса
        if user_id in self._active_sessions:
            active_session = self._active_sessions[user_id]
            
            # Если запрашивается тот же поток - разрешаем (продолжение)
            if active_session.current_flow == requested_flow:
                return True, None
            
            # Иначе предупреждаем о конфликте
            flow_info = self.flow_definitions.get(active_session.current_flow, {})
            active_flow_name = flow_info.get("name", active_session.current_flow)
            
            conflict_message = (
                f"⚠️ У вас уже запущен тест: **{active_flow_name}**\n\n"
                f"🔄 Прогресс: {active_session.flow_progress:.0%} ({active_session.step_count} шагов)\n"
                f"⏱️ Активен: {self._format_time_ago(active_session.last_activity)}\n\n"
                f"Выберите действие:\n"
                f"• **Продолжить** текущий тест\n"
                f"• **Отменить** и начать новый\n"
                f"• **Домой** в главное меню"
            )
            
            return False, conflict_message
        
        return True, None
    
    async def start_flow(self, user_id: int, flow_name: str, state: FSMContext) -> SessionData:
        """Начинает новый поток FSM"""
        
        # Очистка предыдущего сеанса если есть
        if user_id in self._active_sessions:
            await state.clear()
        
        # Создание нового сеанса
        session = SessionData(
            user_id=user_id,
            current_flow=flow_name,
            current_step="",
            flow_data={},
            started_at=time.time(),
            last_activity=time.time(),
            step_count=0,
            flow_progress=0.0
        )
        
        self._active_sessions[user_id] = session
        return session
    
    async def update_step(self, user_id: int, step_name: str, step_data: Dict[str, Any] = None) -> Optional[SessionData]:
        """Обновляет текущий шаг в сеансе"""
        
        if user_id not in self._active_sessions:
            return None
        
        session = self._active_sessions[user_id]
        session.current_step = step_name
        session.last_activity = time.time()
        session.step_count += 1
        
        # Обновление данных шага
        if step_data:
            session.flow_data.update(step_data)
        
        # Вычисление прогресса
        flow_def = self.flow_definitions.get(session.current_flow, {})
        steps = flow_def.get("steps", [])
        if steps and step_name in steps:
            step_index = steps.index(step_name)
            session.flow_progress = (step_index + 1) / len(steps)
        
        return session
    
    async def complete_flow(self, user_id: int) -> Optional[SessionData]:
        """Завершает поток и удаляет сеанс"""
        
        if user_id not in self._active_sessions:
            return None
        
        session = self._active_sessions[user_id]
        session.flow_progress = 1.0
        
        # Удаляем из активных сеансов
        completed_session = self._active_sessions.pop(user_id)
        
        return completed_session
    
    async def abandon_flow(self, user_id: int, state: FSMContext) -> bool:
        """Отменяет текущий поток"""
        
        if user_id not in self._active_sessions:
            return False
        
        # Очистка состояния и сеанса
        await state.clear()
        del self._active_sessions[user_id]
        
        return True
    
    async def get_session(self, user_id: int) -> Optional[SessionData]:
        """Получает текущий сеанс пользователя"""
        await self._cleanup_expired_sessions()
        return self._active_sessions.get(user_id)
    
    async def get_recovery_message(self, user_id: int) -> Optional[str]:
        """Генерирует сообщение для восстановления сеанса"""
        
        session = await self.get_session(user_id)
        if not session:
            return None
        
        flow_def = self.flow_definitions.get(session.current_flow, {})
        flow_name = flow_def.get("name", session.current_flow)
        
        time_ago = self._format_time_ago(session.last_activity)
        
        recovery_message = (
            f"🔄 **Восстановление сеанса**\n\n"
            f"📋 Тест: **{flow_name}**\n"
            f"📊 Прогресс: {session.flow_progress:.0%} ({session.step_count} шагов)\n"
            f"⏱️ Последняя активность: {time_ago}\n\n"
            f"💡 *{flow_def.get('description', '')}*\n\n"
            f"Хотите продолжить с места остановки?"
        )
        
        return recovery_message
    
    def get_step_hint(self, flow_name: str, step_name: str) -> Optional[str]:
        """Получает подсказку для текущего шага"""
        
        hints = {
            # Palette Flow hints
            "A1_UNDERTONE": "🔍 Посмотрите на внутреннюю сторону запястья при естественном освещении. Это поможет определить ваш подтон.",
            "A2_VALUE": "💡 Светлота определяет, насколько яркими или приглушенными должны быть ваши цвета.",
            "A3_HAIR": "🎨 Естественный цвет волос влияет на выбор оттенков макияжа и одежды.",
            "A4_BROWS": "✨ Форма и цвет бровей помогают гармонично завершить образ.",
            "A5_EYES": "👁️ Цвет глаз определяет наиболее выигрышные оттенки теней и подводки.",
            "A6_CONTRAST": "⚡ Контрастность влияет на интенсивность макияжа и аксессуаров.",
            
            # Skincare Flow hints  
            "B1_TYPE": "🧴 Тип кожи - основа для выбора правильного ухода.",
            "B2_CONCERNS": "🎯 Проблемы кожи помогут подобрать целевые средства с нужными активами.",
            "B3_CONFIRM": "✅ Проверьте данные перед формированием рекомендаций.",
            
            # Detailed Palette hints
            "Q1_HAIR_COLOR": "💇 Учитываем только натуральный цвет волос без окрашивания.",
            "Q2_EYE_COLOR": "👀 Основной цвет радужки, не учитывая вкрапления.",
            "Q3_SKIN_UNDERTONE": "🩸 Вены на запястье: синие = холодный, зеленые = теплый подтон.",
            "Q4_CONTRAST": "🔄 Разница между цветом волос, глаз и кожи.",
            "Q5_SUN_REACTION": "☀️ Реакция на солнце указывает на чувствительность кожи.",
            
            # Detailed Skincare hints
            "Q1_TIGHTNESS": "💧 Ощущения после очищения говорят о потребности в увлажнении.",
            "Q2_SUN_REACTION": "🌞 Реакция на UV помогает подобрать правильный SPF.",
            "Q3_IMPERFECTIONS": "🔍 Основные проблемы определяют целевые активные ингредиенты.",
            "Q4_EYE_AREA": "👁️ Деликатная зона требует специального ухода.",
        }
        
        return hints.get(step_name)
    
    async def _cleanup_expired_sessions(self):
        """Очищает истекшие сеансы"""
        current_time = time.time()
        expired_users = []
        
        for user_id, session in self._active_sessions.items():
            if current_time - session.last_activity > self._session_timeout:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self._active_sessions[user_id]
            
    async def force_cleanup_expired_sessions(self):
        """Принудительная очистка истекших сессий с более агрессивным timeout"""
        current_time = time.time()
        expired_users = []
        
        # Более агрессивный timeout: 5 минут (300 секунд)
        aggressive_timeout = 300
        
        for user_id, session in self._active_sessions.items():
            if current_time - session.last_activity > aggressive_timeout:
                expired_users.append(user_id)
                print(f"🧹 Force cleaning expired session for user {user_id} (inactive for {current_time - session.last_activity:.0f}s)")
        
        for user_id in expired_users:
            del self._active_sessions[user_id]
            
        if expired_users:
            print(f"🧹 Cleaned {len(expired_users)} expired sessions")
            
    async def clear_user_session(self, user_id: int):
        """Принудительная очистка сессии конкретного пользователя"""
        if user_id in self._active_sessions:
            del self._active_sessions[user_id]
            print(f"🧹 Manually cleared session for user {user_id}")
    
    def _format_time_ago(self, timestamp: float) -> str:
        """Форматирует время 'назад'"""
        seconds_ago = time.time() - timestamp
        
        if seconds_ago < 60:
            return "только что"
        elif seconds_ago < 3600:
            minutes = int(seconds_ago / 60)
            return f"{minutes} мин назад"
        else:
            hours = int(seconds_ago / 3600)
            return f"{hours} ч назад"
    
    def get_active_sessions_count(self) -> int:
        """Возвращает количество активных сеансов"""
        return len(self._active_sessions)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Статистика сеансов для мониторинга"""
        if not self._active_sessions:
            return {"active_sessions": 0}
        
        flow_counts = {}
        total_progress = 0
        
        for session in self._active_sessions.values():
            flow = session.current_flow
            flow_counts[flow] = flow_counts.get(flow, 0) + 1
            total_progress += session.flow_progress
        
        avg_progress = total_progress / len(self._active_sessions)
        
        return {
            "active_sessions": len(self._active_sessions),
            "flow_distribution": flow_counts,
            "average_progress": avg_progress,
            "total_steps_completed": sum(s.step_count for s in self._active_sessions.values())
        }


# Глобальный экземпляр координатора
_coordinator = None

def get_fsm_coordinator() -> FSMCoordinator:
    """Получить глобальный экземпляр FSM координатора"""
    global _coordinator
    if _coordinator is None:
        _coordinator = FSMCoordinator()
    return _coordinator


# Декораторы для интеграции с handlers
def require_single_flow(flow_name: str):
    """Декоратор для защиты от параллельных потоков"""
    def decorator(handler_func):
        async def wrapper(event, state: FSMContext, *args, **kwargs):
            coordinator = get_fsm_coordinator()
            user_id = event.from_user.id
            
            can_start, conflict_msg = await coordinator.can_start_flow(user_id, flow_name)
            
            if not can_start:
                if isinstance(event, Message):
                    await event.answer(conflict_msg)
                elif isinstance(event, CallbackQuery):
                    await event.message.edit_text(conflict_msg)
                return
            
            # Продолжаем выполнение handler'а
            return await handler_func(event, state, *args, **kwargs)
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Тест координатора
    import asyncio
    
    async def test_coordinator():
        coordinator = FSMCoordinator()
        
        # Тест создания сеанса
        class MockState:
            async def clear(self): pass
        
        session = await coordinator.start_flow(12345, "palette", MockState())
        print(f"Created session: {session.current_flow}")
        
        # Тест обновления шага
        await coordinator.update_step(12345, "A1_UNDERTONE", {"undertone": "warm"})
        session = await coordinator.get_session(12345)
        print(f"Progress: {session.flow_progress:.1%}")
        
        # Тест подсказки
        hint = coordinator.get_step_hint("palette", "A1_UNDERTONE")
        print(f"Hint: {hint}")
        
        # Тест статистики
        stats = coordinator.get_session_stats()
        print(f"Stats: {stats}")
    
    asyncio.run(test_coordinator())






