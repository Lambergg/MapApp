from time import time
import random
from fastapi import HTTPException, status, Request

from src.init import redis_manager


class RateLimiter:
    def __init__(self):
        self._lua_sha = None

    async def _load_script(self):
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
            self._lua_sha = await redis_manager._redis.script_load(script)

    async def is_limited(
        self,
        ip_address: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        await self._load_script()

        key = f"rate_limiter:{endpoint}:{ip_address}"

        current_ms = int(time() * 1000)
        window_start_ms = current_ms - window_seconds * 1000
        member_id = f"{current_ms}-{random.randint(0, 100_000)}"

        result = await redis_manager._redis.evalsha(
            self._lua_sha,
            1,
            key,
            current_ms,
            window_start_ms,
            max_requests,
            window_seconds,
            member_id,
        )

        return result == 1


_rate_limiter = RateLimiter()


def rate_limiter_factory(
    endpoint: str,
    max_requests: int,
    window_seconds: int,
):
    async def dependency(
        request: Request,
    ):
        ip_address = request.client.host

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
rate_limit_auth_get_me = rate_limiter_factory("/auth/me", 1, 3)
