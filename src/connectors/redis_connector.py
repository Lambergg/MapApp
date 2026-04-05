import logging

import redis.asyncio as redis


class RedisManager:
    _redis = redis.Redis

    def __init__(self, host: str, port: int, db: int = 0):
        self.host = host
        self.port = port
        self.db = db

    async def connect(self):
        logging.info("Подключаюсь к Redis...")
        self._redis = await redis.Redis(
            host=self.host, port=self.port, db=self.db, decode_responses=True
        )
        logging.info("Redis подключен")

    async def ping(self):
        if self._redis is None:
            logging.error("Нет подключения")
            return False
        try:
            await self._redis.ping()
            logging.info("Пинг прошел успешно!")
            return True
        except Exception as e:
            logging.error(f"Ошибка при пинге {e}")
            return False

    async def set(self, key: str, value: str, expire: int | None = None):
        if expire:
            await self._redis.set(key, value, ex=expire)
        else:
            await self._redis.set(key, value)
        logging.info(f"{key} и {value} сохранено в редис")

    async def get(self, key: str):
        return await self._redis.get(key)

    async def delete(self, key: str):
        await self._redis.delete(key)

    async def close(self):
        await self._redis.close()
