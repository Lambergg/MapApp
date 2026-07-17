import logging
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket

from src.api.dependencies import get_chat_service
from src.services.chat import ChatService

logger = logging.getLogger("chat")

router = APIRouter(prefix="/chat", tags=["Чат пользователей"])


@router.websocket("/ws/{username}")
async def websocket_endpoint(
        websocket: WebSocket,
        service: Annotated[ChatService, Depends(get_chat_service)],
        username: str
) -> None:
    """
    Обработчик WebSocket-подключения для чата.

    :param service: Сервис предоставляющий логику чата.
    :param websocket: Объект соединения.
    :param username: Имя пользователя (из пути).
    :return: None
    """
    await service.connect_user(websocket, username)
    await service.broadcast_message(username, websocket)
