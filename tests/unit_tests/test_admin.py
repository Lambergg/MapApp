from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.exceptions import (AdminOnlyAccessHTTPException,
                            ObjectNotFoundException,
                            UserIndexWrongHTTPException,
                            UserNotFoundHTTPException)
from src.schemas.users import UserFilterDTO, UserPutDTO
from src.services.admin import AdminService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.admin = MagicMock()
    db.admin.get_filtered_by_time = AsyncMock()

    db.users = MagicMock()
    db.users.get_one = AsyncMock()
    db.users.edit = AsyncMock()
    db.users.delete = AsyncMock()
    db.users.deactivate_user = AsyncMock()

    db.commit = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    return AdminService(db=mock_db)


@pytest.mark.asyncio
async def test_get_filtered_by_time_success(service, mock_db):
    mock_db.admin.get_filtered_by_time.return_value = [MagicMock()]
    pagination = MagicMock(page=2, per_page=10)
    filters = UserFilterDTO(email="test@test.com", name="Ivan", sname="Ivanov")

    result = await service.get_filtered_by_time(
        pagination, filters, role="admin"
    )

    mock_db.admin.get_filtered_by_time.assert_awaited_once_with(
        limit=10,
        offset=10,  # (2 - 1) * 10
        email="test@test.com",
        name="Ivan",
        sname="Ivanov",
    )
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_filtered_by_time_not_admin(service):
    pagination = MagicMock(page=1, per_page=10)
    filters = UserFilterDTO(email=None, name=None, sname=None)

    with pytest.raises(AdminOnlyAccessHTTPException):
        await service.get_filtered_by_time(pagination, filters, role="user")


@pytest.mark.asyncio
async def test_get_user_success(service, mock_db):
    mock_user = MagicMock()
    mock_db.users.get_one.return_value = mock_user

    result = await service.get_user(user_id=1, role="admin")

    mock_db.users.get_one.assert_awaited_once_with(id=1)
    assert result == mock_user


@pytest.mark.asyncio
async def test_get_user_wrong_index(service):
    with pytest.raises(UserIndexWrongHTTPException):
        await service.get_user(user_id=0, role="admin")


@pytest.mark.asyncio
async def test_get_user_not_admin(service):
    with pytest.raises(AdminOnlyAccessHTTPException):
        await service.get_user(user_id=1, role="user")


@pytest.mark.asyncio
async def test_edit_user_role_success(service, mock_db):
    mock_db.users.get_one.return_value = MagicMock()
    data = UserPutDTO(role="moderator", is_active=True)

    await service.edit_user_role(user_id=1, data=data, role="admin")

    mock_db.users.get_one.assert_awaited_once_with(id=1)
    mock_db.users.edit.assert_awaited_once_with(data, id=1, exclude_unset=False)
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_edit_user_role_user_not_found(service, mock_db):
    mock_db.users.get_one.side_effect = ObjectNotFoundException()
    data = UserPutDTO(role="user", is_active=True)

    with pytest.raises(UserNotFoundHTTPException):
        await service.edit_user_role(user_id=99, data=data, role="admin")

    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_user_role_not_admin(service):
    data = UserPutDTO(role="user", is_active=True)
    with pytest.raises(AdminOnlyAccessHTTPException):
        await service.edit_user_role(user_id=1, data=data, role="user")


@pytest.mark.asyncio
@patch("src.services.admin.delete_refresh_token")
async def test_delete_user_success(mock_delete_rt, service, mock_db):
    mock_db.users.get_one.return_value = MagicMock()

    await service.delete_user(user_id=1, role="admin")

    mock_db.users.get_one.assert_awaited_once_with(id=1)
    mock_delete_rt.assert_awaited_once_with(1)  # Проверяем очистку токенов
    mock_db.users.delete.assert_awaited_once_with(id=1)
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_user_wrong_index(service):
    with pytest.raises(UserIndexWrongHTTPException):
        await service.delete_user(user_id=-5, role="admin")


@pytest.mark.asyncio
async def test_delete_user_not_admin(service):
    with pytest.raises(AdminOnlyAccessHTTPException):
        await service.delete_user(user_id=1, role="guest")


@pytest.mark.asyncio
@patch("src.services.admin.delete_refresh_token")
async def test_soft_delete_user_success(mock_delete_rt, service, mock_db):
    mock_db.users.get_one.return_value = MagicMock()

    await service.soft_delete_user(user_id=1, role="admin")

    mock_db.users.get_one.assert_awaited_once_with(id=1)
    mock_db.users.deactivate_user.assert_awaited_once_with(1)
    mock_delete_rt.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_soft_delete_user_not_found(service, mock_db):
    mock_db.users.get_one.side_effect = ObjectNotFoundException()

    with pytest.raises(UserNotFoundHTTPException):
        await service.soft_delete_user(user_id=99, role="admin")
