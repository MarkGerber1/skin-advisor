import json
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Загружаем тексты кнопок
with open('app/i18n/ru.json', 'r', encoding='utf-8') as f:
    LEXICON = json.load(f)


def set_main_menu() -> ReplyKeyboardMarkup:
    """Создает основную клавиатуру с кнопками."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=LEXICON['btn_start_survey']),
        KeyboardButton(text=LEXICON['btn_results']),
        KeyboardButton(text=LEXICON['btn_recommendations']),
    )
    builder.row(
        KeyboardButton(text=LEXICON['btn_navigation']),
        KeyboardButton(text=LEXICON['btn_reset'])
    )
    return builder.as_markup(resize_keyboard=True)


def create_nav_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для навигации."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=LEXICON['btn_help'], callback_data='nav_help'),
        InlineKeyboardButton(text=LEXICON['btn_policy'], callback_data='nav_policy')
    )
    return builder.as_markup()


def create_survey_keyboard(question_id: str, options: dict, is_multi: bool = False) -> InlineKeyboardMarkup:
    """Создает клавиатуру для вопроса анкеты."""
    builder = InlineKeyboardBuilder()
    for key, value in options.items():
        builder.add(InlineKeyboardButton(text=value, callback_data=f'survey:{question_id}:{key}'))

    if is_multi:
        builder.add(InlineKeyboardButton(text=LEXICON['btn_next'], callback_data=f'survey:{question_id}:next'))

    builder.adjust(1)
    return builder.as_markup()


def create_confirm_keyboard(callback_data: str, text: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с одной кнопкой подтверждения."""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    return builder.as_markup()


def create_results_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для страницы с результатами."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=LEXICON['btn_get_recommendations'], callback_data='action:get_recs'),
        InlineKeyboardButton(text=LEXICON['btn_download_pdf'], callback_data='action:get_pdf')
    )
    builder.row(
        InlineKeyboardButton(text=LEXICON['btn_change_answers'], callback_data='action:reset')
    )
    return builder.as_markup()


def create_price_tier_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора ценовой категории."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=LEXICON['btn_budget'], callback_data='price:budget'),
        InlineKeyboardButton(text=LEXICON['btn_mid'], callback_data='price:mid'),
        InlineKeyboardButton(text=LEXICON['btn_premium'], callback_data='price:premium')
    )
    return builder.as_markup()


def create_links_keyboard(product: dict) -> InlineKeyboardMarkup:
    """Создает клавиатуру со ссылками на маркетплейсы."""
    builder = InlineKeyboardBuilder()
    from app.infra.settings import get_settings
    settings = get_settings()

    for marketplace_name in settings.app.marketplaces:
        if url := product.get("links", {}).get(marketplace_name):
            builder.add(InlineKeyboardButton(text=f'🛒 {marketplace_name}', url=url))

    builder.adjust(1)
    return builder.as_markup()



