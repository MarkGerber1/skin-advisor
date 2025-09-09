"""
Унифицированная пост-тестовая навигация
Обеспечивает единообразное меню после завершения любого теста
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional


def create_post_test_navigation(
    test_type: str,  # "palette" или "skincare"
    current_screen: Optional[str] = None,  # "description", "recommendations", "products", "cart"
    show_cart: bool = True,
    cart_count: int = 0
) -> InlineKeyboardMarkup:
    """
    Создает унифицированную навигацию для пост-тестового состояния

    Args:
        test_type: Тип теста ("palette" или "skincare")
        current_screen: Текущий экран для выделения активной кнопки
        show_cart: Показывать ли кнопку корзины
        cart_count: Количество товаров в корзине

    Returns:
        InlineKeyboardMarkup с навигационными кнопками
    """
    prefix = "pl:" if test_type == "palette" else "sk:"

    buttons = []

    # Основная навигация
    nav_row = []

    # Описание
    desc_text = "📋 Описание" if current_screen != "description" else "📋 Описание ✓"
    nav_row.append(InlineKeyboardButton(
        text=desc_text,
        callback_data=f"{prefix}nav:description"
    ))

    # Рекомендации
    rec_text = "💡 Рекомендации" if current_screen != "recommendations" else "💡 Рекомендации ✓"
    nav_row.append(InlineKeyboardButton(
        text=rec_text,
        callback_data=f"{prefix}nav:recommendations"
    ))

    buttons.append(nav_row)

    # Что купить
    buy_text = "🛍️ Что купить" if current_screen != "products" else "🛍️ Что купить ✓"
    buttons.append([InlineKeyboardButton(
        text=buy_text,
        callback_data=f"{prefix}nav:products"
    )])

    # Корзина (если есть товары или всегда показывать)
    if show_cart or cart_count > 0:
        cart_text = f"🛒 Корзина ({cart_count})" if cart_count > 0 else "🛒 Корзина"
        if current_screen == "cart":
            cart_text += " ✓"
        buttons.append([InlineKeyboardButton(
            text=cart_text,
            callback_data="show_cart"
        )])

    # В меню
    buttons.append([InlineKeyboardButton(
        text="⤴️ В меню",
        callback_data="universal:home"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_product_buttons(
    test_type: str,
    product_id: str,
    has_ref_link: bool = False,
    in_cart: bool = False,
    variant_id: Optional[str] = None
) -> List[List[InlineKeyboardButton]]:
    """
    Создает кнопки для товара: "В корзину" и опционально "Купить на сайте"

    Args:
        test_type: Тип теста для префикса
        product_id: ID товара
        has_ref_link: Есть ли партнерская ссылка
        in_cart: Товар уже в корзине
        variant_id: ID варианта товара

    Returns:
        Список рядов кнопок
    """
    buttons = []

    # Кнопка "В корзину"
    cart_callback = f"c:add:{product_id}:{variant_id or 'default'}"
    cart_text = "✓ В корзине" if in_cart else "🛒 В корзину"

    if has_ref_link:
        # Две кнопки в ряд
        buttons.append([
            InlineKeyboardButton(text=cart_text, callback_data=cart_callback),
            InlineKeyboardButton(text="🌐 Купить на сайте", callback_data=f"buy:{product_id}")
        ])
    else:
        # Только корзина
        buttons.append([InlineKeyboardButton(text=cart_text, callback_data=cart_callback)])

    return buttons


def create_cart_controls(
    item_count: int,
    total_price: float,
    currency: str = "RUB"
) -> InlineKeyboardMarkup:
    """
    Создает элементы управления корзиной

    Args:
        item_count: Количество товаров
        total_price: Общая сумма
        currency: Валюта

    Returns:
        Клавиатура с кнопками управления корзиной
    """
    buttons = []

    # Информация о корзине
    if item_count > 0:
        price_text = f"{total_price:.0f} ₽" if currency == "RUB" else f"${total_price:.0f}"
        buttons.append([InlineKeyboardButton(
            text=f"📊 Итого: {price_text} ({item_count} шт.)",
            callback_data="cart_info"
        )])

    # Управление товарами (будет реализовано в cart handler)
    buttons.append([
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="cart:add_item"),
        InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="cart:clear")
    ])

    # Оформление
    buttons.append([InlineKeyboardButton(
        text="✅ Оформить заказ",
        callback_data="cart:checkout"
    )])

    # Навигация обратно
    buttons.append([InlineKeyboardButton(
        text="⬅️ Назад к товарам",
        callback_data="nav:back_to_products"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Готовые шаблоны для быстрого использования
PALETTE_NAV = create_post_test_navigation("palette")
SKINCARE_NAV = create_post_test_navigation("skincare")
