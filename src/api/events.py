from fastapi import APIRouter, Body
from fastapi_cache.decorator import cache

from src.api.dependencies import DBDep, UserRoleDep, UserIdDep
from src.exceptions import WrongUserDataHTTPException
from src.schemas.events import EventsAddDTO
from src.services.events import EventsService

router = APIRouter(prefix="/events", tags=["События"])


@router.get(
    "",
    summary="Получить список всех событиий",
    description="<h1>Возвращает список всех событий</h1>",
)
@cache(expire=10)
async def get_facilities(
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
)
async def create_facilities(
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
    return {"Status": "Ok", "data": events}
