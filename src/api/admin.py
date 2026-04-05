from fastapi import APIRouter, Path, Body, status, Query
from fastapi_cache.decorator import cache

from src.api.dependencies import DBDep, UserRoleDep, PaginationDep, UserIdDep
from src.exceptions import (
    AdminOnlyAccessHTTPException,
    ObjectNotFoundException,
    UserNotFoundHTTPException, UserIndexWrongHTTPException,
)
from src.schemas.users import UserPutDTO
from src.services.admin import AdminService
from src.utils.redis_utils import delete_refresh_token

router = APIRouter(prefix="/admin", tags=["Администрирование"])


@router.get(
    "/users",
    summary="Получение всех пользователей",
    description="Получение списка всех пользователей. Требуются права администратора",
)
@cache(expire=10)
async def get_users(
    db: DBDep,
    pagination: PaginationDep,
    role: UserRoleDep,
    email: str | None = Query(None, description="Email пользователя"),

):
    if role != "admin":
        raise AdminOnlyAccessHTTPException

    return await AdminService(db).get_filtered_by_time(
        pagination,
        email,
    )


@router.get(
    "/users/{user_id}",
    summary="Получение конкретного пользователя",
    description="Тут мы получаем конкретного пользователя, нужно указать id. Требуются права администратора",
)
@cache(expire=10)
async def get_user(
    db: DBDep,
    role: UserRoleDep,
    user_id: int = Path(..., le=2147483647),
):
    try:
        if role != "admin":
            raise AdminOnlyAccessHTTPException
        return await AdminService(db).get_user(user_id)
    except ObjectNotFoundException:
        raise UserNotFoundHTTPException


@router.put(
    "/change_role/{user_id}",
    summary="Обновление роли и статуса пользователя",
    description="Обновляем роль и статус аккаунта пользователю. Нужно обязательно передать ID, новую роль и статус аккаунта. Требуются права администратора",
    status_code=status.HTTP_200_OK,
)
async def edit_user_role_status(
    db: DBDep,
    role: UserRoleDep,
    user_id: int = Path(..., le=2147483647),
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
    if role != "admin":
        raise AdminOnlyAccessHTTPException
    await AdminService(db).edit_user_role_status(user_id, user_data, exclude_unset=False)
    return status.HTTP_200_OK


@router.delete(
    "/delete_user/{user_id}",
    summary="Удаление выбранного пользователя",
    description="Удалем выбранного пользователя: нужно отправить id пользователя. Требуются права администратора",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    db: DBDep,
    role: UserRoleDep,
    user_id: int = Path(..., le=2147483647),
):
    if role != "admin":
        raise AdminOnlyAccessHTTPException
    await AdminService(db).delete_user(user_id)
    return status.HTTP_204_NO_CONTENT


@router.post(
    "/delete_account/{user_id}",
    summary="Мягкое удаление аккаунта",
    description="<h1>Пользователь деактивируется (Баниться), происходит logout</h1>",
    status_code=status.HTTP_200_OK,
)
async def delete_account(
    db: DBDep,
    user_id: int = Path(..., le=2147483647),
):
    if user_id <= 0:
        raise UserIndexWrongHTTPException
    try:
        await db.users.get_one(id=user_id)
    except ObjectNotFoundException:
        raise UserNotFoundHTTPException
    await AdminService(db).soft_delete_user(user_id)
    await delete_refresh_token(user_id)
    return {"message": "Аккаунт успешно деактивирован (Забанен)", "status": status.HTTP_200_OK}

