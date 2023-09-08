from starlette.concurrency import run_in_threadpool
from tests.conftest import override_get_dynamo_db_table
from tests.factories import TestUser


async def create_user(user: TestUser) -> TestUser:
    users_table = override_get_dynamo_db_table().table
    await run_in_threadpool(users_table.put_item, Item=user.model_dump())
    user = await run_in_threadpool(users_table.get_item, Key={'id': user.id})
    return TestUser(**user['Item'])
