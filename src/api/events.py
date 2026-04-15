from fastapi import APIRouter, Body, status, Path
from fastapi_cache.decorator import cache

from src.api.dependencies import DBDep, UserRoleDep, UserIdDep
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
