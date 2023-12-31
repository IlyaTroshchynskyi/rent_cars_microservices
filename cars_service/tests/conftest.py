import asyncio
import os
from io import BytesIO
from pathlib import Path
from typing import Generator

import aiofiles
from alembic.command import downgrade, upgrade
from alembic.config import Config
from httpx import AsyncClient
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import Session, SessionTransaction

from app.cars.schemas import CarOut
from app.config import get_settings
from app.reviews.schemas import ReviewIn
from app import create_app


def pytest_configure(config: pytest.Config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    base_dir: Path = Path(__file__).resolve().parent.parent
    os.environ['DATABASE_URL'] = 'postgresql+psycopg://test_postgres:test_postgres@localhost:5433/rent-cars-test'
    os.environ['POSTGRES_HOST'] = 'localhost'
    os.environ['POSTGRES_PORT'] = '5433'
    os.environ['POSTGRES_DB'] = 'rent-cars-test'
    os.environ['POSTGRES_USER'] = 'test_postgres'
    os.environ['POSTGRES_PASSWORD'] = 'test_postgres'
    os.environ['RABBITMQ_URL'] = 'amqp://rmuser:rmpassword@127.0.0.1/'
    os.environ['QUEUE_NAME'] = 'test'
    os.environ['GEO_SERVICE_BASE_URL'] = 'http://test-car-service-host/cars/'
    os.environ['STATIC_URL'] = 'http://test-car-service-host/'
    os.environ['STATIC_DIR']: str = os.path.join(base_dir, 'app/') + 'static/'
    os.environ['STATIC_URL']: str
    os.environ['TEST_DIR']: str = os.path.join(base_dir, 'tests/')


@pytest.fixture(scope='session')
async def app():
    _app = create_app()
    yield _app


@pytest.fixture(scope='session')
async def client(app) -> AsyncClient:
    async with AsyncClient(app=app, base_url='http://test') as client:
        yield client


@pytest.fixture
async def db(app) -> AsyncSession:
    """https://github.com/sqlalchemy/sqlalchemy/issues/5811#issuecomment-756269881"""
    async_engine = create_async_engine(os.environ['DATABASE_URL'])

    async with async_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()
        AsyncSessionLocal = async_sessionmaker(
            bind=conn,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        async_session = AsyncSessionLocal()

        @event.listens_for(async_session.sync_session, 'after_transaction_end')
        def end_savepoint(session: Session, transaction: SessionTransaction) -> None:
            if conn.closed:
                return
            if not conn.in_nested_transaction():
                if conn.sync_connection:
                    conn.sync_connection.begin_nested()

        def get_test_session() -> Generator:
            try:
                yield AsyncSessionLocal()
            except SQLAlchemyError:
                pass

        from app.db import get_session
        app.dependency_overrides[get_session] = get_test_session

        yield async_session
        await async_session.close()
        await conn.rollback()


@pytest.fixture(scope='session')
def alembic_config() -> Config:
    config = Config()
    config.set_main_option('script_location', f'{get_settings().BASE_DIR}/migrations')
    config.set_main_option('sqlalchemy.url', os.environ['DATABASE_URL'])
    return config


@pytest.fixture(scope='session', autouse=True)
async def make_migration(alembic_config) -> None:
    engine = create_engine(os.environ['DATABASE_URL'], echo=True)
    with engine.begin():
        upgrade(alembic_config, 'head')
        yield
    with engine.begin():
        downgrade(alembic_config, 'base')


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@register_fixture(name='cars_factory')
class CarReadFactory(ModelFactory[CarOut]):
    __model__ = CarOut
    __random_seed__ = 1

    @classmethod
    def car_number(cls) -> str:
        return cls.__random__.choice(['AM1234AO', 'AX2345AF'])

    @classmethod
    def year(cls) -> str:
        return cls.__random__.choice([2021, 2022])

    @classmethod
    def transmission(cls) -> str:
        return cls.__random__.choice(['automatic', 'automatic'])

    @classmethod
    def rental_cost(cls) -> str:
        return cls.__random__.choice([10, 15])

    @classmethod
    def engine(cls) -> str:
        return cls.__random__.choice(['2.1L', '2.2L'])

    @classmethod
    def image(cls) -> str:
        return cls.__random__.choice(
            ['http://127.0.0.1:8000/static/AM1234AO.jpg',
             'http://127.0.0.1:8000/static/AM1234AO.jpg']
        )


@pytest.fixture(scope='function')
async def cars(cars_factory: CarReadFactory) -> tuple[CarOut]:
    car_1 = cars_factory.build()
    car_2 = cars_factory.build()
    yield car_1, car_2


async def create_test_image(filename):
    settings = get_settings()
    file_content = b'This is the content of the file.'
    file_obj = BytesIO(file_content)

    async with aiofiles.open(settings.STATIC_DIR + filename + '.jpg', 'wb') as output_file:
        await output_file.write(file_obj.read())


@register_fixture(name='review_factory')
class ReviewInFactory(ModelFactory[ReviewIn]):
    __model__ = ReviewIn


@pytest.fixture(scope='function')
async def reviews(review_factory: ReviewInFactory) -> tuple[ReviewIn]:
    review_1 = review_factory.build()
    review_2 = review_factory.build()
    yield review_1, review_2
