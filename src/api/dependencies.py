from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request
from pydantic import BaseModel

from src.database import async_session_maker
from src.init import redis_manager_auth
from src.services.admin import AdminService
from src.services.auth import AuthService
from src.utils.db_manager import DBManager


class PaginationParams(BaseModel):
    """
    Параметры пагинации для запросов с постраничным выводом.
    Используется как зависимость в эндпоинтах, где нужно разбить данные на страницы.
    """

    page: Annotated[int, Query(1, ge=1, description="Текущая страница")]
    """
    Номер текущей страницы.
    По умолчанию: 1.
    Ограничение: ≥ 1.
    """
    per_page: Annotated[
        int | None,
        Query(None, ge=1, le=30, description="Элементов на странице"),
    ]
    """
    Количество элементов на странице.
    По умолчанию: зависит от эндпоинта (часто 10).
    Ограничения: от 1 до 30.
    Если не указано — используется значение по умолчанию из сервиса.
    """


def get_token(request: Request) -> str:
    """
    Извлекает токен доступа из cookies.

    :param request: Объект HTTP-запроса.
    :return: Строка с access token.
    :raises HTTPException: Если токен не найден.
    """
    token = request.cookies.get("access_token") or None
    if not token:
        raise HTTPException(
            status_code=401, detail="Вы не предоставили токен доступа"
        )
    return token


def get_current_user_id(token: str = Depends(get_token)) -> int:
    """
    Декодирует JWT-токен и возвращает ID пользователя.

    :param token: Токен доступа (извлекается через `get_token`).
    :return: ID пользователя из payload токена.
    :raises HTTPException: Если токен недействителен или просрочен.
    """
    data = AuthService().decode_access_token(token)
    return data["user_id"]


async def get_current_user_role(
    user_id: int = Depends(get_current_user_id),
) -> str:
    """
    Получает роль пользователя из Redis по его ID.

    :param user_id: ID пользователя (получается из токена).
    :return: Роль пользователя (`admin`, `user`, `guest` и т.д.).
    :raises HTTPException: Если роль не найдена в Redis.
    """
    user_role = await redis_manager_auth.get(f"user_role:{user_id}")
    if not user_role:
        raise HTTPException(
            status_code=401, detail="Не удалось получить данные пользователя"
        )
    return user_role


def get_db_manager():
    """
    Создаёт и возвращает экземпляр DBManager с фабрикой сессий.
    :return: Экземпляр DBManager.
    """
    return DBManager(session_factory=async_session_maker)


async def get_db():
    """
    Асинхронная зависимость для получения активной сессии БД.
    Управляет жизненным циклом сессии: открывает и закрывает её через контекстный менеджер.
    :yield: Активный экземпляр DBManager.
    """
    async with get_db_manager() as db:
        yield db


async def get_admin_service(
    db: Annotated[get_db_manager, Depends(get_db)]
) -> AdminService:
    return AdminService(db)
