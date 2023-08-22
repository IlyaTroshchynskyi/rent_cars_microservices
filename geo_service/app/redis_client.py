from functools import lru_cache
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends

from app.config import get_settings


@lru_cache
def get_redis_client():
    settings = get_settings()
    return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


db_dependency = Annotated[redis.Redis, Depends(get_redis_client)]
