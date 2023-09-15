import asyncio
import os

import boto3
from httpx import AsyncClient
import pytest
from starlette.concurrency import run_in_threadpool
from tests.factories import TestUser

from app import create_app
from app.config import get_settings


def pytest_configure(config: pytest.Config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    os.environ['ENV'] = 'dev'
    os.environ['DYNAMODB_ENDPOINT'] = 'http://localhost:8000'
    os.environ['USER_TABLE'] = 'user_test'


def override_get_dynamo_db_table():
    settings = get_settings()

    class SingletonUserTable:
        def __init__(self):
            self._ddb = boto3.resource('dynamodb', endpoint_url=settings.DYNAMODB_ENDPOINT)
            self.table = self._ddb.Table(settings.USER_TABLE)

    return SingletonUserTable()


@pytest.fixture(scope='session')
async def app():
    from app.db import get_user_table
    _app = create_app()
    _app.dependency_overrides[get_user_table] = override_get_dynamo_db_table
    yield _app


@pytest.fixture(scope='session')
def db_client():
    client = boto3.client('dynamodb', endpoint_url=get_settings().DYNAMODB_ENDPOINT)
    yield client


@pytest.fixture(scope='session', autouse=True)
async def create_delete_user_table(db_client):
    settings = get_settings()
    await run_in_threadpool(
        db_client.create_table,
        TableName=settings.USER_TABLE,
        AttributeDefinitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'},
            {'AttributeName': 'user_name', 'AttributeType': 'S'},
        ],
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        ProvisionedThroughput={
            'ReadCapacityUnits': settings.READ_CAPACITY_UNITS,
            'WriteCapacityUnits': settings.WRITE_CAPACITY_UNITS,
        },
        GlobalSecondaryIndexes=[
            {
                'IndexName': settings.USER_NAME_INDEX,
                'KeySchema': [{'AttributeName': 'user_name', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': settings.READ_CAPACITY_UNITS,
                    'WriteCapacityUnits': settings.WRITE_CAPACITY_UNITS
                }
            },
        ],
    )
    yield
    await run_in_threadpool(db_client.delete_table, TableName=settings.USER_TABLE)


@pytest.fixture(scope='function')
async def clear_tables(db_client):
    yield
    settings = get_settings()
    response = db_client.scan(TableName=settings.USER_TABLE)
    delete_requests = []
    for item in response['Items']:
        delete_requests.append({'DeleteRequest': {'Key': {'id': item['id']}}})
    if delete_requests:
        await run_in_threadpool(db_client.batch_write_item, RequestItems={settings.USER_TABLE: delete_requests})


@pytest.fixture(scope='function')
async def client(app, db_client) -> AsyncClient:
    async with AsyncClient(app=app, base_url='http://test/') as client:
        yield client


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='function')
async def users() -> tuple[TestUser]:
    user_1 = TestUser()
    user_2 = TestUser()
    yield user_1, user_2
