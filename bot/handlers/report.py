from __future__ import annotations

import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile


router = Router()


def _user_id(cb: CallbackQuery) -> int | None:
    if cb.from_user and cb.from_user.id:
        return int(cb.from_user.id)
    return None


@router.callback_query(F.data == "report:latest")
async def send_latest_report(cb: CallbackQuery) -> None:
    uid = _user_id(cb)
    if not uid:
        await cb.answer()
        return
    path = os.path.join("data", "reports", str(uid), "last.pdf")
    if not os.path.exists(path):
        await cb.answer("Отчёт ещё не сформирован", show_alert=True)
        return
    try:
        await cb.message.answer_document(document=FSInputFile(path), caption="Ваш последний отчёт")
    finally:
        await cb.answer()




