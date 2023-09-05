from asyncio import AbstractEventLoop, get_event_loop_policy
from datetime import datetime, timedelta
import os

from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture
import pytest

from app import create_app
from app.models import gather_documents, Order
from app.orders.schemas import OrderCreate, OrderDictSerialized, OrderOut, CarOut


def pytest_configure(config: pytest.Config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    os.environ['MONGODB_URI'] = 'mongodb://root:example@localhost:27017'
    os.environ['MONGODB_DB_NAME'] = 'OrdersDbTest'
    os.environ['CASE_SENSITIVE'] = '1'
    os.environ['CAR_SERVICE_BASE_URL'] = 'http://test-car-service-host/cars/'


@pytest.fixture(scope='session')
def event_loop() -> AbstractEventLoop:
    """Create an instance of the default event loop for each test case."""
    loop = get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def clear_database(_app: FastAPI) -> None:
    for model in gather_documents():
        await model.get_motor_collection().drop()
        await model.get_motor_collection().drop_indexes()


@pytest.fixture(scope='session')
async def app():
    app = create_app()
    async with LifespanManager(app):
        yield app


@pytest.fixture()
async def client(app) -> AsyncClient:
    """Async server client"""
    async with AsyncClient(app=app, base_url='http://test') as _client:
        try:
            yield _client
        except Exception:  # pylint: disable=broad-except
            pass
        finally:
            await clear_database(app)


@register_fixture(name='orders_factory')
class OrderReadFactory(ModelFactory[OrderOut]):
    __model__ = OrderOut
    __random_seed__ = 1

    @classmethod
    def rental_date_start(cls) -> datetime:
        dt = datetime.now() + timedelta(minutes=10)
        return dt.replace(second=0, microsecond=0)

    @classmethod
    def rental_date_end(cls) -> datetime:
        dt = datetime.now() + timedelta(days=3, hours=1)
        return dt.replace(second=0, microsecond=0)


class OrderCreateFactory(ModelFactory[OrderCreate]):
    __model__ = OrderCreate
    __random_seed__ = 1

    @classmethod
    def rental_date_start(cls) -> datetime:
        return datetime.now() + timedelta(minutes=10)

    @classmethod
    def rental_date_end(cls) -> datetime:
        return datetime.now() + timedelta(days=3, hours=1)


@pytest.fixture(scope='function')
async def orders(orders_factory) -> list[OrderDictSerialized]:
    order_1: OrderOut = orders_factory.build()
    db_order_1 = Order(**order_1.model_dump())
    await db_order_1.insert()
    yield [order_1.serializable_dict(by_alias=True)]


class CarReadFactory(ModelFactory[CarOut]):
    __model__ = CarOut
