from __future__ import annotations

from typing import List

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from engine.cart_store import CartStore, CartItem


router = Router()
store = CartStore()


def _user_id(msg: Message | None) -> int | None:
    if msg and msg.from_user and msg.from_user.id:
        return int(msg.from_user.id)
    return None


@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart(cb: CallbackQuery, state: FSMContext) -> None:
    if not cb.data:
        await cb.answer()
        return
    msg = cb.message
    if not isinstance(msg, Message):
        await cb.answer()
        return
    user_id = _user_id(msg)
    if not user_id:
        await cb.answer("Неизвестный пользователь", show_alert=True)
        return
    pid = cb.data.split(":", 2)[2]
    # сохраняем минимальные данные; полное наполнение возможно при отдельном просмотре карточки
    store.add(user_id, CartItem(product_id=pid, qty=1))
    await cb.answer("Добавлено в корзину")


@router.message(F.text == "🛒 Моя подборка")
async def show_cart(m: Message, state: FSMContext) -> None:
    user_id = _user_id(m)
    if not user_id:
        await m.answer("Неизвестный пользователь")
        return
    items: List[CartItem] = store.get(user_id)
    if not items:
        await m.answer("Ваша корзина пуста. Добавьте товары из рекомендаций.")
        return
    lines = ["🛒 Ваша корзина:"]
    total = 0.0
    for it in items:
        price = it.price or 0.0
        qty = it.qty
        total += price * qty
        title = it.name or it.product_id
        lines.append(f"— {title} × {qty}")
    lines.append("")
    lines.append(f"Итого позиций: {len(items)}")
    await m.answer("\n".join(lines))


