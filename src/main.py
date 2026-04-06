# ruff: noqa E402
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
import logging
from pathlib import Path
import sys
import uvicorn


sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)

from src.init import redis_manager, redis_manager_auth
from src.health.health import router as heals_router
from src.api.auth import router as auth_router
from src.api.admin import router as admin_router
from src.api.images import router as images_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте приложения
    logging.info("Приложение стартовало")
    await redis_manager.connect()
    await redis_manager_auth.connect()
    await redis_manager.ping()
    FastAPICache.init(RedisBackend(redis_manager._redis), prefix="fastapi-cache")
    logging.info("FastApiCache инициирован")
    yield
    # При выключении/перезагрузке приложения
    await redis_manager.close()
    await redis_manager_auth.close()
    logging.info("Подключение к Redis закрыто")
    logging.info("Приложение остановлено")


app = FastAPI(docs_url=None, lifespan=lifespan)

app.include_router(heals_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(images_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Берём первое сообщение
    error_msg = exc.errors()[0]["msg"]

    # Локализуем
    if error_msg == "Field required":
        localized_msg = "Обязательное поле"
    elif "value is not a valid email address" in error_msg:
        localized_msg = "Некорректный email"
    elif "JSON decode error" in error_msg:
        localized_msg = "Неполные данные"
    else:
        localized_msg = error_msg

    raise HTTPException(status_code=422, detail=localized_msg)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
