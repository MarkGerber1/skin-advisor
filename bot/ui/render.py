from __future__ import annotations

from typing import Dict, List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Design System Message Templates
class MessageTemplates:
    """Шаблоны сообщений в стиле дизайн-системы"""

    # Цветовые эмодзи для категоризации
    CATEGORY_ICONS = {
        "cleanser": "🧼",
        "toner": "💧",
        "serum": "✨",
        "moisturizer": "🧴",
        "sunscreen": "☀️",
        "mask": "😷",
        "foundation": "💄",
        "concealer": "🎭",
        "powder": "🧁",
    }

    # Статусные сообщения
    SUCCESS_MESSAGES = [
        "✅ Отлично! Продолжаем...",
        "🎉 Прекрасно! Идем дальше...",
        "✨ Отличный выбор! Следующий шаг...",
        "💫 Превосходно! Продолжим...",
    ]

    ERROR_MESSAGES = [
        "❌ Что-то пошло не так. Попробуйте еще раз...",
        "⚠️ Произошла ошибка. Давайте попробуем снова...",
        "🚫 Извините, возникла проблема...",
    ]

    # Приветственные сообщения
    WELCOME_MESSAGES = [
        "👋 Привет! Я ваш косметический помощник",
        "💄 Добро пожаловать в мир красоты!",
        "✨ Давайте подберем идеальный уход вместе!",
    ]


def _add_to_cart_button(item: Dict) -> InlineKeyboardButton | None:
    """Создает кнопку добавления в корзину с дизайном из системы"""
    pid = item.get("id")
    if not pid:
        return None

    # Design System: Краткий и понятный текст кнопки
    brand = item.get("brand", "").strip()
    name = item.get("name", "").strip()
    item.get("price", "")

    # Короткий текст для мобильных устройств
    if brand and name:
        button_text = f"🛒 {brand[:10]}..."
    else:
        button_text = "🛒 В корзину"

    return InlineKeyboardButton(
        text=button_text,
        callback_data=f"cart:add:{pid}:default",
    )


def _price_row(it: Dict) -> str:
    value = int(it.get("price") or 0)
    currency = it.get("price_currency") or it.get("currency") or "₽"
    # В тестах ожидается символ ₽ рядом с числом
    if currency in ("RUB", "₽"):
        return f"{value} ₽"
    return f"{value} {currency}"


def _rows(items: List[Dict]) -> List[str]:
    lines: List[str] = []
    for it in items:
        # Получаем информацию об источнике
        source_name = it.get("source_name", "")
        source_mark = f" 🏪 {source_name}" if source_name else ""

        # Проверяем альтернативу
        alt_reason = it.get("alternative_reason", "")
        alt_mark = ""
        if alt_reason == "другой_вариант_товара":
            alt_mark = " 🔄"
        elif alt_reason == "аналог_категории":
            alt_mark = " 🔀"
        elif alt_reason == "универсальный_вариант":
            alt_mark = " ⭐"

        lines.append(
            f"— {it.get('brand','')} {it.get('name','')}{alt_mark} — {_price_row(it)}{source_mark}"
        )
    return lines


def _noop_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔄 Обновить", callback_data="noop")]]
    )


def render_skincare_report(result: Dict) -> Tuple[str, InlineKeyboardMarkup]:
    print(f"🧴 render_skincare_report called with result keys: {list(result.keys())}")
    s = result.get("skincare", {})
    print(f"🧴 Skincare data keys: {list(s.keys()) if s else 'No skincare data'}")

    # CRITICAL FIX: Use ENGLISH keys that actually come from SelectorV2
    # Данные приходят с английскими ключами из селектора
    cleanser = s.get("cleanser", [])
    toner = s.get("toner", [])
    serum = s.get("serum", [])
    moisturizer = s.get("moisturizer", [])
    eye_cream = s.get("eye_cream", [])  # Keep technical key for data access
    sunscreen = s.get("sunscreen", [])
    mask = s.get("mask", [])

    print(
        f"🧴 Found products: cleanser={len(cleanser)}, toner={len(toner)}, serum={len(serum)}, moisturizer={len(moisturizer)}, eye_cream={len(eye_cream)}, sunscreen={len(sunscreen)}, mask={len(mask)}"
    )

    # Применяем приоритизацию источников и поиск альтернатив
    from engine.source_resolver import enhance_product_with_source_info

    # Enhance products with source info and alternatives
    enhanced_cleanser = [enhance_product_with_source_info(p) for p in cleanser]
    enhanced_toner = [enhance_product_with_source_info(p) for p in toner]
    enhanced_serum = [enhance_product_with_source_info(p) for p in serum]
    enhanced_moisturizer = [enhance_product_with_source_info(p) for p in moisturizer]
    enhanced_eye_cream = [enhance_product_with_source_info(p) for p in eye_cream]
    enhanced_sunscreen = [enhance_product_with_source_info(p) for p in sunscreen]
    enhanced_mask = [enhance_product_with_source_info(p) for p in mask]

    # Organize into AM/PM/Weekly for display
    am = (
        enhanced_cleanser
        + enhanced_toner
        + enhanced_serum
        + enhanced_moisturizer
        + enhanced_sunscreen
    )  # Morning routine
    pm = (
        enhanced_cleanser + enhanced_serum + enhanced_moisturizer + enhanced_eye_cream
    )  # Evening routine
    wk = enhanced_mask  # Weekly treatments

    text_lines: List[str] = [
        "📋 Персональный уход",
        "",
        "🌅 **УТРОМ (AM):**",
        *(_rows(am) or ["— Нет подходящих продуктов"]),
        "",
        "🌙 **ВЕЧЕРОМ (PM):**",
        *(_rows(pm) or ["— Нет подходящих продуктов"]),
        "",
        "📅 **ЕЖЕНЕДЕЛЬНО:**",
        *(_rows(wk) or ["— Нет подходящих продуктов"]),
        "",
        "**🛍️ Выбрать товары:**",
        "• 🏪 источник товара",
        "• 🔄 другой вариант",
        "• 🔀 аналог категории",
        "• ⭐ универсальный выбор",
    ]

    all_products = [*(am or []), *(pm or []), *(wk or [])]

    # CRITICAL FIX: Create cart buttons based on product ID, not ref_link
    # Even if ref_link is missing, we can still add products to cart
    products_with_id = [p for p in all_products if p.get("id")]
    print(f"🆔 Skincare products with ID: {len(products_with_id)}")

    # Generate affiliate links for products
    products_with_ref_link = []
    for product in products_with_id:
        if not product.get("ref_link"):
            try:
                # Проверяем, что у продукта есть необходимые поля
                if not product.get("id"):
                    print("⚠️ Skincare product missing ID, skipping affiliate link generation")
                    products_with_ref_link.append(product)
                    continue

                if not product.get("link") and not product.get("url"):
                    print(
                        f"⚠️ Skincare product {product.get('id')} has no link, skipping affiliate link generation"
                    )
                    products_with_ref_link.append(product)
                    continue

                from services.affiliates import build_ref_link

                ref_link = build_ref_link(product, "skincare_recommendation")
                if ref_link:
                    product["ref_link"] = ref_link
                    print(
                        f"🔗 Generated affiliate link for {product.get('id')}: {ref_link[:50]}..."
                    )
                else:
                    print(
                        f"⚠️ Failed to generate affiliate link for {product.get('id')} (returned None)"
                    )

            except Exception as e:
                print(f"⚠️ Failed to generate affiliate link for {product.get('id')}: {e}")
                import traceback

                traceback.print_exc()
        products_with_ref_link.append(product)

    print(
        f"🌐 Skincare products with ref_link: {len([p for p in products_with_ref_link if p.get('ref_link')])}"
    )

    buttons: List[List[InlineKeyboardButton]] = []

    # Add cart buttons for first 8 products
    for product in products_with_id[:8]:
        atc = _add_to_cart_button(product)
        if atc:
            buttons.append([atc])

    # Add "Show All" button if we have many products
    if len(products_with_id) > 8:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🛍️ Показать все товары ({len(products_with_id)})",
                    callback_data="skincare:show_all",
                )
            ]
        )

    # ALWAYS: Add "Go to Cart" button if we have any products
    if products_with_id:
        buttons.append(
            [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="show_cart")]
        )

    # Debug ref_link issue
    ref_link_products = [p for p in all_products if p.get("ref_link")]
    print(f"🌐 Skincare products with ref_link: {len(ref_link_products)}")
    if not ref_link_products and products_with_id:
        print("⚠️ Skincare products have IDs but no ref_links - check affiliate link generation")
        if products_with_id:
            sample_product = products_with_id[0]
            print(
                f"📝 Sample skincare product: id={sample_product.get('id')}, link={sample_product.get('link')}, ref_link={sample_product.get('ref_link')}"
            )

    # Return keyboard or noop
    if buttons:
        print(f"🛒 Created {len(buttons)} total skincare buttons")
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    else:
        print("⚠️ No skincare products with ID found, returning noop keyboard")
        kb = _noop_keyboard()

    return "\n".join(text_lines), kb


def render_makeup_report(result: Dict) -> Tuple[str, InlineKeyboardMarkup]:
    print(f"🎨 render_makeup_report called with result keys: {list(result.keys())}")
    m = result.get("makeup", {})
    print(f"💄 Makeup data keys: {list(m.keys()) if m else 'No makeup data'}")

    # CRITICAL DEBUG: Show all makeup categories and their content counts
    if m:
        print("🔍 DETAILED MAKEUP ANALYSIS:")
        for key, products in m.items():
            count = len(products) if products else 0
            print(f"  📦 EXACT KEY '{key}': {count} products")
            if products and count > 0:
                print(f"      First product: {products[0].get('name', 'No name')}")

        # CRITICAL: Let's use the ACTUAL keys that exist in the data
        print("🎯 USING ACTUAL KEYS FROM SELECTOR:")
        actual_keys = list(m.keys())
        print(f"Available keys: {actual_keys}")
    else:
        print("❌ No makeup data to analyze")

    # Map SelectorV2 categories to display groups
    # CRITICAL: SelectorV2 returns in CAPITALIZED keys: "Тональный крем", "Брови", "Помада", "Тушь", "Тени для век"
    face_categories = [
        "основа",
        "консилер",
        "корректор",
        "пудра",
        "румяна",
        "бронзатор",
        "контур",
        "хайлайтер",
        "Тональный крем",
    ]
    brows_categories = ["брови", "Брови"]
    eyes_categories = ["тушь для ресниц", "Тени для век", "подводка для глаз", "Тушь"]
    lips_categories = ["помада", "блеск для губ", "lip_liner", "Помада"]

    print(f"🔍 Looking for face categories: {face_categories}")
    print(f"🔍 Looking for brows categories: {brows_categories}")
    print(f"🔍 Looking for eyes categories: {eyes_categories}")
    print(f"🔍 Looking for lips categories: {lips_categories}")

    # SIMPLIFIED: Just use ALL available products from makeup data
    face = []
    brows = []
    eyes = []
    lips = []

    # If we have makeup data, distribute all products to appropriate categories
    if m:
        print("🎯 SIMPLIFIED APPROACH: Using all available makeup products")
        all_makeup_products = []
        for key, products in m.items():
            if products:
                print(f"📦 Adding {len(products)} products from '{key}'")
                all_makeup_products.extend(products)

        # Distribute products based on their category field
        for product in all_makeup_products:
            category = str(product.get("category", "")).lower()
            print(f"🔍 Product category: '{category}' -> {product.get('name', 'No name')}")

            # Face products
            if any(
                term in category
                for term in [
                    "тональн",
                    "основ",
                    "консил",
                    "пудр",
                    "румян",
                    "foundation",
                    "concealer",
                    "powder",
                    "blush",
                ]
            ):
                face.append(product)
            # Brow products
            elif any(term in category for term in ["бров", "eyebrow", "brow"]):
                brows.append(product)
            # Eye products
            elif any(
                term in category
                for term in ["тушь", "тени", "подводк", "mascara", "eyeshadow", "eyeliner"]
            ):
                eyes.append(product)
            # Lip products
            elif any(term in category for term in ["помад", "блеск", "lipstick", "lip"]):
                lips.append(product)
            else:
                # Default to face if category unclear
                face.append(product)

    # Products already distributed above in the simplified approach
    else:
        # No makeup data available
        print("❌ No makeup data - using empty lists")

    print(
        f"🛍️ Products count: face={len(face)}, brows={len(brows)}, eyes={len(eyes)}, lips={len(lips)}"
    )

    text_lines: List[str] = [
        "🎨 Макияж по палитре",
        "",
        "💋 **ЛИЦО:**",
        *(_rows(face) or ["— Нет подходящих продуктов"]),
        "",
        "🤨 **БРОВИ:**",
        *(_rows(brows) or ["— Нет подходящих продуктов"]),
        "",
        "👁️ **ГЛАЗА:**",
        *(_rows(eyes) or ["— Нет подходящих продуктов"]),
        "",
        "💄 **ГУБЫ:**",
        *(_rows(lips) or ["— Нет подходящих продуктов"]),
        "",
        "**🛍️ Выбрать товары:**",
        "• 🏪 источник товара",
        "• 🔄 другой вариант",
        "• 🔀 аналог категории",
        "• ⭐ универсальный выбор",
    ]

    all_products = [*(face or []), *(brows or []), *(eyes or []), *(lips or [])]
    print(f"🛍️ Total makeup products for buttons: {len(all_products)}")

    # CRITICAL FIX: Create cart buttons based on product ID, not ref_link
    # Even if ref_link is missing, we can still add products to cart
    products_with_id = [p for p in all_products if p.get("id")]
    print(f"🆔 Products with ID: {len(products_with_id)}")

    # Generate affiliate links for products
    products_with_ref_link = []
    for product in products_with_id:
        if not product.get("ref_link"):
            try:
                # Проверяем, что у продукта есть необходимые поля
                if not product.get("id"):
                    print("⚠️ Product missing ID, skipping affiliate link generation")
                    products_with_ref_link.append(product)
                    continue

                if not product.get("link") and not product.get("url"):
                    print(
                        f"⚠️ Product {product.get('id')} has no link, skipping affiliate link generation"
                    )
                    products_with_ref_link.append(product)
                    continue

                from services.affiliates import build_ref_link

                ref_link = build_ref_link(product, "makeup_recommendation")
                if ref_link:
                    product["ref_link"] = ref_link
                    print(
                        f"🔗 Generated affiliate link for {product.get('id')}: {ref_link[:50]}..."
                    )
                else:
                    print(
                        f"⚠️ Failed to generate affiliate link for {product.get('id')} (returned None)"
                    )

            except Exception as e:
                print(f"⚠️ Failed to generate affiliate link for {product.get('id')}: {e}")
                import traceback

                traceback.print_exc()
        products_with_ref_link.append(product)

    print(
        f"🌐 Products with ref_link: {len([p for p in products_with_ref_link if p.get('ref_link')])}"
    )

    buttons: List[List[InlineKeyboardButton]] = []

    # Add cart buttons for first 8 products
    for product in products_with_id[:8]:
        atc = _add_to_cart_button(product)
        if atc:
            buttons.append([atc])

    # Add "Show All" button if we have many products
    if len(products_with_id) > 8:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🛍️ Показать все товары ({len(products_with_id)})",
                    callback_data="makeup:show_all",
                )
            ]
        )

    # ALWAYS: Add "Go to Cart" button if we have any products
    if products_with_id:
        buttons.append(
            [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="show_cart")]
        )

    # Debug ref_link issue
    ref_link_products = [p for p in all_products if p.get("ref_link")]
    print(f"🌐 Products with ref_link: {len(ref_link_products)}")
    if not ref_link_products and products_with_id:
        print("⚠️ Products have IDs but no ref_links - check affiliate link generation")
        sample_product = products_with_id[0]
        print(
            f"📝 Sample product: id={sample_product.get('id')}, link={sample_product.get('link')}, ref_link={sample_product.get('ref_link')}"
        )

    # Return keyboard or noop
    if buttons:
        print(f"🛒 Created {len(buttons)} total buttons")
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    else:
        print("⚠️ No products with ID found, returning noop keyboard")
        kb = _noop_keyboard()

    return "\n".join(text_lines), kb
