# ruff: noqa
import json
from typing import AsyncGenerator
from unittest import mock

mock.patch(
    "fastapi_cache.decorator.cache", lambda *args, **kwargs: lambda f: f
).start()

import pytest
from httpx import AsyncClient, ASGITransport

from src.api.dependencies import get_db
from src.main import app
from src.config import settings
from src.database import Base, engine_null_pool, async_session_maker_null_pool
from src.models import *
from src.schemas.events import EventsAddDTO
from src.schemas.users import UserAddDTO
from src.utils.db_manager import DBManager


@pytest.fixture(scope="session", autouse=True)
def check_test_mode():
    assert settings.mode == "TEST"


async def get_db_null_pool():
    async with DBManager(session_factory=async_session_maker_null_pool) as db:
        yield db


@pytest.fixture()
async def db() -> AsyncGenerator[DBManager, None]:
    async for db in get_db_null_pool():
        yield db


app.dependency_overrides[get_db] = get_db_null_pool


@pytest.fixture(scope="session", autouse=True)
async def setup_database(check_test_mode):
    async with engine_null_pool.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    with open("tests/mock_events.json", encoding="utf-8") as file_events:
        events = json.load(file_events)
    with open("tests/mock_users.json", encoding="utf-8") as file_users:
        users = json.load(file_users)

    events = [EventsAddDTO.model_validate(event) for event in events]
    users = [UserAddDTO.model_validate(user) for user in users]

    async with DBManager(session_factory=async_session_maker_null_pool) as db_:
        await db_.events.add_bulk(events)
        await db_.users.add_bulk(users)
        await db_.commit()


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
async def register_user(ac: AsyncClient, setup_database):
    await ac.post(
        "/auth/register",
        json={
            "name": "test_user",
            "sname": "User",
            "age": 25,
            "email": "test@test.com",
            "password": "test1234",
        },
    )


@pytest.fixture(scope="session")
async def authenticated_ac(register_user, ac: AsyncClient):
    await ac.post(
        "/auth/login", json={"email": "test@test.com", "password": "test1234"}
    )
    assert ac.cookies["access_token"]
    yield ac
