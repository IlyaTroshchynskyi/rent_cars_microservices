import uuid

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table
from passlib.context import CryptContext
from pydantic import TypeAdapter
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.custom_exceptions import UsernameAlreadyTakenError, UserNotFoundError
from app.users.schemas import UserIn, UserOut, UserUpdate, UserUpdateParams, UserWithPasswd


async def get_users(users_table: Table) -> list[UserOut]:
    users = await run_in_threadpool(users_table.scan)
    return TypeAdapter(list[UserOut]).validate_python(users['Items'])


async def create_user(users_table: Table, user: UserIn, pwd_context: CryptContext) -> UserOut:
    try:
        await get_user_by_username(users_table, user.user_name)
    except UserNotFoundError:
        user_id = str(uuid.uuid4())
        hashed_password = _generate_password_hash(user.password, pwd_context)
        await run_in_threadpool(
            users_table.put_item,
            Item=user.model_dump(exclude={'password'}) | {'id': user_id, 'password': hashed_password},
        )
        return await get_user_by_id(users_table, user_id)

    raise UsernameAlreadyTakenError


async def get_user_by_id(users_table: Table, user_id: str) -> UserOut:
    user_db = await run_in_threadpool(users_table.get_item, Key={'id': user_id})
    if user_db.get('Item'):
        return UserOut(**user_db['Item'])
    raise UserNotFoundError


async def delete_user_by_id(users_table: Table, user_id: str):
    user_db = await run_in_threadpool(users_table.delete_item, Key={'id': user_id}, ReturnValues='ALL_OLD')
    if not user_db.get('Attributes'):
        raise UserNotFoundError


async def update_user_by_id(users_table: Table, user_id: str, user: UserUpdate) -> UserOut:
    if user.user_name:
        try:
            await get_user_by_username(users_table, user.user_name)
            raise UsernameAlreadyTakenError
        except UserNotFoundError:
            pass

    user_update_params = _build_user_update_params(user)
    await get_user_by_id(users_table, user_id)
    await run_in_threadpool(
        users_table.update_item,
        Key={'id': user_id},
        UpdateExpression=user_update_params.set_expression,
        ExpressionAttributeValues=user_update_params.attribute_values,
        ExpressionAttributeNames=user_update_params.attribute_names,
    )
    return await get_user_by_id(users_table, user_id)


async def get_user_by_username(users_table: Table, username: str) -> UserWithPasswd:
    user_db = await run_in_threadpool(
        users_table.query,
        IndexName=get_settings().USER_NAME_INDEX,
        KeyConditionExpression=Key('user_name').eq(username),
    )
    if user_db['Items']:
        return UserWithPasswd(**user_db['Items'][0])
    raise UserNotFoundError


def _build_user_update_params(user: UserUpdate) -> UserUpdateParams:
    """
    Example:
        update_expression = set  #first_name = :first_name,  #last_name = :last_name
        attribute_values = {':first_name': 'TestFirstName', ':last_name': 'TetLastName'}
        attribute_names = {'#first_name': 'first_name', '#last_name': 'last_name'}
    """
    update_expression = []
    attribute_values = {}
    attribute_names = {}

    for key, value in user.model_dump(exclude_unset=True).items():
        update_expression.append(f' #{key.lower()} = :{key.lower()}')
        attribute_values[f':{key.lower()}'] = value
        attribute_names[f'#{key.lower()}'] = key.lower()

    return UserUpdateParams(
        set_expression='set ' + ', '.join(update_expression),
        attribute_values=attribute_values,
        attribute_names=attribute_names,
    )


def _generate_password_hash(password: str, pwd_context: CryptContext):
    return pwd_context.hash(password)
