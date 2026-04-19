from fastapi import APIRouter, Body, status, Path, Query
from fastapi_cache.decorator import cache

from src.api.dependencies import DBDep, UserRoleDep, PaginationDep, UserIdDep
from src.exceptions import WrongUserDataHTTPException
from src.schemas.events import EventsAddDTO, EventsUpdateDTO
from src.services.events import EventsService

router = APIRouter(prefix="/events", tags=["События"])


@router.get(
    "",
    summary="Получить список всех событиий",
    description="<h1>Возвращает список всех событий</h1>",
)
@cache(expire=10)
async def get_events(
    db: DBDep,
    role: UserRoleDep,
):
    if role not in ("admin", "user", "guest"):
        raise WrongUserDataHTTPException

    return await EventsService(db).get_events()


@router.get(
    "/me",
    summary="Получить все события пользователя",
    description="<h1>Получаем все события пользователя</h1>",
)
@cache(expire=10)
async def get_my_bookings(user_id: UserIdDep, db: DBDep):
    return await EventsService(db).get_my_events(user_id)


@router.get(
    "/search",
    summary="Поиск по событиям",
    description="<h1>Поиск событий по фильтрам.</h1>",
)
@cache(expire=10)
async def get_search_events(
    db: DBDep,
    pagination: PaginationDep,
    role: UserRoleDep,
    title: str | None = Query(None, description="Название события"),
    category: str | None = Query(None, description="Категория события"),
    address: str | None = Query(None, description="Адрес события"),
    date: str | None = Query(None, description="Дата/время события"),
    max_users: int | None = Query(None, description="Максимальное количество участников события"),
):
    if role not in ("admin", "user", "guest"):
        raise WrongUserDataHTTPException

    return await EventsService(db).get_filtered_by_time(
        pagination,
        title,
        category,
        address,
        date,
        max_users,
    )


@router.post(
    "",
    summary="Добавить событие",
    description="<h1>Добавляет событие</h1>",
    status_code=status.HTTP_200_OK,
)
async def create_events(
    db: DBDep,
    role: UserRoleDep,
    data: EventsAddDTO = Body(
        openapi_examples={
            "1": {
                "summary": "Новое событие",
                "value": {
                    "title": "Поход в театр",
                    "descriptions": "Какое то описание",
                    "category": "Досуг",
                    "address": "Фонтанка 32",
                    "date": "2026-01-01T17:00:00",
                    "max_users": 4,
                },
            },
        }
    ),
):
    if role not in ("admin", "user", "guest"):
        raise WrongUserDataHTTPException

    events = await EventsService(db).create_events(data)
    return {"Status": status.HTTP_200_OK, "data": events}


@router.put(
    "/edit_events/{event_id}",
    summary="Обновление события",
    description="<h1>Обновляем событие. Нужно передать ID и новые данные.</h1>",
    status_code=status.HTTP_200_OK,
)
async def edit_event(
    role: UserRoleDep,
    db: DBDep,
    event_id: int = Path(..., le=2147483647),
    event_data: EventsUpdateDTO = Body(
        openapi_examples={
            "1": {
                "summary": "Пример данных",
                "value": {
                    "title": "Поход в бар",
                    "descriptions": "Какое то описание",
                    "category": "Досуг",
                    "address": "Думская 22",
                    "date": "2027-12-31T18:00:00",
                    "max_users": 2,
                },
            },
        }
    ),
):
    if role not in ("admin", "user", "guest"):
        raise WrongUserDataHTTPException
    await EventsService(db).edit_event(event_id, event_data, exclude_unset=True)
    return status.HTTP_200_OK


@router.delete(
    "/{event_id}",
    summary="Удаление выбранного события",
    description="<h1>Удалем выбранное событие: нужно отправить id события.</h1>",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_event(
    db: DBDep,
    role: UserRoleDep,
    event_id: int = Path(..., le=2147483647),
):
    if role not in ("admin", "user", "guest"):
        raise WrongUserDataHTTPException
    await EventsService(db).delete_event(event_id)
    return status.HTTP_204_NO_CONTENT
