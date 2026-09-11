import json
import logging
from typing import Any, Optional, List, Dict, Union

import redis.asyncio as redis


class RedisManager:
    """
    Асинхронный менеджер для взаимодействия с Redis.

    Поддерживает хранение строк, чисел, словарей и списков с автоматической
    JSON-сериализацией. Управляет жизненным циклом соединения через async context manager.
    """

    def __init__(
            self,
            host: str,
            port: int,
            db: int = 0,
            decode_responses: bool = False,
            use_json_serialization: bool = True
    ):
        self.host = host
        self.port = port
        self.db = db
        self.decode_responses = decode_responses
        self.use_json = use_json_serialization
        self._redis: Optional[redis.Redis] = None

    async def __aenter__(self) -> "RedisManager":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        await self.close()
        return False  # Не подавляем исключения из блока 'with'

    async def connect(self):
        if self._redis is not None:
            logging.warning("Повторное подключение отклонено.")
            return

        try:
            logging.info(f"Подключение к Redis {self.host}:{self.port}/{self.db}")
            self._redis = await redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=self.decode_responses
            )
            await self._redis.ping()
            logging.info("Redis подключен")
        except Exception as e:
            logging.error(f"Сбой подключения к Redis: {e}")
            self._redis = None
            raise ConnectionError(f"Failed to connect to Redis: {e}") from e

    async def close(self):
        if self._redis is None:
            return

        try:
            await self._redis.aclose()
            logging.info("Соединение Redis закрыто")
        except Exception as e:
            logging.error(f"Ошибка закрытия Redis: {e}")
        finally:
            self._redis = None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Записывает данные любого поддерживаемого типа."""
        if self._redis is None:
            raise RuntimeError("Not connected to Redis")

        data_to_store = value

        if self.use_json and isinstance(value, (dict, list)):
            try:
                data_to_store = json.dumps(value)
            except (TypeError, OverflowError) as e:
                logging.error(f"Не удалось сериализовать объект для ключа '{key}': {e}")
                return False

        try:
            result = await self._redis.set(key, data_to_store, ex=expire)
            return bool(result)
        except redis.RedisError as e:
            logging.error(f"Ошибка SET для ключа '{key}': {e}")
            return False

    async def get(self, key: str) -> Optional[Union[str, bytes, dict, list]]:
        """Получает данные с попыткой десериализации JSON."""
        if self._redis is None:
            raise RuntimeError("Not connected to Redis")

        raw_value = await self._redis.get(key)

        if raw_value is None:
            return None

        if self.use_json and isinstance(raw_value, str):
            try:
                return json.loads(raw_value)
            except json.JSONDecodeError:
                # Это не JSON, возвращаем обычную строку
                pass

        return raw_value

    async def delete(self, key: str) -> int:
        """Удаляет ключ."""
        if self._redis is None:
            raise RuntimeError("Not connected to Redis")
        return await self._redis.delete(key)

    # --- Работа со списками (для очередей задач или логов) ---
    async def lpush(self, key: str, *values: Any) -> int:
        """Добавляет элементы в начало списка."""
        if self._redis is None:
            raise RuntimeError("Not connected to Redis")

        serialized_values = [json.dumps(v) if self.use_json and isinstance(v, (dict, list)) else v for v in values]
        return await self._redis.lpush(key, *serialized_values)

    async def rpush(self, key: str, *values: Any) -> int:
        """Добавляет элементы в конец списка."""
        if self._redis is None:
            raise RuntimeError("Not connected to Redis")

        serialized_values = [json.dumps(v) if self.use_json and isinstance(v, (dict, list)) else v for v in values]
        return await self._redis.rpush(key, *serialized_values)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Получает диапазон элементов списка."""
        if self._redis is None:
            raise RuntimeError("Not connected to Redis")

        items = await self._redis.lrange(key, start, end)
        if not items or not self.use_json:
            return items

        deserialized = []
        for item in items:
            try:
                deserialized.append(json.loads(item))
            except json.JSONDecodeError:
                deserialized.append(item)
        return deserialized

    async def hset(self, name: str, key: str, value: Any) -> bool:
        """Устанавливает поле в хеше."""
        if self._redis is None:
            raise RuntimeError("Not connected to Redis")

        val = json.dumps(value) if self.use_json and isinstance(value, (dict, list)) else value
        return await self._redis.hset(name, key, val)

    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Получает все поля хеша."""
        if self._redis is None:
            raise RuntimeError("Not connected to Redis")

        raw_data = await self._redis.hgetall(name)
        if not raw_data or not self.use_json:
            return raw_data

        parsed_data = {}
        for k, v in raw_data.items():
            try:
                parsed_data[k] = json.loads(v)
            except json.JSONDecodeError:
                parsed_data[k] = v
        return parsed_data

    async def ping(self) -> bool:
        if self._redis is None:
            return False
        try:
            return await self._redis.ping()
        except redis.RedisError:
            return False
