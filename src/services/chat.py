import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("chat")

class ChatService:
    def __init__(self, connection_manager: Any):
        self.manager = connection_manager

    async def connect_user(self, websocket: WebSocket, username: str) -> None:
        """
        Подключает пользователя к чату и уведомляет других.

        :param websocket: Объект WebSocket-соединения.
        :param username: Имя пользователя.
        """
        logger.info(f"Подключение чата: {username}")
        await self.manager.connect(websocket)
        await self.manager.broadcast(f"{username} зашёл в чат")

    async def broadcast_message(self, username: str, websocket: WebSocket) -> None:
        """
        Получает и рассылает сообщения от пользователя.

        :param username: Имя пользователя.
        :param websocket: Объект WebSocket-соединения.
        """
        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"Сообщение от {username}: {data}")
                await self.manager.broadcast(f"{username}: {data}")
        except WebSocketDisconnect:
            await self.disconnect_user(websocket, username)

    async def disconnect_user(self, websocket: WebSocket, username: str) -> None:
        """
        Отключает пользователя от чата и уведомляет других.

        :param websocket: Объект WebSocket-соединения.
        :param username: Имя пользователя.
        """
        self.manager.disconnect(websocket)
        logger.warning(f"{username} вышел из чата")
        await self.manager.broadcast(f"{username} вышел из чат")
