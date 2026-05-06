from fastapi import APIRouter, status, Depends

from src.init import redis_manager, redis_manager_auth
from src.utils.ratelimitter import rate_limit_auth_get_me

router = APIRouter(prefix="/health", tags=["Health"])


@router.post(
    "/redis_set",
    status_code=status.HTTP_201_CREATED,
    summary="Установка значений",
    description="<h1>Проверка установки данных в Redis, устанавливает ключи A и B со значениями 1234 и 3421</h1>",
)
async def redis_set():
    """
    Устанавливает тестовые значения в два разных экземпляра Redis (db0 и db1).
    Используется для проверки работоспособности подключения к Redis.

    :return: HTTP статус 201 при успешной записи.
    :rtype: Int
    """
    key1 = "A"
    value1 = "1234"
    key2 = "B"
    value2 = "3421"

    await redis_manager.set(key1, value1)
    await redis_manager_auth.set(key2, value2)
    return status.HTTP_201_CREATED


@router.get("/get_redis", summary="Получение значений из редиса")
async def get_data_from_redis(_: None = Depends(rate_limit_auth_get_me)):
    """
    Получает тестовые значения из двух экземпляров Redis:
    - `A` из основной базы (db0)
    - `B` из базы аутентификации (db1)
    Используется для проверки чтения данных из Redis.

    :param _: Применяется зависимость лимита запросов (игнорируется).
    :type _: None
    :return: Словарь с полученными значениями.
    :rtype: Dict[str, str | None]
    """
    value_db0 = await redis_manager.get("A")
    value_db1 = await redis_manager_auth.get("B")
    return {"value_db0": value_db0, "value_db1": value_db1}
