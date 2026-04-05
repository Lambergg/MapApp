import asyncio
from passlib.context import CryptContext
from pathlib import Path
import sys
from sqlalchemy import text
import logging

sys.path.append(str(Path(__file__).parent.parent))

from src.database import async_session_maker
from src.models.users import UsersOrm

logging.basicConfig(level=logging.INFO)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

AsyncSessionLocal = async_session_maker


async def seed_data():
    async with AsyncSessionLocal() as session:
        async with session.begin():

            await session.execute(text("DELETE FROM users"))

            users = [
                UsersOrm(
                    name="Админ",
                    sname="Админович",
                    age=45,
                    email="admin@example.com",
                    hashed_password=pwd_context.hash("admin123"),
                    role="admin",
                ),
                UsersOrm(
                    name="Менеджер",
                    sname="Менеджеров",
                    age=16,
                    email="manager@example.com",
                    hashed_password=pwd_context.hash("manager123"),
                    role="user",
                ),
                UsersOrm(
                    name="Обычный",
                    sname="Пользователь",
                    age=34,
                    email="user@example.com",
                    hashed_password=pwd_context.hash("user123"),
                    role="user",
                ),
                UsersOrm(
                    name="Гость",
                    sname="Обычный",
                    age=21,
                    email="guest@example.com",
                    hashed_password=pwd_context.hash("guest123"),
                    role="guest",
                ),
            ]

            session.add_all(users)

        await session.commit()
        logging.info(f"Тестовые данные успешно загружены!")


if __name__ == "__main__":
    asyncio.run(seed_data())
