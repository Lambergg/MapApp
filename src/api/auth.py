from fastapi import APIRouter, Response, Request, Body, status, Depends, Path

from src.api.dependencies import UserIdDep, DBDep, UserRoleDep
from src.exceptions import (
    UserDeleteTokenHTTPException,
    WrongUserDataHTTPException,
)
from src.schemas.users import UserRequestAddDTO, UserLoginDTO, UserPatchDTO
from src.services.auth import AuthService
from src.tasks.tasks import test_task
from src.utils.ratelimitter import (
    rate_limit_auth_refresh,
    rate_limit_auth_get_me,
)
from src.utils.redis_utils import delete_refresh_token

router = APIRouter(prefix="/auth", tags=["Авторизация и аутентификация"])


@router.post(
    "/register",
    summary="Регистрация нового пользователя",
    description="<h1>Для регистрации нового пользователя нужно передать имя, фамилию и возраст + email и пароль</h1>",
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    db: DBDep,
    data: UserRequestAddDTO = Body(
        openapi_examples={
            "1": {
                "summary": "Новый пользователь",
                "value": {
                    "name": "Игорь",
                    "sname": "Котопес",
                    "age": 34,
                    "email": "koto-pes@mail.ru",
                    "password": "abcd1234",
                },
            }
        }
    ),
):
    """
    Регистрирует нового пользователя.

    :param db: Сессия базы данных (DI).
    :param data: Данные пользователя для регистрации.
    :return: HTTP 201 Created.
    """
    await AuthService(db).register_user(data)
    return status.HTTP_201_CREATED


@router.post(
    "/login",
    summary="Авторизация пользователя",
    description="<h1>Для авторизации пользователя нужно передать email и пароль</h1>",
)
async def login_user(
    response: Response,
    db: DBDep,
    data: UserLoginDTO = Body(
        openapi_examples={
            "1": {
                "summary": "Пользователь",
                "value": {
                    "email": "koto-pes@mail.ru",
                    "password": "abcd1234",
                },
            }
        }
    ),
):
    """
    Авторизует пользователя по email и паролю.

    :param response: HTTP-ответ (для установки cookies).
    :param db: Сессия БД.
    :param data: Логин и пароль.
    :return: Словарь с сообщением об успехе.
    """
    return await AuthService(db).login_user(data, response)


@router.get(
    "/me",
    summary="Получение информации о пользователе",
    description="<h1>Для получения информации о пользователе он должен быть аутентифицирован</h1>",
)
async def get_me(
    user_id: UserIdDep, db: DBDep, _: None = Depends(rate_limit_auth_get_me)
):
    """
    Возвращает данные текущего пользователя по ID из токена.

    :param user_id: ID пользователя из JWT (DI).
    :param db: Сессия БД.
    :param _: Ограничение по частоте запросов.
    :return: Объект UserDTO.
    """
    test_task.delay()  # type: ignore

    return await AuthService(db).get_me(user_id)


@router.post(
    "/logout",
    summary="Выход пользователя",
    description="<h1>Выход пользователя и удаление токена из cookie и Redis</h1>",
    status_code=status.HTTP_200_OK,
)
async def logout_user(
    user_id: UserIdDep,
    response: Response,
    request: Request,
):
    """
    Выполняет выход: удаляет токены из cookies и Redis.

    :param user_id: ID пользователя (DI).
    :param response: Для удаления cookies.
    :param request: Для получения access-токена из cookie.
    :return: HTTP 200 OK.
    """
    access_token = request.cookies.get("access_token") or None
    if not access_token:
        raise UserDeleteTokenHTTPException
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    await delete_refresh_token(user_id)
    return status.HTTP_200_OK


@router.put(
    "/edit_profile/{user_id}",
    summary="Обновление профиля пользователя",
    description="<h1>Обновляем профиль пользователя. Нужно передать ID и новые данные.</h1>",
    status_code=status.HTTP_200_OK,
)
async def edit_user_profile(
    db: DBDep,
    role: UserRoleDep,
    user_id: int = Path(..., le=2147483647),
    user_data: UserPatchDTO = Body(
        openapi_examples={
            "1": {
                "summary": "Пример данных",
                "value": {
                    "name": "Игорь",
                    "sname": "Котопес",
                    "age": 34,
                    "email": "koto-pes@mail.ru",
                    "password": "abcd1234",
                    "events_ids": [],
                },
            },
        }
    ),
):
    """
    Обновляет профиль пользователя. Только для владельца или админа.

    :param db: Сессия БД.
    :param role: Роль текущего пользователя.
    :param user_id: ID профиля для редактирования.
    :param user_data: Новые данные (частичные).
    :return: HTTP 200 OK.
    """
    if role not in ("admin", "user", "guest"):
        raise WrongUserDataHTTPException
    await AuthService(db).edit_user_profile(
        user_id, user_data, exclude_unset=True
    )
    return status.HTTP_200_OK


@router.post(
    "/refresh",
    summary="Обноввление пары access/refresh токенов",
    description="<h1>Обновляет аксесс ключ на основе рефреша. При этом обновляется кука с аксесс токеном.</h1>",
)
async def refresh(
    request: Request,
    response: Response,
    db: DBDep,
    _: None = Depends(rate_limit_auth_refresh),
):
    """
    Обновляет пару токенов, используя refresh-токен.

    :param request: Для получения refresh-токена из cookie.
    :param response: Для установки нового access-токена.
    :param db: Сессия БД.
    :param _: Ограничение по частоте.
    :return: Сообщение об успехе.
    """
    return await AuthService(db).refresh_tokens(request, response)
