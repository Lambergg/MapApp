from fastapi import WebSocket
from typing import List
import logging

logger = logging.getLogger("websocket")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Новое соединение. Всего: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        try:
            self.active_connections.remove(websocket)
            logger.info(
                f"Соединение закрыто. Оставшиеся: {len(self.active_connections)}"
            )
        except ValueError:
            pass

    async def send_personal_message(
        self, message: str, websocket: WebSocket
    ) -> None:
        """Отправка личного сообщения одному клиенту."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения клиенту: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str) -> None:
        """Рассылка всем активным клиентам."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение клиенту: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()
