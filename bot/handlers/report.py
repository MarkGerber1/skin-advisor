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
        path = os.path.join("data", "reports", str(uid), "last.pdf")
        if not os.path.exists(path):
            await cb.answer("Отчёт ещё не сформирован", show_alert=True)
            return
        
        # Simplified document sending
        if cb.message:
            try:
                # Use message.answer_document instead of bot.send_document
                await cb.message.answer_document(
                    document=FSInputFile(path),
                    caption="📄 Ваш последний отчёт"
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
