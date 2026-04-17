from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from src.connectors.ws_connector import manager

logger = logging.getLogger("chat")

router = APIRouter(prefix="/chat", tags=["Чат пользователей"])

@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    logger.info(f"Подключение чата: {username}")
    await manager.connect(websocket)
    await manager.broadcast(f"{username} зашёл в чат")
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Сообщение от {username}: {data}")
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.warning(f"{username} вышел из чата")
        await manager.broadcast(f"{username} вышел из чата")