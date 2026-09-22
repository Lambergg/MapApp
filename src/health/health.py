from fastapi import APIRouter, Depends, status

from src.init import redis_manager, redis_manager_auth
from src.schemas.answers import HealthAnswerDTO
from src.utils.ratelimitter import rate_limiter_factory

router = APIRouter(prefix="/health", tags=["Health"])


@router.post(
    "/set",
    status_code=status.HTTP_201_CREATED,
    summary="Установка значений",
    description="<h1>Проверка установки данных, устанавливает ключи A и B</h1>",
)
async def redis_set(
        _: None = Depends(rate_limiter_factory("/health/set", 1, 5))
) -> None:
    """
    Устанавливает тестовые значения в два разных экземпляра (db0 и db1).
    Используется для проверки работоспособности подключения.

    :return: HTTP статус 201 при успешной записи.
    :rtype: Int
    """
    key1 = "A"
    value1 = "1234"
    key2 = "B"
    value2 = "3421"

    await redis_manager.set(key1, value1, 60)
    await redis_manager_auth.set(key2, value2 , 60)
    return


@router.get(
    "/get",
    summary="Получение значений",
    response_model=HealthAnswerDTO
)
async def get_data_from_redis(
        _: None = Depends(rate_limiter_factory("/health/get", 1, 5))
) -> HealthAnswerDTO:
    """
    Получает тестовые значения из двух экземпляров:
    - `A` из основной базы.
    - `B` из базы аутентификации.
    Используется для проверки чтения данных.

    :param _: Применяется зависимость лимита запросов (игнорируется).
    :type _: None
    :return: Словарь с полученными значениями.
    :rtype: Dict[str, str | None]
    """
    value_db0 = await redis_manager.get("A")
    value_db1 = await redis_manager_auth.get("B")
    res = {"value1": value_db0, "value2": value_db1}
    return HealthAnswerDTO(answer=res)
