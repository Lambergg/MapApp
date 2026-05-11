import logging
from typing import List

from fastapi import WebSocket

logger = logging.getLogger("websocket")


class ConnectionManager:
    """
    Менеджер WebSocket-соединений для управления активными клиентами.

    Предоставляет методы подключения, отключения и отправки сообщений
    как отдельным клиентам, так и рассылки всем подключённым.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """
        Принимает новое WebSocket-соединение и добавляет его в список активных.

        :param websocket: Объект WebSocket.
        :type websocket: WebSocket
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Новое соединение. Всего: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Удаляет соединение из списка активных.

        :param websocket: Объект WebSocket для отключения.
        :type websocket: WebSocket
        """
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
        """
        Отправляет личное сообщение конкретному клиенту.

        :param message: Текст сообщения.
        :type message: str
        :param websocket: Целевой WebSocket.
        :type websocket: WebSocket
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения клиенту: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str) -> None:
        """
        Рассылает сообщение всем активным клиентам.
        Автоматически удаляет соединения, при отправке в которые произошла ошибка.

        :param message: Текст сообщения для рассылки.
        :type message: str
        """
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
