import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from fastapi import Response, Request
import jwt

from src.services.auth import AuthService
from src.schemas.users import UserRequestAddDTO, UserLoginDTO, UserAddDTO
from src.config import settings
from src.exceptions import (
    UserPasswordToShortHTTPException, UserAllReadyExistsHTTPException,
    UserNotRegisterHTTPException, WrongPasswordHTTPException, UserIsBannedHTTPException,
    WrongRefreshTokenHTTPException, RefreshTokenRequiredHTTPException,
    UserDeleteTokenHTTPException, ExpiredSignatureErrorHTTPException, TokenWrongTypeHTTPException
)
from src.exceptions import ObjectAlreadyExistsException, ObjectNotFoundException

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.users = MagicMock()
    db.users.get_user_with_hashed_password = AsyncMock()
    db.users.get_one = AsyncMock()
    db.users.add = AsyncMock()
    db.commit = AsyncMock()
    return db

@pytest.fixture
def service(mock_db):
    return AuthService(db=mock_db)

@pytest.fixture
def mock_redis():
    with patch("src.services.auth.redis_manager_auth") as mock:
        mock.set = AsyncMock()
        mock.get = AsyncMock()
        mock.delete = AsyncMock()
        yield mock

def test_create_access_token(service):
    token = service.create_access_token(user_id=1, user_role="admin", username="Ivan")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    assert payload["user_id"] == 1
    assert payload["user_role"] == "admin"
    assert payload["username"] == "Ivan"
    assert payload["type"] == "access"

def test_decode_access_token_success(service):
    token = service.create_access_token(1, "user", "Test")
    payload = service.decode_access_token(token)
    assert payload["user_id"] == 1

def test_decode_access_token_wrong_type(service):
    to_encode = {"type": "refresh", "user_id": 1, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(TokenWrongTypeHTTPException):
        service.decode_access_token(token)

def test_decode_access_token_expired(service):
    to_encode = {"type": "access", "exp": datetime.now(timezone.utc) - timedelta(minutes=5)}
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(ExpiredSignatureErrorHTTPException):
        service.decode_access_token(token)

@pytest.mark.asyncio
async def test_store_refresh_token(service, mock_redis):
    await service.store_refresh_token(user_id=1, refresh_token="rt_123")

    assert mock_redis.set.call_count == 2
    mock_redis.set.assert_any_call("refresh_token:1", "rt_123", expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS))
    mock_redis.set.assert_any_call("rt:rt_123", "1", expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS))

@pytest.mark.asyncio
async def test_get_refresh_token(service, mock_redis):
    mock_redis.get.return_value = "rt_123"
    token = await service.get_refresh_token(user_id=1)

    mock_redis.get.assert_awaited_once_with("refresh_token:1")
    assert token == "rt_123"

@pytest.mark.asyncio
async def test_delete_refresh_token(service, mock_redis):
    await service.delete_refresh_token(user_id=1, refresh_token="rt_123")

    assert mock_redis.delete.call_count == 3
    mock_redis.delete.assert_any_call("refresh_token:1")
    mock_redis.delete.assert_any_call("rt:rt_123")
    mock_redis.delete.assert_any_call("user_role:1")

@pytest.mark.asyncio
async def test_hash_and_verify_password(service):
    password = "secret_password"
    hashed = await service.hash_password(password)

    assert hashed != password
    assert await service.verify_password(password, hashed) is True
    assert await service.verify_password("wrong_password", hashed) is False

@pytest.mark.asyncio
@patch("src.services.auth.send_email")
async def test_register_user_success(mock_send_email, service, mock_db, mock_redis):
    data = UserRequestAddDTO(
        name="Test", sname="Test", age=20, email="test@test.com", password="password123"
    )

    await service.register_user(data)

    mock_db.users.add.assert_awaited_once()
    mock_db.commit.assert_awaited_once()

    mock_send_email.delay.assert_called_once()
    args, kwargs = mock_send_email.delay.call_args
    assert kwargs["email"] == "test@test.com"

@pytest.mark.asyncio
async def test_register_user_already_exists(service, mock_db):
    data = UserRequestAddDTO(name="Test", sname="Test", age=20, email="test@test.com", password="password123")
    mock_db.users.add.side_effect = ObjectAlreadyExistsException()

    with pytest.raises(UserAllReadyExistsHTTPException):
        await service.register_user(data)

@pytest.mark.asyncio
async def test_login_user_success(service, mock_db, mock_redis):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.role = "user"
    mock_user.name = "Ivan"
    mock_user.is_active = True

    mock_user.hashed_password = await service.hash_password("password123")

    mock_db.users.get_user_with_hashed_password.return_value = mock_user
    mock_response = MagicMock(spec=Response)
    data = UserLoginDTO(email="test@test.com", password="password123")

    result = await service.login_user(data, mock_response)

    assert "access_token" in result
    assert "refresh_token" in result
    assert mock_response.set_cookie.call_count == 2

    mock_redis.set.assert_any_call("user_role:1", "user", expire=timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS))

@pytest.mark.asyncio
async def test_login_user_not_found(service, mock_db):
    mock_db.users.get_user_with_hashed_password.return_value = None
    mock_response = MagicMock(spec=Response)
    data = UserLoginDTO(email="notfound@test.com", password="password123")

    with pytest.raises(UserNotRegisterHTTPException):
        await service.login_user(data, mock_response)

@pytest.mark.asyncio
async def test_login_user_banned(service, mock_db):
    mock_user = MagicMock()
    mock_user.is_active = False
    mock_user.hashed_password = await service.hash_password("password123")
    mock_db.users.get_user_with_hashed_password.return_value = mock_user
    mock_response = MagicMock(spec=Response)
    data = UserLoginDTO(email="banned@test.com", password="password123")

    with pytest.raises(UserIsBannedHTTPException):
        await service.login_user(data, mock_response)

@pytest.mark.asyncio
async def test_logout_user_success(service, mock_redis):
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"access_token": "at", "refresh_token": "rt"}
    mock_response = MagicMock(spec=Response)

    await service.logout_user(mock_request, mock_response, user_id=1)

    assert mock_response.delete_cookie.call_count == 2
    assert mock_redis.delete.call_count == 3

@pytest.mark.asyncio
async def test_refresh_tokens_success(service, mock_db, mock_redis):
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"refresh_token": "old_rt"}
    mock_response = MagicMock(spec=Response)

    # Настраиваем Redis
    mock_redis.get.side_effect = lambda key: {
        "rt:old_rt": "1",
        "user_role:1": "admin"
    }.get(key)

    mock_user = MagicMock()
    mock_user.name = "Admin"
    mock_db.users.get_one.return_value = mock_user

    result = await service.refresh_tokens(mock_request, mock_response)

    assert "access_token" in result
    assert result["refresh_token"] != "old_rt"

    mock_redis.delete.assert_any_call("rt:old_rt")

@pytest.mark.asyncio
async def test_refresh_tokens_missing(service):
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {}

    with pytest.raises(RefreshTokenRequiredHTTPException):
        await service.refresh_tokens(mock_request, MagicMock())

@pytest.mark.asyncio
async def test_get_me_success(service, mock_db):
    mock_user = MagicMock()
    mock_user.is_active = True
    mock_db.users.get_one_with_events = AsyncMock(return_value=mock_user)

    user = await service.get_me(user_id=1)
    assert user == mock_user

@pytest.mark.asyncio
async def test_get_me_banned(service, mock_db):
    mock_user = MagicMock()
    mock_user.is_active = False
    mock_db.users.get_one_with_events = AsyncMock(return_value=mock_user)

    with pytest.raises(UserIsBannedHTTPException):
        await service.get_me(user_id=1)