from passlib.context import CryptContext
from starlette.concurrency import run_in_threadpool
from tests.conftest import override_get_dynamo_db_table
from tests.factories import TestUser


async def create_user(user: TestUser) -> TestUser:
    return await run_in_threadpool(_wrapper_create_user, user)


def _wrapper_create_user(user) -> TestUser:
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    users_table = override_get_dynamo_db_table().table
    users_table.put_item(Item=user.model_dump(exclude={'password'}) | {'password': pwd_context.hash(user.password)})
    user = users_table.get_item(Key={'id': user.id})
    return TestUser(**user['Item'])
