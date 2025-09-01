from __future__ import annotations

from typing import List, Dict, Optional
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from engine.cart_store import CartStore, CartItem
from engine.selector import SelectorV2
from engine.business_metrics import get_metrics_tracker


router = Router()
store = CartStore()
selector = SelectorV2()
metrics = get_metrics_tracker()


def _user_id(msg: Message | None) -> int | None:
    if msg and msg.from_user and msg.from_user.id:
        return int(msg.from_user.id)
    return None


async def _find_product_in_recommendations(user_id: int, product_id: str) -> Optional[Dict]:
    """Найти товар в текущих рекомендациях пользователя"""
    try:
        # Получаем профиль пользователя
        from engine.models import UserProfile
        from engine.catalog import get_catalog_manager
        
        # Получаем реальный профиль пользователя из FSM coordinator
        from bot.handlers.fsm_coordinator import get_fsm_coordinator
        coordinator = get_fsm_coordinator()
        session = await coordinator.get_session(user_id)
        
        # Если есть активная сессия с данными теста, используем их
        if session and session.flow_data:
            profile_data = session.flow_data
            print(f"🔍 Found session profile data: {profile_data}")
            
            user_profile = UserProfile(
                user_id=user_id,
                skin_type=profile_data.get("skin_type", "normal"),
                concerns=profile_data.get("concerns", []),
                season=profile_data.get("season", "spring"),
                undertone=profile_data.get("undertone", "neutral"),
                contrast=profile_data.get("contrast", "medium")
            )
            print(f"✅ Using real profile: skin_type={user_profile.skin_type}, season={user_profile.season}")
        else:
            # Fallback: используем универсальный профиль
            print(f"⚠️ No session found for user {user_id}, using fallback profile")
            user_profile = UserProfile(
                user_id=user_id,
                skin_type="normal",
                concerns=[],
                season="spring",
                undertone="neutral",
                contrast="medium"
            )
            print(f"🔄 Using fallback profile: skin_type={user_profile.skin_type}, season={user_profile.season}")
        
        # Получаем каталог и строим рекомендации
        catalog_manager = get_catalog_manager()
        catalog = catalog_manager.get_catalog()
        
        # Используем селектор для получения рекомендаций
        print(f"🔧 Calling selector.select_products_v2 with profile...")
        result = selector.select_products_v2(user_profile, catalog, partner_code="S1")
        print(f"📦 Selector result keys: {list(result.keys()) if result else 'None'}")
        
        # Логируем количество товаров в каждой категории
        if result and result.get("makeup"):
            for category, products in result["makeup"].items():
                print(f"  💄 Makeup {category}: {len(products)} products")
        if result and result.get("skincare"):
            for step, products in result["skincare"].items():
                print(f"  🧴 Skincare {step}: {len(products)} products")
        
        # Ищем товар во всех категориях
        all_products = []
        if result.get("makeup"):
            for category_products in result["makeup"].values():
                all_products.extend(category_products)
        if result.get("skincare"):
            for category_products in result["skincare"].values():
                all_products.extend(category_products)
        
        # Ищем по ID
        for product in all_products:
            if str(product.get("id", "")) == product_id:
                return product
                
    except Exception as e:
        print(f"❌ Error finding product {product_id}: {e}")
    
    return None


@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Улучшенное добавление товара в корзину с полной валидацией и защитой от дублей"""
    if not cb.data:
        await cb.answer()
        return
        
    msg = cb.message
    if not isinstance(msg, Message):
        await cb.answer()
        return
        
    user_id = _user_id(msg)
    if not user_id:
        await cb.answer("Неизвестный пользователь", show_alert=True)
        return
    
    try:
        # Парсим callback data: cart:add:product_id или cart:add:product_id:variant_id
        parts = cb.data.split(":", 3)
        product_id = parts[2] if len(parts) > 2 else ""
        variant_id = parts[3] if len(parts) > 3 else None
        
        print(f"🛒 Adding product {product_id} (variant: {variant_id}) to cart for user {user_id}")
        
        # Используем улучшенный сервис корзины
        from services.cart_service import get_cart_service, CartServiceError, CartErrorCode
        cart_service = get_cart_service()
        
        # Добавляем товар с полной валидацией
        cart_item = await cart_service.add_item(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id,
            qty=1
        )
        
        # Метрика: успешное добавление
        metrics.track_event("cart_add_success", user_id, {
            "product_id": product_id,
            "variant_id": variant_id,
            "category": cart_item.category,
            "price": cart_item.price
        })
        
        # Формируем красивое уведомление
        brand_name = f"{cart_item.brand or ''} {cart_item.name or ''}".strip()
        price_text = f"{cart_item.price} {cart_item.price_currency}"
        
        message = f"✅ Добавлено в корзину!\n\n🛍️ {brand_name}"
        if cart_item.variant_name:
            message += f" ({cart_item.variant_name})"
        message += f"\n💰 {price_text}"
        
        if cart_item.explain:
            message += f"\n💡 {cart_item.explain}"
        
        await cb.answer(message, show_alert=True)
        
    except CartServiceError as e:
        print(f"❌ Cart service error: {e}")
        
        # Метрика: ошибка добавления
        metrics.track_event("cart_add_failed", user_id, {
            "reason": e.code.value,
            "product_id": parts[2] if len(parts) > 2 else "",
            "variant_id": parts[3] if len(parts) > 3 else None,
            "error_message": e.message
        })
        
        # Пользовательские сообщения об ошибках
        error_messages = {
            CartErrorCode.INVALID_PRODUCT_ID: "⚠️ Некорректный ID товара",
            CartErrorCode.INVALID_VARIANT_ID: "⚠️ Некорректный вариант товара", 
            CartErrorCode.PRODUCT_NOT_FOUND: "⚠️ Товар не найден в каталоге",
            CartErrorCode.OUT_OF_STOCK: "⚠️ Товар временно недоступен",
            CartErrorCode.VARIANT_NOT_SUPPORTED: "⚠️ Этот товар не поддерживает варианты",
            CartErrorCode.VARIANT_MISMATCH: "⚠️ Неподходящий вариант для данного товара",
            CartErrorCode.DUPLICATE_REQUEST: "⚠️ Подождите, товар уже добавляется...",
        }
        
        user_message = error_messages.get(e.code, "⚠️ Не удалось добавить товар в корзину")
        await cb.answer(user_message, show_alert=True)
        
    except Exception as e:
        print(f"❌ Unexpected error in add_to_cart: {e}")
        
        # Метрика: неожиданная ошибка
        metrics.track_event("cart_add_failed", user_id, {
            "reason": "unexpected_error",
            "product_id": parts[2] if len(parts) > 2 else "",
            "error_message": str(e)
        })
        
        await cb.answer("⚠️ Произошла ошибка. Попробуйте позже", show_alert=True)


@router.message(F.text == "🛒 Моя подборка")
async def show_cart(m: Message, state: FSMContext) -> None:
    """Показать корзину с полной информацией и кнопками управления"""
    user_id = _user_id(m)
    if not user_id:
        await m.answer("Неизвестный пользователь")
        return
        
    items: List[CartItem] = store.get(user_id)
    if not items:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Получить рекомендации", callback_data="get_recommendations")]
        ])
        await m.answer("🛒 Ваша корзина пуста.\n\nДобавьте товары из рекомендаций!", reply_markup=kb)
        return
    
    # Метрика: просмотр корзины
    metrics.track_event("cart_view", user_id, {"items_count": len(items)})
    
    # Формируем сообщение с полной информацией
    lines = ["🛒 **ВАША КОРЗИНА**\n"]
    total = 0.0
    available_items = 0
    
    for i, item in enumerate(items, 1):
        price = item.price or 0.0
        qty = item.qty
        total += price * qty
        
        # Формируем название товара
        brand_name = f"{item.brand or ''} {item.name or item.product_id}".strip()
        price_text = f"{price} {item.price_currency or '₽'}" if price > 0 else "Цена уточняется"
        
        # Статус наличия
        stock_emoji = "✅" if item.in_stock else "❌"
        if item.in_stock:
            available_items += 1
        
        lines.append(f"{i}. {stock_emoji} **{brand_name}**")
        lines.append(f"   💰 {price_text} × {qty} = {price * qty} {item.price_currency or '₽'}")
        
        if item.explain:
            lines.append(f"   💡 {item.explain}")
        
        if item.category:
            lines.append(f"   📂 {item.category}")
            
        lines.append("")
    
    # Итоги
    lines.append(f"📊 **ИТОГО:**")
    lines.append(f"• Позиций: {len(items)}")
    lines.append(f"• В наличии: {available_items}")
    lines.append(f"• Сумма: {total:.0f} ₽")
    
    # Кнопки управления
    buttons = []
    
    # Кнопки покупки для товаров в наличии
    buy_buttons = []
    for item in items[:3]:  # Показываем только первые 3
        if item.in_stock and item.ref_link:
            brand_short = (item.brand or "")[:10]
            buy_buttons.append([
                InlineKeyboardButton(
                    text=f"🛒 {brand_short}",
                    url=item.ref_link
                )
            ])
    
    if buy_buttons:
        buttons.extend(buy_buttons)
        buttons.append([InlineKeyboardButton(text="🛍️ Купить всё", callback_data="cart:buy_all")])
    
    # Кнопки управления корзиной
    buttons.extend([
        [
            InlineKeyboardButton(text="🗑️ Очистить", callback_data="cart:clear"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="cart:refresh")
        ],
        [InlineKeyboardButton(text="📋 Подробнее", callback_data="cart:details")]
    ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await m.answer("\n".join(lines), reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "cart:clear")
async def clear_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Очистить корзину"""
    user_id = _user_id(cb.message)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    store.clear(user_id)
    metrics.track_event("cart_clear", user_id, {})
    await cb.message.edit_text("🗑️ Корзина очищена")
    await cb.answer("Корзина очищена")


@router.callback_query(F.data == "cart:refresh")
async def refresh_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Обновить информацию в корзине"""
    user_id = _user_id(cb.message)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    # Проверяем актуальность товаров в корзине
    items = store.get(user_id)
    updated_count = 0
    removed_count = 0
    
    for item in items:
        # Получаем актуальную информацию о товаре
        current_product = await _find_product_in_recommendations(user_id, item.product_id)
        
        if not current_product:
            # Товар больше не доступен
            store.remove(user_id, item.product_id)
            removed_count += 1
        elif current_product.get("in_stock") != item.in_stock or current_product.get("price") != item.price:
            # Обновляем информацию
            updated_item = CartItem(
                product_id=item.product_id,
                qty=item.qty,
                brand=current_product.get("brand", item.brand),
                name=current_product.get("name", item.name),
                price=current_product.get("price", item.price),
                price_currency=current_product.get("price_currency", item.price_currency),
                ref_link=current_product.get("ref_link", item.ref_link),
                explain=current_product.get("explain", item.explain),
                category=current_product.get("category", item.category),
                in_stock=current_product.get("in_stock", True),
                added_at=item.added_at
            )
            store.remove(user_id, item.product_id)
            store.add(user_id, updated_item)
            updated_count += 1
    
    metrics.track_event("cart_refresh", user_id, {
        "updated": updated_count,
        "removed": removed_count
    })
    
    message = f"🔄 Корзина обновлена"
    if updated_count > 0:
        message += f"\n• Обновлено: {updated_count}"
    if removed_count > 0:
        message += f"\n• Удалено недоступных: {removed_count}"
    
    await cb.answer(message, show_alert=True)
    
    # Показываем обновленную корзину
    await show_cart(cb.message, state)


@router.callback_query(F.data == "cart:buy_all")  
async def buy_all_items(cb: CallbackQuery, state: FSMContext) -> None:
    """Открыть все ссылки для покупки (показать инструкцию)"""
    user_id = _user_id(cb.message)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    items = store.get(user_id)
    available_items = [item for item in items if item.in_stock and item.ref_link]
    
    if not available_items:
        await cb.answer("Нет доступных товаров для покупки", show_alert=True)
        return
    
    # Создаем кнопки со ссылками
    buttons = []
    for i, item in enumerate(available_items[:5], 1):  # Максимум 5 ссылок
        brand_name = f"{item.brand or ''} {item.name or ''}".strip()[:20]
        buttons.append([
            InlineKeyboardButton(
                text=f"{i}. {brand_name}",
                url=item.ref_link
            )
        ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    metrics.track_event("cart_buy_all_clicked", user_id, {
        "items_count": len(available_items)
    })
    
    await cb.message.answer(
        f"🛍️ **ПОКУПКА ТОВАРОВ**\n\nНажимайте на кнопки ниже для покупки каждого товара:\n\n" +
        f"Всего доступно: {len(available_items)} товаров",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await cb.answer("Ссылки для покупки готовы!")


async def _find_product_alternatives(user_id: int, unavailable_product_id: str) -> List[Dict]:
    """Найти альтернативы для недоступного товара"""
    try:
        from engine.models import UserProfile
        from engine.catalog import get_catalog_manager
        
        # Получаем профиль пользователя (тестовый)
        test_profile = UserProfile(
            user_id=user_id,
            skin_type="normal",
            concerns=[],
            season="spring",
            undertone="neutral",
            contrast="medium"
        )
        
        # Получаем каталог и строим рекомендации с fallback
        catalog_manager = get_catalog_manager()
        catalog = catalog_manager.get_catalog()
        
        # Используем fallback селектор
        result = selector.select_products_v2(test_profile, catalog, partner_code="S1")
        
        # Ищем альтернативы в той же категории
        alternatives = []
        all_products = []
        
        if result.get("makeup"):
            for category_products in result["makeup"].values():
                all_products.extend(category_products)
        if result.get("skincare"):
            for category_products in result["skincare"].values():
                all_products.extend(category_products)
        
        # Берем доступные товары (исключая недоступный)
        for product in all_products:
            if (product.get("in_stock", True) and 
                str(product.get("id", "")) != unavailable_product_id and
                len(alternatives) < 3):
                alternatives.append(product)
        
        return alternatives
        
    except Exception as e:
        print(f"❌ Error finding alternatives: {e}")
        return []


@router.callback_query(F.data.startswith("cart:unavailable:"))
async def handle_unavailable_product(cb: CallbackQuery, state: FSMContext) -> None:
    """Обработать недоступный товар - показать альтернативы"""
    if not cb.data:
        await cb.answer()
        return
        
    user_id = _user_id(cb.message)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
        
    product_id = cb.data.split(":", 2)[2]
    print(f"🔍 Finding alternatives for unavailable product {product_id}")
    
    # Ищем альтернативы
    alternatives = await _find_product_alternatives(user_id, product_id)
    
    metrics.track_event("cart_unavailable_viewed", user_id, {
        "product_id": product_id,
        "alternatives_found": len(alternatives)
    })
    
    if not alternatives:
        await cb.answer("😔 К сожалению, похожих товаров сейчас нет в наличии", show_alert=True)
        return
    
    # Формируем сообщение с альтернативами
    lines = ["⚠️ **ТОВАР НЕДОСТУПЕН**\n"]
    lines.append("Вот похожие товары в наличии:\n")
    
    buttons = []
    
    for i, alt in enumerate(alternatives, 1):
        brand_name = f"{alt.get('brand', '')} {alt.get('name', '')}".strip()
        price_text = f"{alt.get('price', 0)} {alt.get('price_currency', '₽')}"
        explain = alt.get('explain', '')
        
        lines.append(f"{i}. **{brand_name}**")
        lines.append(f"   💰 {price_text}")
        if explain:
            lines.append(f"   💡 {explain}")
    lines.append("")
        
        # Кнопки для добавления альтернативы
        alt_id = str(alt.get('id', ''))
        if alt_id:
            buttons.append([
                InlineKeyboardButton(
                    text=f"➕ Добавить {i}",
                    callback_data=f"cart:add:{alt_id}"
                ),
                InlineKeyboardButton(
                    text=f"🛒 Купить {i}",
                    url=alt.get('ref_link', 'https://goldapple.ru/')
                )
            ])
    
    # Кнопка возврата к корзине
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад к корзине", callback_data="cart:back")
    ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await cb.message.answer(
        "\n".join(lines),
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await cb.answer("Найдены похожие товары")


@router.callback_query(F.data == "cart:back")
async def back_to_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Вернуться к корзине"""
    await show_cart(cb.message, state)


@router.callback_query(F.data == "get_recommendations")
async def get_recommendations(cb: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Получить рекомендации' в корзине"""
    user_id = _user_id(cb.message)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    print(f"🎯 get_recommendations: user {user_id} wants recommendations for cart")
    
    # Показываем текущую корзину
    await show_cart(cb, state)
    
    await cb.answer("Открываю корзину с рекомендациями")


@router.callback_query(F.data == "cart:details")
async def show_cart_details(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать подробную информацию о товарах в корзине"""
    user_id = _user_id(cb.message)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    items = store.get(user_id)
    if not items:
        await cb.answer("Корзина пуста")
        return
    
    # Формируем детальное описание каждого товара
    for i, item in enumerate(items, 1):
        lines = [f"**ТОВАР {i}/{len(items)}**\n"]
        
        brand_name = f"{item.brand or ''} {item.name or item.product_id}".strip()
        lines.append(f"🏷️ **{brand_name}**")
        
        if item.category:
            lines.append(f"📂 Категория: {item.category}")
        
        price_text = f"{item.price} {item.price_currency}" if item.price else "Цена уточняется"
        lines.append(f"💰 Цена: {price_text}")
        lines.append(f"📦 Количество: {item.qty}")
        
        stock_text = "✅ В наличии" if item.in_stock else "❌ Недоступен"
        lines.append(f"📊 Статус: {stock_text}")
        
        if item.explain:
            lines.append(f"\n💡 **Почему подходит:**\n{item.explain}")
        
        if item.added_at:
            lines.append(f"\n📅 Добавлено: {item.added_at[:10]}")
        
        # Кнопки для товара
        buttons = []
        
        if item.in_stock and item.ref_link:
            buttons.append([
                InlineKeyboardButton(
                    text="🛒 Купить",
                    url=item.ref_link
                )
            ])
        elif not item.in_stock:
            buttons.append([
                InlineKeyboardButton(
                    text="🔍 Найти похожие",
                    callback_data=f"cart:unavailable:{item.product_id}"
                )
            ])
        
        buttons.extend([
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить",
                    callback_data=f"cart:remove:{item.product_id}"
                ),
                InlineKeyboardButton(
                    text="📊 +1",
                    callback_data=f"cart:inc:{item.product_id}"
                ),
                InlineKeyboardButton(
                    text="📉 -1", 
                    callback_data=f"cart:dec:{item.product_id}"
                )
            ]
        ])
        
        if i == len(items):  # Последний товар
            buttons.append([
                InlineKeyboardButton(text="⬅️ Назад к корзине", callback_data="cart:back")
            ])
        else:
            buttons.append([
                InlineKeyboardButton(text="➡️ Следующий товар", callback_data="cart:details")
            ])
        
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await cb.message.answer(
            "\n".join(lines),
            reply_markup=kb,
            parse_mode="Markdown"
        )
    
    await cb.answer("Подробная информация")


@router.callback_query(F.data.startswith("cart:remove:"))
async def remove_from_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Удалить товар из корзины"""
    user_id = _user_id(cb.message)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    product_id = cb.data.split(":", 2)[2]
    store.remove(user_id, product_id)
    
    metrics.track_event("cart_remove", user_id, {"product_id": product_id})
    await cb.answer("Товар удален из корзины")
    await show_cart(cb.message, state)


@router.callback_query(F.data.startswith("cart:inc:"))
async def increase_quantity(cb: CallbackQuery, state: FSMContext) -> None:
    """Увеличить количество товара"""
    user_id = _user_id(cb.message)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    product_id = cb.data.split(":", 2)[2]
    items = store.get(user_id)
    
    for item in items:
        if item.product_id == product_id:
            new_qty = min(item.qty + 1, 10)  # Максимум 10 штук
            store.set_qty(user_id, product_id, new_qty)
            
            metrics.track_event("cart_qty_change", user_id, {
                "product_id": product_id,
                "new_qty": new_qty,
                "action": "increase"
            })
            
            await cb.answer(f"Количество: {new_qty}")
            break
    
    await show_cart(cb.message, state)


@router.callback_query(F.data.startswith("cart:dec:"))
async def decrease_quantity(cb: CallbackQuery, state: FSMContext) -> None:
    """Уменьшить количество товара"""
    user_id = _user_id(cb.message)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    product_id = cb.data.split(":", 2)[2]
    items = store.get(user_id)
    
    for item in items:
        if item.product_id == product_id:
            new_qty = max(item.qty - 1, 1)  # Минимум 1 штука
            store.set_qty(user_id, product_id, new_qty)
            
            metrics.track_event("cart_qty_change", user_id, {
                "product_id": product_id,
                "new_qty": new_qty,
                "action": "decrease"
            })
            
            await cb.answer(f"Количество: {new_qty}")
            break
    
    await show_cart(cb.message, state)
