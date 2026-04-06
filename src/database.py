from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

engine = create_async_engine(settings.DB_URL)

async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

# Асинхронный движок с отключённым пулом (NullPool) — полезно для тестов и Celery
engine_null_pool = create_async_engine(settings.DB_URL, poolclass=NullPool)

# Фабрика сессий без пула — используется в фоновых задачах (Celery), чтобы избежать проблем с пулом
async_session_maker_null_pool = async_sessionmaker(bind=engine_null_pool, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
