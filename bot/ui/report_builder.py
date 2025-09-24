"""
Report Builder - формирует блоки отчёта и рендеры для Telegram и PDF.

Структура:
1) Заголовок
2) Описание
3) Рекомендации
4) Что купить (товары с кнопками В корзину)
5) Советы
6) Действия (кнопки)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
import json
from pathlib import Path

from bot.utils.security import sanitize_message


@dataclass
class ReportBlocks:
    title: str
    description: str
    recommendations: Dict[str, List[str]]  # keys: morning/evening or sections
    to_buy: List[Dict[str, Any]]  # items with id, name, price, variant_id?
    tips: List[str]


def _plain(text: str) -> str:
    return sanitize_message(text or "")


def build_palette_report(profile: Dict[str, Any], picks: Dict[str, Any]) -> ReportBlocks:
    title = _plain("Отчёт по цветотипу и палитре")
    description = _plain(
        f"Ваш сезон: {profile.get('season', 'не определён')}. Подтон: {profile.get('undertone', '—')}"
    )
    recos = {
        "tones": [_plain(r) for r in picks.get("tones", ["Подберите натуральный оттенок тона"])]
    }
    products = picks.get("products", [])[:15]
    tips = [
        _plain("Используйте базу под макияж для стойкости"),
        _plain("Сочетайте тёплые и холодные оттенки аккуратно"),
    ]
    return ReportBlocks(title, description, recos, products, tips)


def build_skincare_report(profile: Dict[str, Any], picks: Dict[str, Any]) -> ReportBlocks:
    title = _plain("Отчёт по уходу за кожей")
    skin = profile.get("skin_type") or profile.get("skinType") or "не определён"
    description = _plain(f"Тип кожи: {skin}")
    # Утро/вечер из picks['skincare']
    recos = {
        "morning": [
            _plain("Очищение"),
            _plain("Увлажнение"),
            _plain("Солнцезащита"),
        ],
        "evening": [
            _plain("Очищение"),
            _plain("Сыворотка"),
            _plain("Крем"),
        ],
    }
    products = picks.get("products", [])[:15]
    tips = [
        _plain("Наносите SPF ежедневно"),
        _plain("Не забывайте про зону вокруг глаз"),
    ]
    return ReportBlocks(title, description, recos, products, tips)


def render_report_telegram(blocks: ReportBlocks) -> Tuple[str, List[List[Tuple[str, str]]]]:
    """Возвращает текст и инлайн-клавиатуру (label, callback)."""
    lines: List[str] = []
    lines.append(blocks.title)
    lines.append("")
    lines.append(blocks.description)
    lines.append("")
    lines.append("Рекомендации:")
    if blocks.recommendations.get("morning"):
        lines.append("Утро:")
        for item in blocks.recommendations["morning"]:
            lines.append(f"• {item}")
    if blocks.recommendations.get("evening"):
        lines.append("Вечер:")
        for item in blocks.recommendations["evening"]:
            lines.append(f"• {item}")
    if blocks.recommendations.get("tones"):
        lines.append("Палитра:")
        for item in blocks.recommendations["tones"]:
            lines.append(f"• {item}")

    lines.append("")
    lines.append("Что купить:")
    for p in blocks.to_buy[:10]:
        name = _plain(p.get("name") or p.get("title") or "Товар")
        price = p.get("price")
        currency = p.get("currency") or "RUB"
        price_str = f"{int(price)} ₽" if isinstance(price, (int, float)) else ""
        lines.append(f"• {name} {price_str}")

    if blocks.tips:
        lines.append("")
        lines.append("Советы:")
        for t in blocks.tips[:5]:
            lines.append(f"• {t}")

    # Клавиатура вкладок и действий
    keyboard: List[List[Tuple[str, str]]] = [
        [("Описание", "report_tab:desc"), ("Рекомендации", "report_tab:reco")],
        [("Что купить", "report_tab:buy")],
        [("🛒 Корзина", "cart:open"), ("📄 PDF", "report:latest")],
    ]

    return ("\n".join(lines), keyboard)


def render_report_pdf(blocks: ReportBlocks) -> Dict[str, Any]:
    """Преобразует блоки в snapshot для pdf_v2.
    Возвращает словарь, пригодный для generate_structured_pdf_report.
    """
    snapshot: Dict[str, Any] = {
        "type": "report",
        "profile": {
            "summary": blocks.description,
        },
        "result": {
            "skincare": {},
            "makeup": {},
            "buy": [
                {
                    "name": _plain(p.get("name") or p.get("title") or "Товар"),
                    "price": p.get("price"),
                    "currency": p.get("currency") or "RUB",
                    "id": p.get("id") or p.get("key"),
                    "variant_id": p.get("variant_id"),
                }
                for p in blocks.to_buy[:15]
            ],
            "tips": [t for t in blocks.tips[:5]],
        },
    }
    return snapshot


# Persistence helpers
def _reports_dir(uid: int) -> Path:
    return Path("data") / "reports" / str(uid)


def save_report_blocks(uid: int, report_type: str, blocks: ReportBlocks) -> str:
    d: Dict[str, Any] = {
        "type": report_type,
        "blocks": {
            "title": blocks.title,
            "description": blocks.description,
            "recommendations": blocks.recommendations,
            "to_buy": blocks.to_buy,
            "tips": blocks.tips,
        },
    }
    dir_path = _reports_dir(uid)
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / "last_blocks.json"
    file_path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(file_path)


def load_report_blocks(uid: int) -> Optional[Tuple[str, ReportBlocks]]:
    file_path = _reports_dir(uid) / "last_blocks.json"
    if not file_path.exists():
        return None
    data = json.loads(file_path.read_text(encoding="utf-8"))
    b = data.get("blocks", {})
    blocks = ReportBlocks(
        title=b.get("title", "Отчёт"),
        description=b.get("description", ""),
        recommendations=b.get("recommendations", {}),
        to_buy=b.get("to_buy", []),
        tips=b.get("tips", []),
    )
    return data.get("type", "report"), blocks
