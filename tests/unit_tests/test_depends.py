import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, Request
from datetime import timedelta

from src.api.dependencies import (
    get_token, get_current_user_id, get_db_manager, get_db,
    get_current_user_role, get_admin_service, get_auth_service,
    get_event_service, get_chat_service
)
from src.exceptions import NotTokenHTTPException
from src.services.auth import AuthService
from src.services.admin import AdminService
from src.services.events import EventsService
from src.services.chat import ChatService
from src.exceptions import ObjectNotFoundException
from src.config import settings

def test_get_token_success():
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"access_token": "my_secret_token"}

    token = get_token(mock_request)
    assert token == "my_secret_token"

def test_get_token_missing():
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {}

    with pytest.raises(NotTokenHTTPException):
        get_token(mock_request)

@patch("src.api.dependencies.AuthService")
def test_get_current_user_id_success(mock_auth_service_cls):
    # Настраиваем мок AuthService
    mock_service_instance = mock_auth_service_cls.return_value
    mock_service_instance.decode_access_token.return_value = {"user_id": 42}

    user_id = get_current_user_id(token="fake.jwt.token")

    assert user_id == 42
    mock_service_instance.decode_access_token.assert_called_once_with("fake.jwt.token")

@patch("src.api.dependencies.DBManager")
def test_get_db_manager(mock_db_manager_cls):
    get_db_manager()
    mock_db_manager_cls.assert_called_once()

    assert "session_factory" in mock_db_manager_cls.call_args.kwargs

@pytest.mark.asyncio
@patch("src.api.dependencies.get_db_manager")
async def test_get_db_lifecycle(mock_get_db_manager):
    mock_db_instance = MagicMock()
    mock_manager = MagicMock()
    mock_manager.__aenter__ = AsyncMock(return_value=mock_db_instance)
    mock_manager.__aexit__ = AsyncMock()

    mock_get_db_manager.return_value = mock_manager

    db_generator = get_db()

    yielded_db = await anext(db_generator)
    assert yielded_db == mock_db_instance
    mock_manager.__aenter__.assert_awaited_once()

    try:
        await anext(db_generator)
    except StopAsyncIteration:
        pass
    mock_manager.__aexit__.assert_awaited_once()

@pytest.mark.asyncio
@patch("src.api.dependencies.redis_manager_auth")
async def test_get_current_user_role_from_redis(mock_redis):
    mock_redis.get = AsyncMock(return_value="admin")
    mock_db = MagicMock()

    role = await get_current_user_role(db=mock_db, user_id=1)

    assert role == "admin"
    mock_redis.get.assert_awaited_once_with("user_role:1")

    mock_db.users.get_one.assert_not_called()

@pytest.mark.asyncio
@patch("src.api.dependencies.redis_manager_auth")
async def test_get_current_user_role_from_db(mock_redis):
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()

    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.role = "user"
    mock_db.users.get_one = AsyncMock(return_value=mock_user)

    role = await get_current_user_role(db=mock_db, user_id=2)

    assert role == "user"
    mock_db.users.get_one.assert_awaited_once_with(id=2)
    mock_redis.set.assert_awaited_once_with(
        "user_role:2",
        "user",
        expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)
    )

@pytest.mark.asyncio
@patch("src.api.dependencies.redis_manager_auth")
async def test_get_current_user_role_not_found(mock_redis):
    mock_redis.get = AsyncMock(return_value=None)
    mock_db = MagicMock()
    mock_db.users.get_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_role(db=mock_db, user_id=3)

    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
@patch("src.api.dependencies.redis_manager_auth")
async def test_get_current_user_role_db_error(mock_redis):
    mock_redis.get = AsyncMock(return_value=None)
    mock_db = MagicMock()
    mock_db.users.get_one = AsyncMock(side_effect=Exception("DB error"))

    with pytest.raises(ObjectNotFoundException):
        await get_current_user_role(db=mock_db, user_id=4)

@pytest.mark.asyncio
async def test_get_admin_service():
    mock_db = MagicMock()
    service = await get_admin_service(db=mock_db)

    assert isinstance(service, AdminService)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_get_auth_service():
    mock_db = MagicMock()
    service = await get_auth_service(db=mock_db)

    assert isinstance(service, AuthService)
    assert service.db == mock_db

@pytest.mark.asyncio
async def test_get_event_service():
    mock_db = MagicMock()
    service = await get_event_service(db=mock_db)

    assert isinstance(service, EventsService)
    assert service.db == mock_db

@pytest.mark.asyncio
@patch("src.api.dependencies.manager")
async def test_get_chat_service(mock_manager):
    service = await get_chat_service()

    assert isinstance(service, ChatService)
    assert service.manager == mock_manager