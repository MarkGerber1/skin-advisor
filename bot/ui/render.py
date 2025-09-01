from __future__ import annotations

from typing import Dict, List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _add_to_cart_button(item: Dict) -> InlineKeyboardButton | None:
    pid = item.get("id")
    if not pid:
        return None
    return InlineKeyboardButton(
        text=f"➕ В корзину: {item.get('brand','')} {item.get('name','')}",
        callback_data=f"cart:add:{pid}",
    )


def _price_row(it: Dict) -> str:
    value = int(it.get("price") or 0)
    currency = it.get("price_currency") or "₽"
    # В тестах ожидается символ ₽ рядом с числом
    if currency in ("RUB", "₽"):
        return f"{value} ₽"
    return f"{value} {currency}"


def _rows(items: List[Dict]) -> List[str]:
    lines: List[str] = []
    for it in items:
        lines.append(f"— {it.get('brand','')} {it.get('name','')} — {_price_row(it)}")
    return lines


def _noop_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔄 Обновить", callback_data="noop")]]
    )


def render_skincare_report(result: Dict) -> Tuple[str, InlineKeyboardMarkup]:
    print(f"🧴 render_skincare_report called with result keys: {list(result.keys())}")
    s = result.get("skincare", {})
    print(f"🧴 Skincare data keys: {list(s.keys()) if s else 'No skincare data'}")
    
    # CRITICAL FIX: Use RUSSIAN keys that actually come from SelectorV2
    # Данные приходят с русскими ключами из селектора
    cleanser = s.get("очищающее средство", [])
    toner = s.get("тоник", [])
    serum = s.get("сыворотка", [])
    moisturizer = s.get("увлажняющее средство", [])
    eye_cream = s.get("крем для кожи вокруг глаз", [])
    sunscreen = s.get("солнцезащитный крем", [])
    mask = s.get("маска", [])
    
    print(f"🧴 Found products: cleanser={len(cleanser)}, toner={len(toner)}, serum={len(serum)}, moisturizer={len(moisturizer)}, eye_cream={len(eye_cream)}, sunscreen={len(sunscreen)}, mask={len(mask)}")
    
    # Organize into AM/PM/Weekly for display
    am = cleanser + toner + serum + moisturizer + sunscreen  # Morning routine
    pm = cleanser + serum + moisturizer + eye_cream  # Evening routine  
    wk = mask  # Weekly treatments

    text_lines: List[str] = [
        "📋 Персональный уход",
        "",
        "AM:",
        *(_rows(am) or ["— Нет подходящих продуктов"]),
        "",
        "PM:",
        *(_rows(pm) or ["— Нет подходящих продуктов"]),
        "",
        "Weekly:",
        *(_rows(wk) or ["— Нет подходящих продуктов"]),
    ]

    links = [*(am or []), *(pm or []), *(wk or [])]
    # Если нет партнерских ссылок вообще — показать только noop-кнопку
    if not any(bool(it.get("ref_link")) for it in links):
        return "\n".join(text_lines), _noop_keyboard()

    buttons: List[List[InlineKeyboardButton]] = []
    for it in links[:5]:
        atc = _add_to_cart_button(it)
        if atc:
            buttons.append([atc])
        if it.get("ref_link"):
            buttons.append(
                [InlineKeyboardButton(text=f"🛒 {it['brand']} {it['name']}", url=it["ref_link"])]
            )

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
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
    face_categories = ['основа', 'консилер', 'корректор', 'пудра', 'румяна', 'бронзатор', 'контур', 'хайлайтер', 'Тональный крем']
    brows_categories = ['брови', 'Брови']  
    eyes_categories = ['тушь для ресниц', 'Тени для век', 'подводка для глаз', 'Тушь']
    lips_categories = ['помада', 'блеск для губ', 'lip_liner', 'Помада']
    
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
            category = str(product.get('category', '')).lower()
            print(f"🔍 Product category: '{category}' -> {product.get('name', 'No name')}")
            
            # Face products
            if any(term in category for term in ['тональн', 'основ', 'консил', 'пудр', 'румян', 'foundation', 'concealer', 'powder', 'blush']):
                face.append(product)
            # Brow products  
            elif any(term in category for term in ['бров', 'eyebrow', 'brow']):
                brows.append(product)
            # Eye products
            elif any(term in category for term in ['тушь', 'тени', 'подводк', 'mascara', 'eyeshadow', 'eyeliner']):
                eyes.append(product)
            # Lip products
            elif any(term in category for term in ['помад', 'блеск', 'lipstick', 'lip']):
                lips.append(product)
            else:
                # Default to face if category unclear
                face.append(product)
    
    # Products already distributed above in the simplified approach
    
    print(f"🛍️ Products count: face={len(face)}, brows={len(brows)}, eyes={len(eyes)}, lips={len(lips)}")

    text_lines: List[str] = [
        "🎨 Макияж по палитре",
        "",
        "Лицо:",
        *(_rows(face) or ["— Нет подходящих продуктов"]),
        "",
        "Брови:",
        *(_rows(brows) or ["— Нет подходящих продуктов"]),
        "",
        "Глаза:",
        *(_rows(eyes) or ["— Нет подходящих продуктов"]),
        "",
        "Губы:",
        *(_rows(lips) or ["— Нет подходящих продуктов"]),
    ]

    links = [*(face or []), *(brows or []), *(eyes or []), *(lips or [])]
    print(f"🔗 Total links found: {len(links)}")
    # Если нет партнерских ссылок — показать только noop-кнопку
    ref_links_count = sum(1 for it in links if bool(it.get("ref_link")))
    print(f"🌐 Products with ref_link: {ref_links_count}")
    if not any(bool(it.get("ref_link")) for it in links):
        print("⚠️ No ref_links found, returning noop keyboard")
        return "\n".join(text_lines), _noop_keyboard()

    buttons: List[List[InlineKeyboardButton]] = []
    for it in links[:5]:
        atc = _add_to_cart_button(it)
        if atc:
            buttons.append([atc])
        if it.get("ref_link"):
            buttons.append(
                [InlineKeyboardButton(text=f"🛒 {it['brand']} {it['name']}", url=it["ref_link"])]
            )

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return "\n".join(text_lines), kb
