from __future__ import annotations

import os
from aiogram import Router, F
from aiogram.types import CallbackQuery

try:
    from aiogram.types import FSInputFile
except ImportError:
    from aiogram.types import InputFile as FSInputFile


router = Router()


def _user_id(cb: CallbackQuery) -> int | None:
    if cb.from_user and cb.from_user.id:
        return int(cb.from_user.id)
    return None


@router.callback_query(F.data == "report:latest")
async def send_latest_report(cb: CallbackQuery) -> None:
    try:
        uid = _user_id(cb)
        if not uid:
            await cb.answer()
            return
        # Пытаемся отправить v2 PDF, затем simple/minimal, затем текстовую версию отчёта
        base_dir = os.path.join("data", "reports", str(uid))
        candidates = [
            os.path.join(base_dir, "last_v2.pdf"),
            os.path.join(base_dir, "last_v2_simple.pdf"),
            os.path.join(base_dir, "last_v2_minimal.pdf"),
            os.path.join(base_dir, "last.pdf"),
        ]

        path = next((p for p in candidates if os.path.exists(p)), None)
        if not path:
            # Фолбэк: отправим текстовую версию из сохранённых блоков
            try:
                from bot.ui.report_builder import load_report_blocks, render_report_telegram

                loaded = load_report_blocks(uid)
                if not loaded:
                    await cb.answer("Отчёт ещё не сформирован", show_alert=True)
                    return
                _, blocks = loaded
                text, kb_spec = render_report_telegram(blocks)
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=lbl, callback_data=cbdata) for (lbl, cbdata) in row]
                        for row in kb_spec
                    ]
                )
                await cb.message.answer(text, reply_markup=kb)
                await cb.answer("📄 Текстовая версия отчёта отправлена")
                return
            except Exception as fb_err:
                print(f"❌ Fallback report text error: {fb_err}")
                await cb.answer("Отчёт ещё не сформирован", show_alert=True)
                return
        if not os.path.exists(path):
            await cb.answer("Отчёт ещё не сформирован", show_alert=True)
            return

        # Отправка документа
        if cb.message:
            try:
                # Use message.answer_document instead of bot.send_document
                await cb.message.answer_document(
                    document=FSInputFile(path), caption="📄 Ваш последний отчёт"
                )
                await cb.answer("📄 Отчёт отправлен!")
            except Exception as send_error:
                print(f"❌ Error sending document: {send_error}")
                await cb.answer("❌ Ошибка при отправке отчёта", show_alert=True)
        else:
            await cb.answer("❌ Ошибка: не найдено сообщение", show_alert=True)

    except Exception as e:
        print(f"❌ Error in send_latest_report: {e}")
        await cb.answer("❌ Ошибка при отправке отчёта", show_alert=True)
