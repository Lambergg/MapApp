import logging

import redis.asyncio as redis

logger = logging.getLogger("redis_connector")


class RedisManager:
    """
    Менеджер для асинхронного взаимодействия с Redis.

    Предоставляет методы подключения, чтения, записи и удаления данных.
    Используется для хранения сессий, токенов и кэширования.

    :param host: Адрес сервера Redis.
    :type host: str
    :param port: Порт Redis.
    :type port: int
    :param db: Номер базы данных (по умолчанию 0).
    :type db: int
    """

    _redis = redis.Redis

    def __init__(self, host: str, port: int, db: int = 0) -> None:
        self.host = host
        self.port = port
        self.db = db

    async def connect(self) -> None:
        """
        Устанавливает соединение с Redis.
        """
        logger.info("Подключаюсь к Redis...")
        self._redis = await redis.Redis(
            host=self.host, port=self.port, db=self.db, decode_responses=True
        )
        logger.info("Redis подключен")

    async def ping(self) -> bool:
        """
        Проверяет активность соединения с Redis.

        :return: True, если пинг успешен, иначе False.
        :rtype: bool
        """
        if self._redis is None:
            logger.error("Нет подключения")
            return False
        try:
            await self._redis.ping()
            logger.info("Пинг прошел успешно!")
            return True
        except Exception as e:
            logger.error(f"Ошибка при пинге {e}")
            return False

    async def set(self, key: str, value: str, expire: int | None = None) -> None:
        """
        Сохраняет значение в Redis с опциональным временем жизни.

        :param key: Ключ для хранения.
        :type key: str
        :param value: Значение.
        :type value: str
        :param expire: Время жизни ключа в секундах. Если None — бессрочно.
        :type expire: int | None
        """
        if expire:
            await self._redis.set(key, value, ex=expire)
        logger.info(f"{key} и {value} сохранено в редис")

    async def get(self, key: str) -> str | None:
        """
        Получает значение по ключу из Redis.

        :param key: Ключ.
        :type key: str
        :return: Значение или None, если ключ не найден.
        :rtype: str | None
        """
        return await self._redis.get(key)

    async def delete(self, key: str) -> None:
        """
        Удаляет ключ из Redis.

        :param key: Ключ для удаления.
        :type key: str
        """
        await self._redis.delete(key)

    async def close(self) -> None:
        """
        Закрывает соединение с Redis.
        """
        await self._redis.close()
