import time
from functools import lru_cache

import redis

from src.core.config import settings


@lru_cache()
def get_redis_pool():
    return redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=settings.REDIS_DECODE_RESPONSES,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        retry_on_timeout=True,
    )


def get_redis_client() -> redis.Redis:
    pool = get_redis_pool()
    for attempt in range(settings.REDIS_RETRY_ATTEMPTS):
        try:
            client = redis.Redis(connection_pool=pool)
            client.ping()
            return client
        except redis.ConnectionError as e:
            if attempt == settings.REDIS_RETRY_ATTEMPTS - 1:
                raise Exception(
                    f"Failed to connect to Redis after {settings.REDIS_RETRY_ATTEMPTS} attempts: {str(e)}"
                )
            time.sleep(settings.REDIS_RETRY_DELAY)
    raise Exception("Failed to connect to Redis")
