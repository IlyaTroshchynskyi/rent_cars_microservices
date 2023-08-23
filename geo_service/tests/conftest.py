import uuid
from asyncio import AbstractEventLoop, get_event_loop_policy
from functools import lru_cache

from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI
from httpx import AsyncClient
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture
import pytest
from fakeredis import aioredis
from app.redis_client import get_redis_client
from app.main import create_app
from app.car_stations.schemas import CarStationIn


@pytest.fixture(scope='session')
def event_loop() -> AbstractEventLoop:
    """Create an instance of the default event loop for each test case."""
    loop = get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@lru_cache
def get_redis_client_overrides() -> FakeRedis:
    return aioredis.FakeRedis()


@pytest.fixture(scope='session')
async def redis_client() -> FakeRedis:
    yield get_redis_client_overrides()


async def clear_database(redis_client: FakeRedis):
    await redis_client.flushdb(asynchronous=True)


@pytest.fixture(scope='session')
async def app() -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_redis_client] = get_redis_client_overrides
    yield app


@pytest.fixture()
async def client(app: FastAPI, redis_client: FakeRedis) -> AsyncClient:
    """Async server client"""
    async with AsyncClient(app=app, base_url='http://test') as _client:
        try:
            yield _client
        except Exception:
            pass
        finally:
            await clear_database(redis_client)


@register_fixture(name='car_station_factory')
class CarStationCreateFactory(ModelFactory[CarStationIn]):
    __model__ = CarStationIn

    @classmethod
    def working_hours(cls) -> str:
        return '10:00-20:00'


@pytest.fixture(scope='function')
async def car_stations(
        redis_client: FakeRedis,
        car_station_factory: CarStationCreateFactory,
) -> list[tuple[str, CarStationIn]]:

    car_station = car_station_factory.build()
    _id = str(uuid.uuid4())
    await redis_client.set(_id, car_station.model_dump_json())
    yield [(_id, car_station)]
