import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.infra.models import Base

# Путь к файлу БД
DB_FILE = "data/app.db"
# Строка подключения к SQLite
DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"

# Создаем директорию для БД, если ее нет
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

# Асинхронный "движок" SQLAlchemy
async_engine = create_async_engine(DATABASE_URL, echo=False)

# Асинхронная фабрика сессий
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def create_db_if_not_exists():
    """Создает таблицы в базе данных, если они еще не существуют."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncSession:
    """Зависимость для получения сессии базы данных."""
    async with async_session_maker() as session:
        yield session
