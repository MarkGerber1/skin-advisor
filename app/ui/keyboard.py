from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def build_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🧪 Пройти анкету"),
                KeyboardButton(text="📄 Мои рекомендации"),
            ],
            [
                KeyboardButton(text="💰 Баланс"),
                KeyboardButton(text="🔗 Моя реферальная ссылка"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие",
    )

