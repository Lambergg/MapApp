from fastapi import APIRouter, Response, Request, Body, status, Depends

from src.api.dependencies import UserIdDep, DBDep
from src.exceptions import UserDeleteTokenHTTPException
from src.schemas.users import UserRequestAddDTO, UserLoginDTO
from src.services.auth import AuthService
from src.utils.ratelimitter import rate_limit_auth_refresh, rate_limit_auth_get_me
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
    return await AuthService(db).login_user(data, response)


@router.get(
    "/me",
    summary="Получение информации о пользователе",
    description="<h1>Для получения информации о пользователе он должен быть аутентифицирован</h1>",
)
async def get_me(user_id: UserIdDep, db: DBDep, _: None = Depends(rate_limit_auth_get_me)):
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
    access_token = request.cookies.get("access_token") or None
    if not access_token:
        raise UserDeleteTokenHTTPException
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    await delete_refresh_token(user_id)
    return status.HTTP_200_OK


@router.post(
    "/refresh",
    summary="Обноввление пары access/refresh токенов",
    description="Обновляет аксесс ключ на основе рефреша. При этом обновляется кука с аксесс токеном.",
)
async def refresh(
    request: Request, response: Response, db: DBDep, _: None = Depends(rate_limit_auth_refresh)
):
    return await AuthService(db).refresh_tokens(request, response)
