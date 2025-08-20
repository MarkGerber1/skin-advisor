from __future__ import annotations

from typing import Dict, List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _rows(items: List[Dict]) -> List[str]:
    lines: List[str] = []
    for it in items:
        lines.append(f"— {it.get('brand','')} {it.get('name','')} — {int(it.get('price') or 0)} {it.get('price_currency') or '₽'}")
    return lines


def render_skincare_report(result: Dict) -> Tuple[str, InlineKeyboardMarkup]:
    s = result.get("skincare", {})
    am = s.get("AM", [])
    pm = s.get("PM", [])
    wk = s.get("weekly", [])
    text_lines: List[str] = [
        "📋 Персональный уход",
        "",
        "AM:",
        *(_rows(am) or ["—"]),
        "",
        "PM:",
        *(_rows(pm) or ["—"]),
        "",
        "Weekly:",
        *(_rows(wk) or ["—"]),
    ]
    buttons: List[List[InlineKeyboardButton]] = []
    links = [*(am or []), *(pm or []), *(wk or [])]
    for it in links[:6]:
        if it.get("ref_link"):
            buttons.append([InlineKeyboardButton(text=f"Купить: {it['brand']} {it['name']}", url=it["ref_link"])])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons or [[InlineKeyboardButton(text="Обновить", callback_data="noop")]])
    return "\n".join(text_lines), kb


def render_makeup_report(result: Dict) -> Tuple[str, InlineKeyboardMarkup]:
    m = result.get("makeup", {})
    face = m.get("face", [])
    brows = m.get("brows", [])
    eyes = m.get("eyes", [])
    lips = m.get("lips", [])
    text_lines: List[str] = [
        "🎨 Макияж по палитре",
        "",
        "Лицо:",
        *(_rows(face) or ["—"]),
        "",
        "Брови:",
        *(_rows(brows) or ["—"]),
        "",
        "Глаза:",
        *(_rows(eyes) or ["—"]),
        "",
        "Губы:",
        *(_rows(lips) or ["—"]),
    ]
    buttons: List[List[InlineKeyboardButton]] = []
    links = [*(face or []), *(brows or []), *(eyes or []), *(lips or [])]
    for it in links[:6]:
        if it.get("ref_link"):
            buttons.append([InlineKeyboardButton(text=f"Купить: {it['brand']} {it['name']}", url=it["ref_link"])])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons or [[InlineKeyboardButton(text="Обновить", callback_data="noop")]])
    return "\n".join(text_lines), kb


