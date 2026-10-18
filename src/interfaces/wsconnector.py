from typing import Protocol

from fastapi import WebSocket


class IWSConnector(Protocol):
    async def connect(self, websocket: WebSocket) -> None: ...

    def disconnect(self, websocket: WebSocket) -> None: ...

    async def broadcast(self, message: str) -> None: ...
