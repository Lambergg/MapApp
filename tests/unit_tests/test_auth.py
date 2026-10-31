import asyncio
from datetime import timedelta

from src.config import settings
from src.init import redis_manager_auth
from src.seed_data import pwd_context
from src.services.auth import AuthService
from src.schemas.users import UserRequestAddDTO, UserAddDTO


def test_create_access_token():
    user_id = 1
    user_role = "admin"
    username = "test_user"

    jwt_token = AuthService().create_access_token(
        user_id, user_role=user_role, username=username
    )
    refresh_token = AuthService().create_refresh_token()
    payload = AuthService().decode_access_token(jwt_token)

    assert jwt_token is not None
    assert refresh_token is not None
    assert isinstance(jwt_token, str)
    assert len(jwt_token) > 0
    assert isinstance(refresh_token, str)
    assert len(refresh_token) > 0
    assert payload["user_id"] == 1
    assert payload["user_role"] == "admin"
    assert payload["username"] == "test_user"
    assert "exp" in payload


async def test_store_refresh_token():
    user_id = 1
    refresh_token = "test_refresh_token"
    key = f"refresh_token:{user_id}"
    rt_key = f"rt:{refresh_token}"
    await redis_manager_auth.set(
        key,
        refresh_token,
        expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS),
    )
    await redis_manager_auth.set(
        rt_key,
        str(user_id),
        expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS),
    )
    assert await redis_manager_auth.get(key) == refresh_token
    assert await redis_manager_auth.get(rt_key) == str(user_id)

async def test_get_refresh_token():
    user_id = 1
    key = f"refresh_token:{user_id}"
    assert await redis_manager_auth.get(key) is None
    await test_store_refresh_token()
    assert await redis_manager_auth.get(key) == "test_refresh_token"

async def test_delete_refresh_token():
    refresh_token = await test_store_refresh_token()
    user_id = 1
    key = f"refresh_token:{user_id}"
    rt_key = f"rt:{refresh_token}"
    user_role = f"user_role:{user_id}"
    await redis_manager_auth.delete(key)
    await redis_manager_auth.delete(rt_key)
    await redis_manager_auth.delete(user_role)
    assert await redis_manager_auth.get(key) is None
    assert await redis_manager_auth.get(rt_key) is None
    assert await redis_manager_auth.get(user_role) is None

async def test_hash_password():
    password = "test_password"
    result = await asyncio.to_thread(pwd_context.hash, password)
    assert result
    assert result != password
    assert pwd_context.verify(password, result) is True
    return result

async def test_register_user(db):
    data = UserRequestAddDTO(
        name="test_name",
        sname="test_sname",
        age=20,
        email="test_email@example.com",
        password="test_password",
    )

    hashed_password = await test_hash_password()

    new_user_data = UserAddDTO(
        name=data.name,
        sname=data.sname,
        age=data.age,
        email=data.email,
        hashed_password=hashed_password,
    )

    await db.users.add(new_user_data)
    await db.commit()

    user = await db.users.get_one(email="test_email@example.com")
    assert user is not None
    if user:
        assert (
                user.name == "test_name"
                and user.sname == "test_sname"
                and user.age == 20
                and user.email == "test_email@example.com"
                and user.is_active is True
                and user.id is not None
                and 0 < user.id == user.id
                and user.role == "guest"
                and user.is_active is True
        )
