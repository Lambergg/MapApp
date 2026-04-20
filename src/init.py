from src.connectors.redis_connector import RedisManager
from src.config import settings

redis_manager = RedisManager(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0
)
redis_manager_auth = RedisManager(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1
)
