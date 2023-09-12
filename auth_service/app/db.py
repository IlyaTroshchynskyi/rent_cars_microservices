import boto3
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from app.config import get_settings


def is_develop() -> bool:
    return get_settings().ENV == 'dev'


def init_dynamodb_resource() -> DynamoDBServiceResource:
    if is_develop():
        ddb = boto3.resource('dynamodb', endpoint_url=get_settings().DYNAMODB_ENDPOINT)
    else:
        ddb = boto3.resource('dynamodb')
    return ddb


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonUserTable(metaclass=Singleton):
    def __init__(self):
        self._ddb = init_dynamodb_resource()
        self.table = self._ddb.Table(get_settings().USER_TABLE)


def get_user_table() -> SingletonUserTable:
    return SingletonUserTable()
