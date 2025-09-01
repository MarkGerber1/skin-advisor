#!/usr/bin/env python3
"""
🛒 Дополнительные обработчики корзины для работы с вариантами
Расширенные операции: смена варианта, количество, групповые операции
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from services.cart_service import get_cart_service, CartServiceError, CartErrorCode
from engine.business_metrics import get_metrics_tracker
from engine.analytics import get_analytics_tracker

router = Router()
metrics = get_metrics_tracker()


def _user_id(cb: CallbackQuery) -> int | None:
    """Извлечь user_id из callback query"""
    return cb.from_user.id if cb.from_user else None


@router.callback_query(F.data.startswith("cart:change_variant:"))
async def change_item_variant(cb: CallbackQuery, state: FSMContext) -> None:
    """Изменить вариант товара в корзине"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    try:
        # Парсим callback: cart:change_variant:product_id:old_variant_id:new_variant_id
        parts = cb.data.split(":", 5)
        if len(parts) < 5:
            await cb.answer("⚠️ Некорректные параметры")
            return
            
        product_id = parts[2]
        old_variant_id = parts[3] if parts[3] != "default" else None
        new_variant_id = parts[4] if parts[4] != "default" else None
        
        cart_service = get_cart_service()
        
        # Обновляем вариант
        updated_item = await cart_service.update_item_variant(
            user_id=user_id,
            product_id=product_id,
            old_variant_id=old_variant_id,
            new_variant_id=new_variant_id
        )
        
        # Analytics: Cart item updated (variant changed)
        analytics = get_analytics_tracker()
        analytics.cart_item_updated(user_id, product_id, old_variant_id, 1, 1)
        
        metrics.track_event("cart_variant_changed", user_id, {
            "product_id": product_id,
            "old_variant": old_variant_id,
            "new_variant": new_variant_id
        })
        
        variant_name = updated_item.variant_name or "стандартный"
        await cb.answer(f"✅ Вариант изменен на: {variant_name}")
        
        # Обновляем отображение корзины
        from bot.handlers.cart import show_cart
        await show_cart(cb.message, state)
        
    except CartServiceError as e:
        print(f"❌ Error changing variant: {e}")
        await cb.answer(f"⚠️ {e.message}")
        
    except Exception as e:
        print(f"❌ Unexpected error in change_item_variant: {e}")
        await cb.answer("⚠️ Произошла ошибка")


@router.callback_query(F.data.startswith("cart:set_qty:"))
async def set_item_quantity(cb: CallbackQuery, state: FSMContext) -> None:
    """Установить количество товара в корзине"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    try:
        # Парсим callback: cart:set_qty:product_id:variant_id:qty
        parts = cb.data.split(":", 5)
        if len(parts) < 5:
            await cb.answer("⚠️ Некорректные параметры")
            return
            
        product_id = parts[2]
        variant_id = parts[3] if parts[3] != "default" else None
        qty = int(parts[4])
        
        cart_service = get_cart_service()
        
        # Устанавливаем количество
        result_item = cart_service.set_item_quantity(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id,
            qty=qty
        )
        
        # Analytics: Cart item updated or removed
        analytics = get_analytics_tracker()
        
        if result_item:
            analytics.cart_item_updated(user_id, product_id, variant_id, qty_before=0, qty_after=qty)
            
            metrics.track_event("cart_quantity_changed", user_id, {
                "product_id": product_id,
                "variant_id": variant_id,
                "new_qty": qty
            })
            await cb.answer(f"✅ Количество изменено: {qty}")
        else:
            analytics.cart_item_removed(user_id, product_id, variant_id)
            
            metrics.track_event("cart_item_removed", user_id, {
                "product_id": product_id,
                "variant_id": variant_id,
                "reason": "qty_zero"
            })
            await cb.answer("✅ Товар удален из корзины")
        
        # Обновляем отображение корзины
        from bot.handlers.cart import show_cart
        await show_cart(cb.message, state)
        
    except (ValueError, IndexError):
        await cb.answer("⚠️ Некорректные параметры")
        
    except CartServiceError as e:
        print(f"❌ Error setting quantity: {e}")
        await cb.answer(f"⚠️ {e.message}")
        
    except Exception as e:
        print(f"❌ Unexpected error in set_item_quantity: {e}")
        await cb.answer("⚠️ Произошла ошибка")


@router.callback_query(F.data.startswith("cart:remove_exact:"))
async def remove_exact_item(cb: CallbackQuery, state: FSMContext) -> None:
    """Удалить точный товар с вариантом из корзины"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    try:
        # Парсим callback: cart:remove_exact:product_id:variant_id
        parts = cb.data.split(":", 4)
        if len(parts) < 4:
            await cb.answer("⚠️ Некорректные параметры")
            return
            
        product_id = parts[2]
        variant_id = parts[3] if parts[3] != "default" else None
        
        cart_service = get_cart_service()
        
        # Удаляем товар
        success = cart_service.remove_item(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id
        )
        
        if success:
            # Analytics: Cart item removed  
            analytics = get_analytics_tracker()
            analytics.cart_item_removed(user_id, product_id, variant_id)
            
            metrics.track_event("cart_item_removed", user_id, {
                "product_id": product_id,
                "variant_id": variant_id,
                "reason": "manual"
            })
            await cb.answer("✅ Товар удален из корзины")
        else:
            await cb.answer("⚠️ Товар не найден в корзине")
        
        # Обновляем отображение корзины
        from bot.handlers.cart import show_cart
        await show_cart(cb.message, state)
        
    except CartServiceError as e:
        print(f"❌ Error removing item: {e}")
        await cb.answer(f"⚠️ {e.message}")
        
    except Exception as e:
        print(f"❌ Unexpected error in remove_exact_item: {e}")
        await cb.answer("⚠️ Произошла ошибка")


@router.callback_query(F.data == "cart:clear_enhanced")
async def clear_cart_enhanced(cb: CallbackQuery, state: FSMContext) -> None:
    """Очистить корзину с подтверждением"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    # Показываем кнопки подтверждения
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, очистить", callback_data="cart:clear_confirmed"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cart:clear_cancelled")
        ]
    ])
    
    await cb.message.edit_text(
        "🗑️ **ОЧИСТКА КОРЗИНЫ**\n\n"
        "Вы уверены, что хотите удалить все товары из корзины?\n"
        "Это действие нельзя отменить.",
        reply_markup=confirm_kb,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "cart:clear_confirmed")
async def clear_cart_confirmed(cb: CallbackQuery, state: FSMContext) -> None:
    """Подтвержденная очистка корзины"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    try:
        cart_service = get_cart_service()
        cart_service.clear_cart(user_id)
        
        metrics.track_event("cart_cleared", user_id, {"reason": "manual"})
        
        await cb.message.edit_text(
            "✅ **КОРЗИНА ОЧИЩЕНА**\n\n"
            "Все товары удалены из корзины."
        )
        await cb.answer("Корзина очищена")
        
    except CartServiceError as e:
        print(f"❌ Error clearing cart: {e}")
        await cb.answer(f"⚠️ {e.message}")
        
    except Exception as e:
        print(f"❌ Unexpected error in clear_cart_confirmed: {e}")
        await cb.answer("⚠️ Произошла ошибка")


@router.callback_query(F.data == "cart:clear_cancelled")
async def clear_cart_cancelled(cb: CallbackQuery, state: FSMContext) -> None:
    """Отмена очистки корзины"""
    await cb.answer("Очистка отменена")
    
    # Возвращаемся к корзине
    from bot.handlers.cart import show_cart
    await show_cart(cb.message, state)
