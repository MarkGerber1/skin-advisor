from __future__ import annotations

from typing import List, Dict, Any

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils.security import safe_edit_message_text
from bot.ui.report_builder import load_report_blocks


router = Router()

PAGE_SIZE = 8


def _format_price(price: Any, currency: str | None) -> str:
    try:
        p = float(price)
    except Exception:
        return ""
    if (currency or "RUB").upper() in ("RUB", "RUR"):
        return f"{int(p)} ₽"
    return f"{p:.2f} {currency or 'RUB'}"


def _build_tabs_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Описание", callback_data="report_tab:desc"),
                InlineKeyboardButton(text="Рекомендации", callback_data="report_tab:reco"),
            ],
            [InlineKeyboardButton(text="Что купить", callback_data="report_tab:buy:1")],
            [
                InlineKeyboardButton(text="🛒 Корзина", callback_data="cart:open"),
                InlineKeyboardButton(text="📄 PDF", callback_data="report:latest"),
            ],
        ]
    )
    return kb


@router.callback_query(F.data.startswith("report_tab:"))
async def handle_report_tabs(cb: CallbackQuery) -> None:
    try:
        uid = int(cb.from_user.id) if cb.from_user and cb.from_user.id else 0
        loaded = load_report_blocks(uid)
        if not loaded:
            await cb.answer("Отчёт ещё не сформирован", show_alert=True)
            return
        report_type, blocks = loaded

        data = cb.data
        if data.startswith("report_tab:desc"):
            text_lines: List[str] = [blocks.title, "", blocks.description]
            text = "\n".join(text_lines)
            await safe_edit_message_text(
                cb.message.bot,
                cb.message.chat.id,
                cb.message.message_id,
                text,
                reply_markup=_build_tabs_kb(),
            )
            await cb.answer()
            return

        if data.startswith("report_tab:reco"):
            lines: List[str] = [blocks.title, "", "Рекомендации:"]
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
            text = "\n".join(lines)
            await safe_edit_message_text(
                cb.message.bot,
                cb.message.chat.id,
                cb.message.message_id,
                text,
                reply_markup=_build_tabs_kb(),
            )
            await cb.answer()
            return

        if data.startswith("report_tab:buy"):
            # format: report_tab:buy or report_tab:buy:<page>
            parts = data.split(":")
            page = 1
            if len(parts) >= 3:
                try:
                    page = int(parts[2])
                except Exception:
                    page = 1

            products: List[Dict[str, Any]] = list(blocks.to_buy or [])
            total = len(products)
            if total == 0:
                await cb.answer("Нет товаров в подборке", show_alert=True)
                return
            total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages

            start = (page - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            page_items = products[start:end]

            # Text
            lines: List[str] = [blocks.title, "", "Что купить:"]
            for p in page_items:
                name = p.get("name") or p.get("title") or "Товар"
                price = _format_price(p.get("price"), p.get("currency"))
                lines.append(f"• {name} {price}")
            lines.append("")
            lines.append(f"Страница {page}/{total_pages}")
            text = "\n".join(lines)

            # Keyboard
            kbl: List[List[InlineKeyboardButton]] = []
            for p in page_items:
                product_id = p.get("id") or p.get("key") or ""
                variant_id = p.get("variant_id") or "none"
                btn = InlineKeyboardButton(
                    text="🛒 В корзину",
                    callback_data=f"cart:add:{product_id}:{variant_id}",
                )
                kbl.append([btn])

            # Pagination row
            nav_row: List[InlineKeyboardButton] = []
            if page > 1:
                nav_row.append(
                    InlineKeyboardButton(text="◀", callback_data=f"report_tab:buy:{page-1}")
                )
            nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
            if page < total_pages:
                nav_row.append(
                    InlineKeyboardButton(text="▶", callback_data=f"report_tab:buy:{page+1}")
                )
            if nav_row:
                kbl.append(nav_row)

            # Actions row
            kbl.append(
                [
                    InlineKeyboardButton(text="🛒 Корзина", callback_data="cart:open"),
                    InlineKeyboardButton(text="📄 PDF", callback_data="report:latest"),
                ]
            )
            kbl.insert(
                0,
                [
                    InlineKeyboardButton(text="Описание", callback_data="report_tab:desc"),
                    InlineKeyboardButton(text="Рекомендации", callback_data="report_tab:reco"),
                ],
            )

            kb = InlineKeyboardMarkup(inline_keyboard=kbl)
            await safe_edit_message_text(
                cb.message.bot,
                cb.message.chat.id,
                cb.message.message_id,
                text,
                reply_markup=kb,
            )
            await cb.answer()
            return

        await cb.answer()
    except Exception:
        await cb.answer("Ошибка отчёта", show_alert=True)
