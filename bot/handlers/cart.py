# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Dict, Optional
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from services.cart_store import get_cart_store, CartStore, CartItem
from engine.selector import SelectorV2
from engine.business_metrics import get_metrics_tracker
from engine.analytics import get_analytics_tracker

# Cart service removed - using direct CartStore operations
print("[OK] Using CartStore directly (services/cart_service removed)")
CART_SERVICE_AVAILABLE = False


router = Router()
store = get_cart_store()
selector = SelectorV2()
metrics = get_metrics_tracker()


def _compare_keyboards(kb1: InlineKeyboardMarkup | None, kb2: InlineKeyboardMarkup | None) -> bool:
    """Сравнить две клавиатуры"""
    if not kb1 and not kb2:
        return True
    if not kb1 or not kb2:
        return False

    if len(kb1.inline_keyboard) != len(kb2.inline_keyboard):
        return False

    for row1, row2 in zip(kb1.inline_keyboard, kb2.inline_keyboard):
        if len(row1) != len(row2):
            return False
        for btn1, btn2 in zip(row1, row2):
            if (btn1.text != btn2.text or
                btn1.callback_data != btn2.callback_data or
                btn1.url != btn2.url):
                return False

    return True

def _user_id(msg_or_cb: Message | CallbackQuery | None) -> int | None:
    """Extract real user ID, not bot ID from Message or CallbackQuery"""
    if msg_or_cb and hasattr(msg_or_cb, 'from_user') and msg_or_cb.from_user and msg_or_cb.from_user.id:
        user_id = int(msg_or_cb.from_user.id)
        print(f"🔍 _user_id: {type(msg_or_cb).__name__}.from_user.id = {user_id}")
        # Проверяем что это не bot ID (8345324302)
        if user_id == 8345324302:
            print(f"[WARNING] Got bot ID instead of user ID!")
            # В callback query контексте попробуем найти реальный user ID
            if hasattr(msg_or_cb, 'message') and msg_or_cb.message and msg_or_cb.message.from_user:
                real_user_id = int(msg_or_cb.message.from_user.id)
                if real_user_id != 8345324302:
                    print(f"[OK] Found real user ID from callback message: {real_user_id}")
                    return real_user_id
        return user_id
    print(f"[ERROR] _user_id: no message/callback or from_user")
    return None


async def _find_product_in_recommendations(user_id: int, product_id: str) -> Optional[Dict]:
    """Найти товар в текущих рекомендациях пользователя"""
    try:
        # Получаем профиль пользователя
        from engine.models import UserProfile
        from engine.catalog_store import CatalogStore

        # Сначала пытаемся загрузить сохраненный профиль пользователя
        from bot.handlers.user_profile_store import get_user_profile_store
        profile_store = get_user_profile_store()
        user_profile = profile_store.load_profile(user_id)

        if user_profile:
            print(f"[OK] Using saved profile: skin_type={user_profile.skin_type}, season={user_profile.season}")
        else:
            # Если сохраненного профиля нет, пробуем получить из FSM coordinator
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
                print(f"[OK] Using session profile: skin_type={user_profile.skin_type}, season={user_profile.season}")
            else:
                # Fallback: используем универсальный профиль
                print(f"[WARNING] No saved or session profile found for user {user_id}, using fallback profile")
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
        import os
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()
        
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
                # Генерируем affiliate link если его нет
                if not product.get("ref_link"):
                    try:
                        from services.affiliates import build_ref_link
                        product["ref_link"] = build_ref_link(product, "cart_add")
                        print(f"🔗 Generated affiliate link for {product_id}: {product['ref_link'][:50]}...")
                    except Exception as e:
                        print(f"⚠️ Failed to generate affiliate link: {e}")
                return product
                
    except Exception as e:
        print(f"[ERROR] Error finding product {product_id}: {e}")
    
    return None


@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Улучшенное добавление товара в корзину с полной валидацией и защитой от дублей"""
    print(f"🛒 Cart add callback triggered: {cb.data}")
    
    if not cb.data:
        print("[ERROR] No callback data provided")
        await cb.answer()
        return
        
    user_id = _user_id(cb)
    if not user_id:
        print("❌ No user ID found")
        await cb.answer("Неизвестный пользователь", show_alert=True)
        return

    msg = cb.message
    if not isinstance(msg, Message):
        print("❌ Invalid message type")
        await cb.answer()
        return
    
    try:
        # Парсим callback data: cart:add:product_id или cart:add:product_id:variant_id
        parts = cb.data.split(":", 3)
        product_id = parts[2] if len(parts) > 2 else ""
        variant_id = parts[3] if len(parts) > 3 else None

        # Валидация входных параметров
        if not product_id or not isinstance(product_id, str) or len(product_id.strip()) == 0:
            await cb.answer("❌ Некорректный ID товара", show_alert=True)
            return
        
        print(f"🛒 DETAILED: Adding product '{product_id}' (variant: {variant_id}) to cart for user {user_id}")
        print(f"🛒 Using CartStore directly (cart_service removed)")

        # Direct CartStore operations (fallback logic)
        print(f"🔄 Using fallback cart method for {product_id}")
        product_data = await _find_product_in_recommendations(user_id, product_id)
        print(f"🔍 Product data found: {product_data is not None}")
        if product_data:
            print(f"📦 Product details: brand={product_data.get('brand')}, name={product_data.get('name')}, price={product_data.get('price')}")

        if not product_data:
            print(f"❌ Product {product_id} not found in recommendations")
            await cb.answer("❌ Товар не найден в рекомендациях", show_alert=True)
            return

        cart_item = CartItem(
            product_id=product_id,
            quantity=1,
            brand=product_data.get('brand'),
            name=product_data.get('name'),
            price=product_data.get('price'),
            price_currency=product_data.get('price_currency', 'RUB'),
            ref_link=product_data.get('ref_link'),
            category=product_data.get('category'),
            variant_id=variant_id
        )
        print(f"📝 Created cart item: {cart_item}")

        # Add to store
        print(f"💾 Adding to store for user {user_id}")
        store.add_item(
            user_id=user_id,
            product_id=cart_item.product_id,
            variant_id=cart_item.variant_id,
            quantity=cart_item.quantity,
            brand=cart_item.brand,
            name=cart_item.name,
            price=cart_item.price,
            ref_link=cart_item.ref_link,
            category=cart_item.category
        )
        print(f"✅ Successfully added to store")
        
        # Диагностика: проверяем что товар действительно добавился
        stored_items = store.get_cart(user_id)
        print(f"🔍 STORE VERIFICATION: User {user_id} now has {len(stored_items)} items in cart")
        for i, item in enumerate(stored_items):
            print(f"    {i+1}. {item.brand} {item.name} (ID: {item.product_id})")
        
        # Analytics: Product added to cart
        analytics = get_analytics_tracker()
        analytics.product_added_to_cart(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id,
            source=cart_item.ref_link,
            price=cart_item.price,
            category=cart_item.category
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
        
    except Exception as e:
        print(f"❌ Cart operation error: {e}")
        print(f"❌ Exception type: {type(e).__name__}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")

        # Метрика: ошибка добавления
        try:
            metrics.track_event("cart_add_failed", user_id, {
                "reason": "cart_error",
                "product_id": parts[2] if len(parts) > 2 else "",
                "variant_id": parts[3] if len(parts) > 3 else None,
                "error_message": str(e)
            })
        except:
            pass  # Ignore metrics errors

        # Пользовательское сообщение об ошибке
        await cb.answer("⚠️ Не удалось добавить товар в корзину", show_alert=True)


@router.callback_query(F.data == "show_cart")
async def show_cart_callback(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать корзину через inline кнопку"""
    print(f"🛒 Show cart callback triggered for user {cb.from_user.id if cb.from_user else 'unknown'}")
    print(f"🔍 CALLBACK DIAGNOSTIC: cb.from_user.id = {cb.from_user.id if cb.from_user else 'None'}")

    user_id = _user_id(cb)
    if not user_id:
        print("❌ No user ID found in callback")
        await cb.answer("Неизвестный пользователь", show_alert=True)
        return

    print(f"🔍 CART DIAGNOSTIC: show_cart called")
    print(f"  👤 Callback user ID: {cb.from_user.id if cb.from_user else 'None'}")
    print(f"  🔑 Processed user ID: {user_id}")

    # Диагностируем состояние корзины
    items: List[CartItem] = store.get_cart(user_id)
    print(f"  🛒 Cart items for user {user_id}: {len(items)}")

    # Показываем все корзины в store для диагностики
    all_carts = store._carts if hasattr(store, '_carts') else {}
    print(f"  📦 All carts in store: {list(all_carts.keys())}")
    for cart_user_id, cart_items in all_carts.items():
        print(f"    User {cart_user_id}: {len(cart_items)} items")

    if not items:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Получить рекомендации", callback_data="get_recommendations")]
        ])
        await cb.message.edit_text("🛒 Ваша корзина пуста.\n\nДобавьте товары из рекомендаций!", reply_markup=kb)
        await cb.answer()
        return

    # Метрика: просмотр корзины
    metrics.track_event("cart_view", user_id, {"items_count": len(items)})

    # Формируем сообщение с полной информацией
    lines = ["🛒 **ВАША КОРЗИНА**\n"]
    total = 0.0
    available_items = 0
    item_buttons = []

    for i, item in enumerate(items, 1):
        price = item.price or 0.0
        qty = item.quantity
        total += price * qty

        # Формируем название товара
        brand_name = f"{item.brand or ''} {item.name or item.product_id}".strip()
        price_text = f"{price} {item.price_currency or '₽'}" if price > 0 else "Цена уточняется"

        # Статус наличия
        stock_emoji = "✅" if item.in_stock else "❌"
        if item.in_stock:
            available_items += 1

        # Строка товара
        lines.append(f"{i}. {stock_emoji} **{brand_name}**\n   {price_text} × {qty}")
        if item.explain:
            lines.append(f"   _{item.explain}_\n")

        # Кнопки управления количеством для каждого товара
        item_buttons.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart:dec:{item.product_id}"),
            InlineKeyboardButton(text=f"{qty}", callback_data=f"cart:show:{item.product_id}"),
            InlineKeyboardButton(text="➕", callback_data=f"cart:inc:{item.product_id}"),
            InlineKeyboardButton(text="🗑️", callback_data=f"cart:del:{item.product_id}")
        ])

    # Итоговая информация
    lines.append(f"\n💰 **Итого:** {total:.0f} ₽")
    lines.append(f"📦 Доступно: {available_items}/{len(items)} товаров")

    # Кнопки управления
    all_buttons = item_buttons + [
        [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="cart:clear")],
        [InlineKeyboardButton(text="📋 Создать заказ", callback_data="cart:checkout")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back:main")]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=all_buttons)

    text = "\n".join(lines)

    # Проверяем, изменилось ли сообщение, чтобы избежать "message is not modified"
    current_text = cb.message.text or ""
    current_markup = cb.message.reply_markup

    # Сравниваем текст и разметку
    text_changed = current_text != text
    markup_changed = self._compare_keyboards(current_markup, kb) if current_markup else True

    if text_changed or markup_changed:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        print("ℹ️ Cart content unchanged, skipping edit_message_text")

    await cb.answer()

@router.message(F.text == "🛒 Корзина")
async def show_cart(m: Message, state: FSMContext) -> None:
    """Показать корзину с полной информацией и кнопками управления"""
    user_id = _user_id(m)
    print(f"🔍 CART DIAGNOSTIC: show_cart called")
    print(f"  👤 Message user ID: {m.from_user.id if m.from_user else 'None'}")
    print(f"  🔑 Processed user ID: {user_id}")
    
    if not user_id:
        print("❌ No user ID found")
        await m.answer("Неизвестный пользователь")
        return
        
    # Диагностируем состояние корзины
    items: List[CartItem] = store.get_cart(user_id)
    print(f"  🛒 Cart items for user {user_id}: {len(items)}")
    
    # Показываем все корзины в store для диагностики
    all_carts = store._carts if hasattr(store, '_carts') else {}
    print(f"  📦 All carts in store: {list(all_carts.keys())}")
    for cart_user_id, cart_items in all_carts.items():
        print(f"    User {cart_user_id}: {len(cart_items)} items")
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
    user_id = _user_id(cb)
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
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    # Проверяем актуальность товаров в корзине
    items = store.get_cart(user_id)
    updated_count = 0
    removed_count = 0
    
    for item in items:
        # Получаем актуальную информацию о товаре
        current_product = await _find_product_in_recommendations(user_id, item.product_id)
        
        if not current_product:
            # Товар больше не доступен
            store.remove_item(user_id, item.product_id, item.variant_id)
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
            store.remove_item(user_id, item.product_id, item.variant_id)
            store.add_item(
                user_id=user_id,
                product_id=updated_item.product_id,
                variant_id=updated_item.variant_id,
                quantity=updated_item.quantity,
                brand=updated_item.brand,
                name=updated_item.name,
                price=updated_item.price,
                ref_link=updated_item.ref_link,
                category=updated_item.category
            )
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
    await show_cart_callback(cb, state)


@router.callback_query(F.data == "cart:buy_all")  
async def buy_all_items(cb: CallbackQuery, state: FSMContext) -> None:
    """Открыть все ссылки для покупки (показать инструкцию)"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    items = store.get_cart(user_id)
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
        from engine.catalog_store import CatalogStore
        
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
        import os
        catalog_path = os.getenv("CATALOG_PATH", "assets/fixed_catalog.yaml")
        catalog_store = CatalogStore.instance(catalog_path)
        catalog = catalog_store.get()
        
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
        
    user_id = _user_id(cb)
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
    await show_cart_callback(cb, state)


@router.callback_query(F.data.startswith("cart:update_variant:"))
async def update_item_variant(cb: CallbackQuery, state: FSMContext) -> None:
    """Обновить вариант товара в корзине"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Неизвестный пользователь")
        return

    try:
        # Парсим: cart:update_variant:product_id:old_variant:new_variant
        parts = cb.data.split(":", 5)
        if len(parts) < 5:
            await cb.answer("❌ Некорректные параметры")
            return

        product_id = parts[2]
        old_variant = parts[3] if parts[3] != "null" else None
        new_variant = parts[4] if parts[4] != "null" else None

        # Use CartStore directly (cart_service removed)
        updated_item = store.update_item_variant(
            user_id=user_id,
            product_id=product_id,
            old_variant_id=old_variant,
            new_variant_id=new_variant
        )

        if updated_item:
            # Analytics
            analytics = get_analytics_tracker()
            analytics.track_event("cart_variant_updated", user_id, {
                "product_id": product_id,
                "old_variant": old_variant,
                "new_variant": new_variant
            })

            await cb.answer(f"✅ Вариант обновлен: {updated_item.variant_name or 'Стандарт'}", show_alert=True)
        else:
            await cb.answer("❌ Товар не найден в корзине", show_alert=True)

    except Exception as e:
        print(f"❌ Unexpected error in variant update: {e}")
        await cb.answer("❌ Произошла ошибка при обновлении варианта", show_alert=True)

    # Показываем обновленную корзину
    await show_cart_callback(cb, state)


@router.callback_query(F.data == "get_recommendations")
async def get_recommendations(cb: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Получить рекомендации' в корзине"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    print(f"🎯 get_recommendations: user {user_id} wants recommendations for cart")
    
    # Показываем текущую корзину
    await show_cart_callback(cb, state)
    
    await cb.answer("Открываю корзину с рекомендациями")


@router.callback_query(F.data == "cart:details")
async def show_cart_details(cb: CallbackQuery, state: FSMContext) -> None:
    """Показать подробную информацию о товарах в корзине"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    items = store.get_cart(user_id)
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


@router.callback_query(F.data.startswith("cart:rm:"))
async def remove_from_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Удалить товар из корзины"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return

    parts = cb.data.split(":")
    product_id = parts[2]
    variant_id = parts[3] if len(parts) > 3 else None

    success = store.remove_item(user_id, product_id, variant_id)

    if success:
        metrics.track_event("cart_item_removed", user_id, {
            "product_id": product_id,
            "variant_id": variant_id
        })
        await cb.answer("Товар удален из корзины")
    else:
        await cb.answer("Товар не найден")

    await show_cart_callback(cb, state)


@router.callback_query(F.data.startswith("cart:inc:"))
async def increase_quantity(cb: CallbackQuery, state: FSMContext) -> None:
    """Увеличить количество товара"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    product_id = cb.data.split(":", 2)[2]
    cart = store.get_cart(user_id)

    for item in cart:
        if item.product_id == product_id:
            new_qty = min(item.quantity + 1, 10)  # Максимум 10 штук
            store.update_quantity(user_id, product_id, item.variant_id, new_qty)

            metrics.track_event("cart_qty_change", user_id, {
                "product_id": product_id,
                "variant_id": item.variant_id,
                "new_qty": new_qty,
                "action": "increase"
            })

            await cb.answer(f"Количество: {new_qty}")
            break

    await show_cart_callback(cb, state)


@router.callback_query(F.data.startswith("cart:dec:"))
async def decrease_quantity(cb: CallbackQuery, state: FSMContext) -> None:
    """Уменьшить количество товара"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    product_id = cb.data.split(":", 2)[2]
    cart = store.get_cart(user_id)

    for item in cart:
        if item.product_id == product_id:
            new_qty = max(item.quantity - 1, 1)  # Минимум 1 штука
            store.update_quantity(user_id, product_id, item.variant_id, new_qty)

            metrics.track_event("cart_qty_change", user_id, {
                "product_id": product_id,
                "variant_id": item.variant_id,
                "new_qty": new_qty,
                "action": "decrease"
            })

            await cb.answer(f"Количество: {new_qty}")
            break

    await show_cart_callback(cb, state)

@router.callback_query(F.data.startswith("cart:inc:"))
async def increase_quantity(cb: CallbackQuery, state: FSMContext) -> None:
    """Увеличить количество товара"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    product_id = cb.data.split(":", 2)[2]
    cart = store.get_cart(user_id)
    
    for item in cart:
        if item.product_id == product_id:
            new_qty = item.quantity + 1
            store.update_quantity(user_id, product_id, item.variant_id, new_qty)
            
            metrics.track_event("cart_qty_change", user_id, {
                "product_id": product_id,
                "variant_id": item.variant_id,
                "new_qty": new_qty,
                "action": "increase"
            })
            
            await cb.answer(f"Количество: {new_qty}")
            break
    
    await show_cart_callback(cb, state)


@router.callback_query(F.data.startswith("cart:rm:"))
async def remove_from_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Удалить товар из корзины"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    parts = cb.data.split(":")
    product_id = parts[2]
    variant_id = parts[3] if len(parts) > 3 else None
    
    success = store.remove_item(user_id, product_id, variant_id)
    
    if success:
        metrics.track_event("cart_item_removed", user_id, {
            "product_id": product_id,
            "variant_id": variant_id
        })
        
        await cb.answer("Товар удален из корзины")
    else:
        await cb.answer("Товар не найден")
    
    await show_cart_callback(cb, state)


@router.callback_query(F.data == "cart:checkout")
async def checkout_cart(cb: CallbackQuery, state: FSMContext) -> None:
    """Оформить заказ"""
    user_id = _user_id(cb)
    if not user_id:
        await cb.answer("Ошибка пользователя")
        return
    
    cart = store.get_cart(user_id)
    if not cart:
        await cb.answer("Корзина пуста")
        return
    
    # Создать сообщение с товарами и ссылками
    text_lines = ["🛒 **ОФОРМЛЕНИЕ ЗАКАЗА**\n"]
    
    total_price = 0
    buttons = []
    
    for item in cart:
        price = (item.price or 0) * item.quantity
        total_price += price
        
        text_lines.append(f"• {item.brand or ''} {item.name or ''}")
        text_lines.append(f"  Количество: {item.quantity}")
        text_lines.append(f"  Цена: {price:.0f} ₽")
        
        # Кнопка для оформления на сайте
        if item.ref_link:
            buttons.append([InlineKeyboardButton(
                text=f"��� Купить {item.brand or item.name}",
                url=item.ref_link
            )])
        elif hasattr(item, 'link') and item.link:
            buttons.append([InlineKeyboardButton(
                text=f"��� Купить {item.brand or item.name}",
                url=item.link
            )])
        
        text_lines.append("")  # Пустая строка
    
    text_lines.append(f"**Итого: {total_price:.0f} ₽**")
    
    # Кнопки навигации
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад в корзину", callback_data="show_cart"),
        InlineKeyboardButton(text="��� Главное меню", callback_data="back:main")
    ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await cb.message.edit_text("\\n".join(text_lines), reply_markup=kb)
    
    # Логирование
    metrics.track_event("cart_checkout_opened", user_id, {
        "items_count": len(cart),
        "total_price": total_price
    })

    await cb.answer()


@router.callback_query(F.data.startswith("cart:inc:"))
async def cart_increment(cb: CallbackQuery):
    """Увеличить количество товара в корзине"""
    try:
        user_id = cb.from_user.id
        product_id = cb.data.split(":")[2]

        print(f"📈 Incrementing {product_id} for user {user_id}")

        # Получаем корзину
        store = get_cart_store()
        cart = store.get_cart(user_id)

        # Находим товар и увеличиваем количество
        for item in cart:
            if item.product_id == product_id:
                item.quantity += 1
                store._save_cart(user_id, cart)
                print(f"✅ Incremented {product_id} to {item.quantity}")

                # Аналитика
                if ANALYTICS_AVAILABLE:
                    analytics = get_analytics_tracker()
                    analytics.track_event("cart_quantity_changed", user_id, {
                        "product_id": product_id,
                        "action": "increment",
                        "new_quantity": item.quantity
                    })
                break

        # Перерисовываем корзину
        await show_cart_callback(cb)

    except Exception as e:
        print(f"❌ Error incrementing cart item: {e}")
        await cb.answer("⚠️ Ошибка при увеличении количества")


@router.callback_query(F.data.startswith("cart:dec:"))
async def cart_decrement(cb: CallbackQuery):
    """Уменьшить количество товара в корзине"""
    try:
        user_id = cb.from_user.id
        product_id = cb.data.split(":")[2]

        print(f"📉 Decrementing {product_id} for user {user_id}")

        # Получаем корзину
        store = get_cart_store()
        cart = store.get_cart(user_id)

        # Находим товар и уменьшаем количество
        for i, item in enumerate(cart):
            if item.product_id == product_id:
                if item.quantity > 1:
                    item.quantity -= 1
                    print(f"✅ Decremented {product_id} to {item.quantity}")
                else:
                    # Удаляем товар если количество = 1
                    cart.pop(i)
                    print(f"🗑️ Removed {product_id} from cart")

                store._save_cart(user_id, cart)

                # Аналитика
                if ANALYTICS_AVAILABLE:
                    analytics = get_analytics_tracker()
                    analytics.track_event("cart_quantity_changed", user_id, {
                        "product_id": product_id,
                        "action": "decrement" if item.quantity > 0 else "remove",
                        "new_quantity": item.quantity if item.quantity > 0 else 0
                    })
                break

        # Перерисовываем корзину
        await show_cart_callback(cb)

    except Exception as e:
        print(f"❌ Error decrementing cart item: {e}")
        await cb.answer("⚠️ Ошибка при уменьшении количества")


@router.callback_query(F.data.startswith("cart:del:"))
async def cart_delete(cb: CallbackQuery):
    """Удалить товар из корзины"""
    try:
        user_id = cb.from_user.id
        product_id = cb.data.split(":")[2]

        print(f"🗑️ Deleting {product_id} from cart for user {user_id}")

        # Удаляем товар из корзины
        store = get_cart_store()
        cart = store.get_cart(user_id)

        # Находим и удаляем товар
        for i, item in enumerate(cart):
            if item.product_id == product_id:
                removed_item = cart.pop(i)
                store._save_cart(user_id, cart)
                print(f"✅ Removed {product_id} from cart")

                # Аналитика
                if ANALYTICS_AVAILABLE:
                    analytics = get_analytics_tracker()
                    analytics.track_event("cart_item_removed", user_id, {
                        "product_id": product_id,
                        "brand": removed_item.brand,
                        "name": removed_item.name
                    })
                break

        # Перерисовываем корзину
        await show_cart_callback(cb)

    except Exception as e:
        print(f"❌ Error deleting cart item: {e}")
        await cb.answer("⚠️ Ошибка при удалении товара")


@router.callback_query(F.data == "cart:clear")
async def cart_clear(cb: CallbackQuery):
    """Очистить всю корзину"""
    try:
        user_id = cb.from_user.id
        print(f"🧹 Clearing cart for user {user_id}")

        # Очищаем корзину
        store = get_cart_store()
        store.clear_cart(user_id)

        print("✅ Cart cleared")

        # Аналитика
        if ANALYTICS_AVAILABLE:
            analytics = get_analytics_tracker()
            analytics.track_event("cart_cleared", user_id)

        await cb.answer("🗑️ Корзина очищена!")

        # Перерисовываем корзину (будет пустая)
        await show_cart_callback(cb)

    except Exception as e:
        print(f"❌ Error clearing cart: {e}")
        await cb.answer("⚠️ Ошибка при очистке корзины")
