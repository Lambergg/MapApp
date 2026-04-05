from typing import Annotated
from fastapi import Depends, Query, HTTPException, Request
from pydantic import BaseModel

from src.database import async_session_maker
from src.init import redis_manager_auth
from src.services.auth import AuthService
from src.utils.db_manager import DBManager


class PaginationParams(BaseModel):
    page: Annotated[int, Query(1, ge=1, description="Текущая страница")]
    per_page: Annotated[int | None, Query(None, ge=1, le=30, description="Элементов на странице")]


PaginationDep = Annotated[PaginationParams, Depends()]


def get_token(request: Request) -> str:
    token = request.cookies.get("access_token") or None
    if not token:
        raise HTTPException(status_code=401, detail="Вы не предоставили токен доступа")
    return token


def get_current_user_id(token: str = Depends(get_token)) -> int:
    data = AuthService().decode_access_token(token)
    return data["user_id"]


UserIdDep = Annotated[int, Depends(get_current_user_id)]


async def get_current_user_role(user_id: int = Depends(get_current_user_id)) -> str:
    user_role = await redis_manager_auth.get(f"user_role:{user_id}")
    if not user_role:
        raise HTTPException(status_code=401, detail="Не удалось получить данные пользователя")
    return user_role


UserRoleDep = Annotated[str, Depends(get_current_user_role)]


def get_db_manager():
    return DBManager(session_factory=async_session_maker)


async def get_db():
    async with get_db_manager() as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]
