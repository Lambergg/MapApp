import random
from time import time

from fastapi import HTTPException, Request, status

from src.init import redis_manager


class RateLimiter:
    """
    Класс для реализации rate limiting (ограничения частоты запросов) с использованием Redis.
    Использует алгоритм "sliding window" через Lua-скрипт в Redis.
    Гарантирует, что клиент не может выполнить более `max_requests` за `window_seconds`.
    """

    def __init__(self):
        self._lua_sha = None

    async def _load_script(self):
        """
        Асинхронно загружает Lua-скрипт в Redis и кэширует его SHA1-хэш.
        Скрипт выполняет:
        1. Удаление устаревших записей (за пределами окна)
        2. Подсчёт текущих запросов
        3. Добавление нового запроса, если лимит не превышен
        4. Установка TTL для ключа

        :return: None
        """
        if self._lua_sha is None:
            script = """
            redis.call("ZREMRANGEBYSCORE", KEYS[1], 0, ARGV[2])
            local count = redis.call("ZCARD", KEYS[1])
            if count >= tonumber(ARGV[3]) then
                return 1
            end
            redis.call("ZADD", KEYS[1], ARGV[1], ARGV[5])
            redis.call("EXPIRE", KEYS[1], ARGV[4])
            return 0
            """
            self._lua_sha = await redis_manager._redis.script_load(script)  # type: ignore

    async def is_limited(
        self,
        ip_address: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """
        Проверяет, превысил ли клиент лимит запросов к эндпоинту.

        :param ip_address: IP-адрес клиента.
        :type ip_address: Str
        :param endpoint: URL-путь эндпоинта (например, '/auth/me').
        :type endpoint: Str
        :param max_requests: Максимальное количество разрешённых запросов.
        :type max_requests: Int
        :param window_seconds: Временное окно в секундах.
        :type window_seconds: Int
        :return: True, если лимит превышен, иначе False.
        :rtype: Bool
        """
        await self._load_script()

        key = f"rate_limiter:{endpoint}:{ip_address}"

        current_ms = int(time() * 1000)
        window_start_ms = current_ms - window_seconds * 1000
        member_id = f"{current_ms}-{random.randint(0, 100_000)}"

        result = await redis_manager._redis.evalsha(
            self._lua_sha,  # type: ignore
            1,  # type: ignore
            key,  # type: ignore
            current_ms,  # type: ignore
            window_start_ms,  # type: ignore
            max_requests,  # type: ignore
            window_seconds,  # type: ignore
            member_id,  # type: ignore
        )

        return result == 1


_rate_limiter = RateLimiter()


def rate_limiter_factory(
    endpoint: str,
    max_requests: int,
    window_seconds: int,
):
    """
    Фабрика зависимостей для создания rate limit-ограничений под конкретный эндпоинт.

    :param endpoint: Путь эндпоинта (например, '/auth/me').
    :type endpoint: str
    :param max_requests: Максимальное количество запросов.
    :type max_requests: int
    :param window_seconds: Длительность окна в секундах.
    :type window_seconds: int
    :return: Зависимость FastAPI, которую можно внедрить в роут.
    :rtype: Callable[[Request], Awaitable[None]]
    """

    async def dependency(
        request: Request,
    ):
        ip_address = request.client.host  # type: ignore

        limited = await _rate_limiter.is_limited(
            ip_address,
            endpoint,
            max_requests,
            window_seconds,
        )

        if limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Превышено количество запросов. Повторите позже",
            )

    return dependency


rate_limit_auth_refresh = rate_limiter_factory("/auth/refresh", 1, 3)
rate_limit_auth_get_me = rate_limiter_factory("/auth/me", 5, 10)
rate_limit_health_get = rate_limiter_factory("/health/get_redis", 1, 3)
