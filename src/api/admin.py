from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, status, Depends
from fastapi_cache.decorator import cache

from src.api.dependencies import PaginationParams, get_admin_service, get_current_user_role
from src.exceptions import ObjectNotFoundException, UserNotFoundHTTPException
from src.schemas.users import UserPutDTO
from src.services.admin import AdminService
from src.utils.redis_utils import delete_refresh_token


router = APIRouter(prefix="/admin", tags=["Администрирование"])


@router.get(
    "/users",
    summary="Получение всех пользователей",
    description="<h1>Получение списка всех пользователей. Требуются права администратора</h1>",
)
@cache(expire=10)
async def get_users(
    service: Annotated[AdminService, Depends(get_admin_service)],
    pagination: Annotated[PaginationParams, Depends()],
    role: Annotated[str, Depends(get_current_user_role)],
    email: str | None = Query(None),
    name: str | None = Query(None),
    sname: str | None = Query(None),
):
    """
    :param service: Для работы с БД через зависимость
    :param pagination: Пагинация: page, per_page
    :param role: Роль текущего пользователя (из JWT)
    :param email: Фильтр по email
    :param name: Фильтр по имени
    :param sname: Фильтр по фамилии
    :return: List[UserDTO] — список пользователей.
    """

    return await service.get_filtered_by_time(
        pagination,
        email,
        name,
        sname,
        role
    )


@router.get(
    "/users/{user_id}",
    summary="Получение конкретного пользователя",
    description="<h1>Тут мы получаем конкретного пользователя, нужно указать id. Требуются права администратора</h1>",
)
@cache(expire=10)
async def get_user(
    service: Annotated[AdminService, Depends(get_admin_service)],
    role: Annotated[str, Depends(get_current_user_role)],
    user_id: int = Path(..., ge=1, le=2147483647, description="ID пользователя"),
):
    """
    :param service: Для работы с БД через зависимость
    :param role: Роль текущего пользователя (из JWT)
    :param user_id: query-параметр ID пользователя (до 2147483647)
    :return: Возврат UserDTO — данные пользователя. По его id.
    """
    try:
        return await service.get_user(user_id, role)
    except ObjectNotFoundException:
        raise UserNotFoundHTTPException


@router.put(
    "/change_role/{user_id}",
    summary="Обновление роли и статуса пользователя",
    description="<h1>Обновляем роль и статус аккаунта пользователю. Нужно обязательно передать ID, новую роль и статус аккаунта. Требуются права администратора</h1>",
    status_code=status.HTTP_200_OK,
)
async def edit_user_role(
    service: Annotated[AdminService, Depends(get_admin_service)],
    role: Annotated[str, Depends(get_current_user_role)],
    user_id: int = Path(..., ge=1, le=2147483647, description="ID пользователя"),
    user_data: UserPutDTO = Body(
        openapi_examples={
            "1": {
                "summary": "Пример роли и статуса аккаунта пользователя",
                "value": {
                    "role": "user",
                    "is_active": True,
                },
            },
        }
    ),
):
    """
    :param service: Для работы с БД через зависимость
    :param role: Роль текущего пользователя (из JWT)
    :param user_id: query-параметр ID пользователя (до 2147483647)
    :param user_data: Схема UserPutDTO
    :return: 200 OK при успехе.
    """
    await service.edit_user_role(
        user_id, user_data, role, exclude_unset=False
    )
    return status.HTTP_200_OK


@router.delete(
    "/delete_user/{user_id}",
    summary="Удаление выбранного пользователя",
    description="<h1>Удалем выбранного пользователя: нужно отправить id пользователя. Требуются права администратора</h1>",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    service: Annotated[AdminService, Depends(get_admin_service)],
    role: Annotated[str, Depends(get_current_user_role)],
    user_id: int = Path(..., ge=1, le=2147483647, description="ID пользователя"),
):
    """
    :param service: Для работы с БД через зависимость
    :param role: Роль текущего пользователя (из JWT)
    :param user_id: query-параметр ID пользователя (до 2147483647)
    :return: 204 No Content
    """
    await service.delete_user(user_id, role)
    return status.HTTP_204_NO_CONTENT


@router.post(
    "/delete_account/{user_id}",
    summary="Мягкое удаление аккаунта",
    description="<h1>Пользователь деактивируется (Банится), происходит logout</h1>",
    status_code=status.HTTP_200_OK,
)
async def delete_account(
    service: Annotated[AdminService, Depends(get_admin_service)],
    role: Annotated[str, Depends(get_current_user_role)],
    user_id: int = Path(..., ge=1, le=2147483647, description="ID пользователя"),
):
    """
    :param service: Для работы с БД через зависимость
    :param role: Роль текущего пользователя (из JWT)
    :param user_id: query-параметр ID пользователя (до 2147483647)
    :return: message: "Аккаунт успешно деактивирован (Забанен)", status: 200
    """
    await service.soft_delete_user(user_id, role)
    await delete_refresh_token(user_id)
    return {
        "message": "Аккаунт успешно деактивирован (Забанен)",
        "status": status.HTTP_200_OK,
    }
