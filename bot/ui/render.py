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
    s = result.get("skincare", {})
    am = s.get("AM", [])
    pm = s.get("PM", [])
    wk = s.get("weekly", [])

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
    
    # Map SelectorV2 categories to display groups
    face_categories = ['основа', 'консилер', 'корректор', 'пудра', 'румяна', 'бронзатор', 'контур', 'хайлайтер']
    brows_categories = ['брови']
    eyes_categories = ['тушь для ресниц', 'тени для век', 'подводка для глаз']
    lips_categories = ['помада', 'блеск для губ', 'lip_liner']
    
    # Collect products by display groups
    face = []
    for cat in face_categories:
        products = m.get(cat, [])
        print(f"📦 Category '{cat}': {len(products)} products")
        face.extend(products)
    
    brows = []
    for cat in brows_categories:
        products = m.get(cat, [])
        print(f"📦 Category '{cat}': {len(products)} products")
        brows.extend(products)
        
    eyes = []
    for cat in eyes_categories:
        products = m.get(cat, [])
        print(f"📦 Category '{cat}': {len(products)} products")
        eyes.extend(products)
        
    lips = []
    for cat in lips_categories:
        products = m.get(cat, [])
        print(f"📦 Category '{cat}': {len(products)} products")
        lips.extend(products)
    
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
