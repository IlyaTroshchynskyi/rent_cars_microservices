from httpx import AsyncClient
from tests.entity_creators import create_user
from tests.factories import TestUser

from app.users.schemas import UserOut


async def test_create_user(client: AsyncClient, users: tuple[TestUser], clear_tables):
    response = await client.post('/users/', json=users[0].model_dump(exclude={'id', 'order_ids'}))

    assert response.status_code == 201
    result = UserOut(**response.json()).model_dump(exclude={'id', 'order_ids'})
    assert result == users[0].model_dump(exclude={'id', 'order_ids', 'password'})


async def test_create_user_not_valid_passport(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user = users[0].model_dump(exclude={'id', 'order_ids', 'passport'}) | {'passport': '1'}

    response = await client.post('/users/', json=user)

    assert response.status_code == 422
    expected_msg = 'Value error, Format for passport  should be 5 digits or two big letter with 6 digits'
    assert response.json()['detail'][0]['msg'] == expected_msg


async def test_create_user_not_valid_phone(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user = users[0].model_dump(exclude={'id', 'order_ids', 'passport'}) | {'phone': '12'}

    response = await client.post('/users/', json=user)

    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'Value error, Format for phone should be like +380XXXXXXXXX'


async def test_get_users(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])

    response = await client.get('/users/')

    assert response.status_code == 200
    assert response.json() == [user_db.model_dump(exclude={'password'})]


async def test_get_user_by_id(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])

    response = await client.get(f'/users/{user_db.id}')

    assert response.status_code == 200
    assert response.json() == user_db.model_dump(exclude={'password'})


async def test_get_user_by_id_not_found(client: AsyncClient, users: tuple[TestUser], clear_tables):
    await create_user(users[0])

    response = await client.get('/users/1')

    assert response.status_code == 404
    assert response.json() == {'detail': 'User not found'}


async def test_delete_user_by_id(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])

    response = await client.delete(f'/users/{user_db.id}')

    assert response.status_code == 204


async def test_delete_user_by_id_not_found(client: AsyncClient, users: tuple[TestUser], clear_tables):
    await create_user(users[0])

    response = await client.delete('/users/1')

    assert response.status_code == 404
    assert response.json() == {'detail': 'User not found'}


async def test_update_user_by_id(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])

    response = await client.patch(
        f'/users/{user_db.id}',
        json={'first_name': 'TestFirstName', 'last_name': 'TetLastName'},
    )

    assert response.status_code == 200
    assert response.json()['first_name'] == 'TestFirstName'
    assert response.json()['last_name'] == 'TetLastName'


async def test_update_user_by_id_not_found(client: AsyncClient, users: tuple[TestUser], clear_tables):
    await create_user(users[0])

    response = await client.patch('/users/1', json={'first_name': 'TestFirstName', 'last_name': 'TetLastName'})

    assert response.status_code == 404
    assert response.json() == {'detail': 'User not found'}


async def test_update_user_not_valid_passport_phone(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])

    response = await client.patch(f'/users/{user_db.id}', json={'password': '1', 'phone': '12', 'passport': '1'})

    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'Value error, Format for phone should be like +380XXXXXXXXX'
    expected_msg = 'Value error, Format for passport  should be 5 digits or two big letter with 6 digits'
    assert response.json()['detail'][1]['msg'] == expected_msg
