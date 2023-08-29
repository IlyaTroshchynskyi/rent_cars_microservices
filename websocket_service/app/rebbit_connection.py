import asyncio
from functools import lru_cache

from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool

from app.config import get_settings


async def _get_connection() -> AbstractRobustConnection:
    return await connect_robust(get_settings().RABBITMQ_URL)


@lru_cache
def get_connection_pool() -> Pool:
    loop = asyncio.new_event_loop()
    connection_pool = Pool(_get_connection, max_size=5, loop=loop)
    return connection_pool
