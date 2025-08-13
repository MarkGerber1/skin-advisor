import json
import aiofiles
from aiogram import Router, F
from aiogram.filters import Command, Filter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.infra.models import User, SurveyResponse, DiagnosisResult
from app.infra.settings import get_settings
from app.domain.recommender import reload_products
from app.ui import messages


class AdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        settings = get_settings()
        return message.from_user.id in settings.bot.admin_ids


router = Router()
router.message.filter(AdminFilter())


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer(messages.LEXICON['admin_welcome'].format(user_name=message.from_user.first_name))


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession):
    total_users = await session.scalar(select(func.count(User.id)))
    completed_surveys = await session.scalar(select(func.count(SurveyResponse.id)))
    diagnoses_count = await session.scalar(select(func.count(DiagnosisResult.id)))

    stats_text = messages.LEXICON['admin_stats'].format(
        total_users=total_users,
        completed_surveys=completed_surveys,
        diagnoses_count=diagnoses_count
    )
    await message.answer(stats_text)


@router.message(Command("update_products"))
async def cmd_update_products(message: Message):
    await message.answer(messages.LEXICON['admin_update_products_prompt'])


@router.message(F.document)
async def handle_product_file(message: Message):
    if message.document.file_name != 'products.json' or message.document.mime_type != 'application/json':
        await message.answer("Пожалуйста, загрузите файл с именем `products.json` и типом `application/json`.")
        return

    try:
        file = await message.bot.get_file(message.document.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        content_str = file_bytes.read().decode('utf-8')

        # Валидируем JSON
        json.loads(content_str)

        # Сохраняем
        async with aiofiles.open('data/products.json', 'w', encoding='utf-8') as f:
            await f.write(content_str)

        # Перезагружаем в память
        count = reload_products()
        await message.answer(f"✅ Каталог продуктов успешно обновлен! Загружено записей: {count}")
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении каталога. Проверьте формат JSON файла.\nОшибка: {e}")
