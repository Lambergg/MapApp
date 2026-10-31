from datetime import datetime

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.events import EventsService
from src.schemas.events import EventsAddDTO, EventsUpdateDTO, EventsFilterDTO
from src.exceptions import (
    WrongUserDataHTTPException, EventIndexWrongHTTPException,
    EventNotFoundHTTPException, EventsNotFoundHTTPException,
    EventsAlreadyExistsHTTPException, EventDataEmptyHTTPException
)
from src.exceptions import ObjectNotFoundException, ObjectAlreadyExistsException, ObjectEmptyDataException

@pytest.fixture
def mock_db():
    db = MagicMock()

    db.events = MagicMock()
    db.events.add = AsyncMock()
    db.events.get_all = AsyncMock()
    db.events.get_one = AsyncMock()
    db.events.get_events_by_user_id = AsyncMock()
    db.events.get_filtered_by_time = AsyncMock()
    db.events.edit = AsyncMock()
    db.events.delete = AsyncMock()
    db.commit = AsyncMock()
    return db

@pytest.fixture
def service(mock_db):
    return EventsService(db=mock_db)

@pytest.mark.asyncio
async def test_create_events_success(service, mock_db):
    data = EventsAddDTO(
        title="Новое событие",
        descriptions="Описание",
        category="День рождения",
        address="Адрес",
        date=datetime.now(),
        max_users=10)
    expected_event = MagicMock()
    mock_db.events.add.return_value = expected_event

    result = await service.create_events(data, role="admin")

    mock_db.events.add.assert_awaited_once_with(data)
    mock_db.commit.assert_awaited_once()
    assert result == expected_event

@pytest.mark.asyncio
async def test_create_events_wrong_role(service):
    data = EventsAddDTO(
        title="Новое событие",
        descriptions="Описание",
        category="День рождения",
        address="Адрес",
        date=datetime.now(),
        max_users=10
    )
    with pytest.raises(WrongUserDataHTTPException):
        await service.create_events(data, role="unknown_role")

@pytest.mark.asyncio
async def test_create_events_already_exists(service, mock_db):
    data = EventsAddDTO(
        title="Новое событие",
        descriptions="Описание",
        category="День рождения",
        address="Адрес",
        date=datetime.now(),
        max_users=10
    )
    mock_db.events.add.side_effect = ObjectAlreadyExistsException()

    with pytest.raises(EventsAlreadyExistsHTTPException):
        await service.create_events(data, role="admin")

    mock_db.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_get_events_success(service, mock_db):
    mock_db.events.get_all.return_value = [MagicMock(), MagicMock()]

    result = await service.get_events(role="user")

    mock_db.events.get_all.assert_awaited_once()
    assert len(result) == 2

@pytest.mark.asyncio
async def test_get_events_wrong_role(service):
    with pytest.raises(WrongUserDataHTTPException):
        await service.get_events(role="banned")

@pytest.mark.asyncio
async def test_get_my_events_success(service, mock_db):
    mock_db.events.get_events_by_user_id.return_value = [MagicMock()]

    result = await service.get_my_events(user_id=1, role="user")

    mock_db.events.get_events_by_user_id.assert_awaited_once_with(user_id=1)
    assert len(result) == 1

@pytest.mark.asyncio
async def test_get_my_events_not_found(service, mock_db):
    mock_db.events.get_events_by_user_id.return_value = []

    with pytest.raises(EventsNotFoundHTTPException):
        await service.get_my_events(user_id=1, role="user")

@pytest.mark.asyncio
async def test_get_one_event_success(service, mock_db):
    mock_event = MagicMock()
    mock_db.events.get_one.return_value = mock_event

    result = await service.get_one_event(event_id=1, role="user")

    mock_db.events.get_one.assert_awaited_once_with(id=1)
    assert result == mock_event

@pytest.mark.asyncio
async def test_get_one_event_wrong_index(service):
    with pytest.raises(EventIndexWrongHTTPException):
        await service.get_one_event(event_id=0, role="user")

@pytest.mark.asyncio
async def test_get_one_event_not_found(service, mock_db):
    mock_db.events.get_one.side_effect = ObjectNotFoundException()

    with pytest.raises(EventNotFoundHTTPException):
        await service.get_one_event(event_id=99, role="user")

@pytest.mark.asyncio
async def test_get_filtered_by_time_success(service, mock_db):
    mock_db.events.get_filtered_by_time.return_value = [MagicMock()]
    pagination = MagicMock(page=2, per_page=10)
    filters = EventsFilterDTO(title="Test", category=None, address=None, date=None, max_users=None)

    result = await service.get_filtered_by_time(pagination, filters, role="user")

    mock_db.events.get_filtered_by_time.assert_awaited_once_with(
        limit=10,
        offset=10,
        title="Test",
        category=None,
        address=None,
        date=None,
        max_users=None
    )
    assert len(result) == 1

@pytest.mark.asyncio
async def test_edit_event_success(service, mock_db):
    data = EventsUpdateDTO(title="Updated", category="Updated", address="Updated", max_users=100)
    mock_db.events.get_one.return_value = MagicMock()

    await service.edit_event(event_id=1, data=data, role="admin")

    mock_db.events.get_one.assert_awaited_once_with(id=1)
    mock_db.events.edit.assert_awaited_once_with(data, id=1, exclude_unset=False)
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_edit_event_not_found(service, mock_db):
    data = EventsUpdateDTO(title="Updated", category="Updated", address="Updated", max_users=100)
    mock_db.events.get_one.side_effect = ObjectNotFoundException()

    with pytest.raises(EventsNotFoundHTTPException):
        await service.edit_event(event_id=1, data=data, role="admin")

@pytest.mark.asyncio
async def test_edit_event_empty_data(service, mock_db):
    data = EventsUpdateDTO(title="Updated", category="Updated", address="Updated", max_users=100)
    mock_db.events.get_one.return_value = MagicMock()
    mock_db.events.edit.side_effect = ObjectEmptyDataException()

    with pytest.raises(EventDataEmptyHTTPException):
        await service.edit_event(event_id=1, data=data, role="admin")

    mock_db.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_delete_event_success(service, mock_db):
    mock_db.events.get_one.return_value = MagicMock()

    await service.delete_event(event_id=1, role="admin")

    mock_db.events.get_one.assert_awaited_once_with(id=1)
    mock_db.events.delete.assert_awaited_once_with(id=1)
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_event_not_found(service, mock_db):
    mock_db.events.get_one.side_effect = ObjectNotFoundException()

    with pytest.raises(EventNotFoundHTTPException):
        await service.delete_event(event_id=99, role="admin")

    mock_db.events.delete.assert_not_awaited()