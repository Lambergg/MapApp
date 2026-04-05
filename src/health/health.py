from fastapi import APIRouter, status

from src.init import redis_manager, redis_manager_auth

router = APIRouter(prefix="/health", tags=['Health'])


@router.post(
    "/redis_set",
    status_code=status.HTTP_201_CREATED,
    summary='Установка значений',
    description="Проверка установки данных в Redis, устанавливает ключи A и B со значениями 1234 и 3421",
)
async def redis_set():
    key1 = "A"
    value1 = "1234"
    key2 = "B"
    value2 = "3421"

    await redis_manager.set(key1, value1)
    await redis_manager_auth.set(key2, value2)
    return status.HTTP_201_CREATED


@router.get('/get_redis', summary="Получение значений из редиса")
async def get_data_from_redis():
    value_db0 = await redis_manager.get("A")
    value_db1 = await redis_manager_auth.get("B")
    return {"value_db0": value_db0, "value_db1": value_db1}
