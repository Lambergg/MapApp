# ruff: noqa E402
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from src.api.admin import router as admin_router
from src.api.auth import router as auth_router
from src.api.chat import router as chat
from src.api.events import router as events_router
from src.api.images import router as images_router
from src.health.health import router as heals_router
from src.init import redis_manager, redis_manager_auth

logging.basicConfig(
    level=logging.INFO, format="%(name)s %(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте приложения
    logger.info("Приложение стартовало")
    await redis_manager.connect()
    await redis_manager_auth.connect()
    await redis_manager.ping()
    FastAPICache.init(
        RedisBackend(redis_manager._redis), prefix="fastapi-cache"
    )
    logger.info("FastApiCache инициирован")
    yield
    # При выключении/перезагрузке приложения
    await redis_manager.close()
    await redis_manager_auth.close()
    logger.info("Подключение к Redis закрыто")
    logger.info("Приложение остановлено")


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, lifespan=lifespan, title="Приложение MapApp")
    app.include_router(heals_router)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(images_router)
    app.include_router(events_router)
    app.include_router(chat)
    return app
