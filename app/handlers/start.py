from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infra.models import User
from app.ui import keyboards, messages
from app.ui.keyboard import build_main_menu

router = Router()


@router.message(CommandStart(), StateFilter(None))
async def start_cmd(message: Message, session: AsyncSession):
    """/start: приветствие и меню"""
    # ensure user exists
    stmt = select(User).where(User.user_id == message.from_user.id)
    existing = (await session.execute(stmt)).scalars().first()
    if not existing:
        session.add(
            User(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name or "",
            )
        )
        await session.commit()
    await message.answer(
        messages.get_welcome_message(message.from_user.first_name),
        reply_markup=build_main_menu(),
    )
    try:
        await message.answer(
            "Нажмите «📄 Мои рекомендации» или «🧪 Пройти анкету».",
            reply_markup=build_main_menu(),
        )
    except Exception:
        pass


@router.message(Command("menu"), StateFilter(None))
async def cmd_menu(message: Message, session: AsyncSession):
    """Показывает главное меню по команде /menu."""
    # Сохраняем пользователя, если его нет
    stmt = select(User).where(User.user_id == message.from_user.id)
    existing = (await session.execute(stmt)).scalars().first()
    if not existing:
        session.add(
            User(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name or "",
            )
        )
        await session.commit()

    await message.answer("Меню", reply_markup=build_main_menu())


@router.message(F.text == messages.LEXICON["btn_navigation"])
@router.message(Command("help", "privacy"))
async def cmd_navigation(message: Message):
    """Обработчик кнопки навигации и команд помощи/приватности."""
    await message.answer(
        "Выберите раздел:", reply_markup=keyboards.create_nav_keyboard()
    )


@router.callback_query(F.data == "nav_help")
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text(messages.get_help_message())
    await callback.answer()


@router.callback_query(F.data == "nav_policy")
async def cb_policy(callback: CallbackQuery):
    await callback.message.edit_text(messages.get_privacy_message())
    await callback.answer()
