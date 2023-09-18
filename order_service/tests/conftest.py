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
from app.orders.schemas import CarOut, OrderCreate, OrderDictSerialized, OrderOut
from app.users.schemas import UserOut


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
    os.environ['AUTH_SERVICE_BASE_URL'] = 'http://test-car-service-host/auth/'


@pytest.fixture
def non_mocked_hosts() -> list:
    return ['test']


@pytest.fixture(scope='session')
def event_loop() -> AbstractEventLoop:
    """Create an instance of the default event loop for each test case."""
    loop = get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def app():
    _app = create_app()
    async with LifespanManager(_app):
        yield _app


@pytest.fixture()
async def client(app) -> AsyncClient:
    """Async server client"""
    async with AsyncClient(app=app, base_url='http://test') as _client:
        yield _client


@pytest.fixture(autouse=True)
async def clear_db(app: FastAPI) -> None:
    yield
    for model in gather_documents():
        await model.get_motor_collection().drop()
        await model.get_motor_collection().drop_indexes()


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
    order_1.customer_id = '1'
    db_order_1 = Order(**order_1.model_dump(exclude={'customer_id'}) | {'customer_id': '1'})
    await db_order_1.insert()

    order_2: OrderOut = orders_factory.build()
    order_2.customer_id = '2'
    db_order_2 = Order(**order_2.model_dump(exclude={'customer_id'}) | {'customer_id': '2'})
    await db_order_2.insert()

    yield [order_1.serializable_dict(by_alias=True), order_2.serializable_dict(by_alias=True)]


class CarReadFactory(ModelFactory[CarOut]):
    __model__ = CarOut


class UserOutFactory(ModelFactory[UserOut]):
    __model__ = UserOut

    @classmethod
    def transmission(cls) -> str:
        return cls.__random__.choice(['automatic', 'automatic'])
