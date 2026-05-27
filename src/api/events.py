from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status
from fastapi_cache.decorator import cache

from src.api.dependencies import (PaginationParams, get_current_user_id,
                                  get_current_user_role, get_event_service)
from src.common.constants import MAX_ID_VALUE, MIN_ID_VALUE
from src.schemas.events import EventsAddDTO, EventsUpdateDTO
from src.services.events import EventsService

router = APIRouter(prefix="/events", tags=["События"])


@router.get(
    "/all",
    summary="Получить список всех событиий",
    description="<h1>Возвращает список всех событий</h1>",
)
@cache(expire=10)
async def get_events(
    service: Annotated[EventsService, Depends(get_event_service)],
    role: Annotated[str, Depends(get_current_user_role)],
):
    """
    Получает список всех событий.

    :param service: Зависимость для работы с базой данных.
    :param role: Роль текущего пользователя (admin/user/guest).
    :type role: Str
    :return: Список событий.
    :rtype: List[EventDTO]
    :raises WrongUserDataHTTPException: Если роль не в списке допустимых.
    """

    return await service.get_events(role)


@router.get(
    "/one/{event_id}",
    summary="Получить событие",
    description="<h1>Возвращает событие по его ID</h1>",
)
@cache(expire=10)
async def get_one_event(
    service: Annotated[EventsService, Depends(get_event_service)],
    role: Annotated[str, Depends(get_current_user_role)],
    event_id: int = Path(
        ...,
        ge=MIN_ID_VALUE,
        le=MAX_ID_VALUE,
        description="path-параметр ID (до 2147483647)"
    ),
):
    """
    Возвращает одно событие по ID.

    :param service: Сессия базы данных.
    :param role: Роль пользователя.
    :type role: Str
    :param event_id: Уникальный идентификатор события. Должен быть > 0.
    :type event_id: int
    :return: Данные события.
    :rtype: EventDTO
    :raises HTTPException 404: Если событие не найдено.
    """

    return await service.get_one_event(event_id, role)


@router.get(
    "/me",
    summary="Получить все события пользователя",
    description="<h1>Получаем все события пользователя</h1>",
)
@cache(expire=10)
async def get_my_events(
    user_id: Annotated[int, Depends(get_current_user_id)],
    service: Annotated[EventsService, Depends(get_event_service)],
    role: Annotated[str, Depends(get_current_user_role)],
):
    """
    Возвращает все события, созданные или в которых участвует пользователь.

    :param user_id: ID текущего пользователя (из JWT).
    :type user_id: Int
    :param service: Сессия базы данных.
    :param role: Роль пользователя.
    :type role: Str
    :return: Список событий пользователя.
    :rtype: List[EventDTO]
    """

    return await service.get_my_events(user_id, role)


@router.get(
    "/search",
    summary="Поиск по событиям",
    description="<h1>Поиск событий по фильтрам.</h1>",
)
@cache(expire=10)
async def get_search_events(
    service: Annotated[EventsService, Depends(get_event_service)],
    pagination: Annotated[PaginationParams, Depends()],
    role: Annotated[str, Depends(get_current_user_role)],
    title: str | None = Query(None, description="Название события"),
    category: str | None = Query(None, description="Категория события"),
    address: str | None = Query(None, description="Адрес события"),
    date: str | None = Query(None, description="Дата/время события"),
    max_users: int | None = Query(
        None, description="Максимальное количество участников события"
    ),
):
    """
    Поиск событий по заданным фильтрам с пагинацией.

    :param service: Сессия базы данных.
    :param pagination: Параметры пагинации (page, per_page).
    :type pagination: PaginationParams
    :param role: Роль пользователя.
    :type role: str
    :param title: Фильтр по названию.
    :type title: str | None
    :param category: Фильтр по категории.
    :type category: str | None
    :param address: Фильтр по адресу.
    :type address: str | None
    :param date: Фильтр по дате (ISO формат).
    :type date: str | None
    :param max_users: Фильтр по максимальному числу участников.
    :type max_users: int | None
    :return: Отфильтрованный список событий.
    :rtype: PaginatedResponse[EventDTO]
    """

    return await service.get_filtered_by_time(
        pagination,
        title,
        category,
        address,
        date,
        max_users,
        role
    )


@router.post(
    "/create",
    summary="Добавить событие",
    description="<h1>Добавляет событие</h1>",
    status_code=status.HTTP_201_CREATED,
)
async def create_events(
    service: Annotated[EventsService, Depends(get_event_service)],
    role: Annotated[str, Depends(get_current_user_role)],
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
    """
    Создаёт новое событие.

    :param service: Сессия базы данных.
    :param role: Роль пользователя.
    :type role: Str
    :param data: Данные для создания события.
    :type data: EventsAddDTO
    :return: Информация о созданном событии.
    :rtype: Dict
    :status 201: Событие успешно создано.
    """

    events = await service.create_events(data, role)
    return {"Status": status.HTTP_201_CREATED, "data": events}


@router.put(
    "/edit/{event_id}",
    summary="Обновление события",
    description="<h1>Обновляем событие. Нужно передать ID и новые данные.</h1>",
    status_code=status.HTTP_200_OK,
)
async def edit_event(
    role: Annotated[str, Depends(get_current_user_role)],
    service: Annotated[EventsService, Depends(get_event_service)],
    event_id: int = Path(
        ...,
        ge=MIN_ID_VALUE,
        le=MAX_ID_VALUE,
        description="path-параметр ID (до 2147483647)"
    ),
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
    """
    Обновляет существующее событие по ID.

    :param role: Роль пользователя.
    :type role: Str
    :param service: Сессия базы данных.
    :param event_id: ID события для обновления.
    :type event_id: Int
    :param event_data: Новые данные события.
    :type event_data: EventsUpdateDTO
    :return: Статус 200 при успехе.
    :rtype: Int
    :status 200: Успешно обновлено.
    :raises HTTPException 404: Если событие не найдено.
    """

    await service.edit_event(event_id, event_data, role, exclude_unset=True)
    return


@router.delete(
    "/delete/{event_id}",
    summary="Удаление выбранного события",
    description="<h1>Удалем выбранное событие: нужно отправить id события.</h1>",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_event(
    service: Annotated[EventsService, Depends(get_event_service)],
    role: Annotated[str, Depends(get_current_user_role)],
    event_id: int = Path(
        ...,
        ge=MIN_ID_VALUE,
        le=MAX_ID_VALUE,
        description="path-параметр ID пользователя (до 2147483647)"
    ),
):
    """
    Удаляет событие по ID.

    :param service: Сессия базы данных.
    :param role: Роль пользователя.
    :type role: Str
    :param event_id: ID события для удаления.
    :type event_id: Int
    :return: Пустой ответ при успехе.
    :rtype: None
    :status 204: Событие успешно удалено.
    :raises HTTPException 404: Если событие не найдено.
    """

    await service.delete_event(event_id, role)
    return
