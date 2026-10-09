# ruff: noqa E402
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

sys.path.append(str(Path(__file__).parent.parent))

from app import create_app
from src.config import settings


app = create_app()

app.mount("/static", StaticFiles(directory="src/static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
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
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    # Берём первое сообщение
    error_msg = exc.errors()[0]["msg"]

    # Локализуем
    if error_msg == "Field required":
        localized_msg = "Обязательное поле"
    elif "value is not a valid email address" in error_msg:
        localized_msg = "Некорректный email"
    elif "JSON decode error" in error_msg:
        localized_msg = "Неполные данные"
    elif (
        "Input should be a valid datetime or date, input is too short"
        in error_msg
    ):
        localized_msg = "Некорректная дата"
    elif "String should have at least 1 character" in error_msg:
        localized_msg = "Строка слишком короткая"
    elif "Input should be greater than or equal to 1" in error_msg:
        localized_msg = "Значение должно быть больше или равно 1"
    elif "Input should be greater than 0" in error_msg:
        localized_msg = "Значение должно быть больше 0"
    else:
        localized_msg = error_msg

    raise HTTPException(status_code=422, detail=localized_msg)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
