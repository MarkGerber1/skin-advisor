"""
💬 Step Hints Integration - Подсказки для улучшения UX
Интегрируется с FSM Coordinator для показа контекстных подсказок
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .fsm_coordinator import get_fsm_coordinator

def add_step_hint_to_message(flow_name: str, step_name: str, base_message: str) -> str:
    """Добавляет подсказку к сообщению шага"""
    
    coordinator = get_fsm_coordinator()
    hint = coordinator.get_step_hint(flow_name, step_name)
    
    if hint:
        return f"{base_message}\n\n💡 {hint}"
    
    return base_message

def create_step_keyboard_with_hint(base_keyboard: InlineKeyboardMarkup, 
                                  flow_name: str, 
                                  step_name: str) -> InlineKeyboardMarkup:
    """Добавляет кнопку подсказки к существующей клавиатуре"""
    
    coordinator = get_fsm_coordinator()
    hint = coordinator.get_step_hint(flow_name, step_name)
    
    if not hint:
        return base_keyboard
    
    # Копируем существующие кнопки
    new_keyboard = []
    for row in base_keyboard.inline_keyboard:
        new_keyboard.append(row)
    
    # Добавляем кнопку подсказки
    hint_button = InlineKeyboardButton(
        text="💡 Подсказка",
        callback_data=f"hint:{flow_name}:{step_name}"
    )
    new_keyboard.append([hint_button])
    
    return InlineKeyboardMarkup(inline_keyboard=new_keyboard)

def get_progress_indicator(flow_name: str, step_name: str) -> str:
    """Возвращает индикатор прогресса для шага"""
    
    coordinator = get_fsm_coordinator()
    flow_def = coordinator.flow_definitions.get(flow_name, {})
    steps = flow_def.get("steps", [])
    
    if not steps or step_name not in steps:
        return ""
    
    current_step = steps.index(step_name) + 1
    total_steps = len(steps)
    progress_percent = int((current_step / total_steps) * 100)
    
    # Создание визуального прогресса
    filled_blocks = int(progress_percent / 10)
    progress_bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
    
    return f"📊 Прогресс: {current_step}/{total_steps} ({progress_percent}%) {progress_bar}"

def format_step_message(flow_name: str, step_name: str, base_message: str, 
                       show_progress: bool = True, show_hint: bool = True) -> str:
    """Форматирует сообщение шага с прогрессом и подсказкой"""
    
    result = base_message
    
    # Добавляем индикатор прогресса
    if show_progress:
        progress = get_progress_indicator(flow_name, step_name)
        if progress:
            result = f"{progress}\n\n{result}"
    
    # Добавляем подсказку
    if show_hint:
        result = add_step_hint_to_message(flow_name, step_name, result)
    
    return result


# Callback handler для подсказок (добавить в main router)
async def handle_hint_callback(cb, state):
    """Обработчик callback'ов для подсказок"""
    
    parts = cb.data.split(":")
    if len(parts) != 3:
        await cb.answer("❌ Ошибка обработки подсказки")
        return
    
    _, flow_name, step_name = parts
    
    coordinator = get_fsm_coordinator()
    hint = coordinator.get_step_hint(flow_name, step_name)
    
    if hint:
        await cb.answer(hint, show_alert=True)
    else:
        await cb.answer("💡 Подсказка недоступна для этого шага")


# Дополнительные UX улучшения
def get_encouragement_message(step_count: int) -> str:
    """Возвращает мотивирующие сообщения на основе прогресса"""
    
    if step_count == 1:
        return "🚀 Отличное начало! Продолжайте отвечать честно для точных рекомендаций."
    elif step_count == 3:
        return "⭐ Вы уже на середине пути! Осталось совсем немного."
    elif step_count == 5:
        return "🎯 Почти готово! Последние вопросы для идеального результата."
    elif step_count >= 7:
        return "🏆 Финишная прямая! Сейчас сформируем ваши персональные рекомендации."
    
    return ""

def get_completion_celebration() -> str:
    """Возвращает сообщение празднования завершения теста"""
    
    return (
        "🎉 **Поздравляем!** 🎉\n\n"
        "✅ Диагностика завершена\n"
        "📊 Анализируем ваши ответы\n"
        "🎨 Формируем персональные рекомендации\n\n"
        "⏱️ Это займет несколько секунд..."
    )


if __name__ == "__main__":
    # Тест функций подсказок
    test_msg = format_step_message(
        "detailed_palette", 
        "Q1_HAIR_COLOR", 
        "Выберите ваш естественный цвет волос:",
        show_progress=True,
        show_hint=True
    )
    print("Test formatted message:")
    print(test_msg)
    print()
    
    encouragement = get_encouragement_message(3)
    print(f"Encouragement: {encouragement}")
    
    celebration = get_completion_celebration()
    print(f"Celebration: {celebration}")
    
    print("\nStep hints system ready! ✅")





