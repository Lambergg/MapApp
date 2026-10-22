from src.config import settings
from src.connectors.redis_connector import RedisManager

redis_manager = RedisManager(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True
)
redis_manager_auth = RedisManager(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1, decode_responses=True
)
redis_manager_cache = RedisManager(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2
)
