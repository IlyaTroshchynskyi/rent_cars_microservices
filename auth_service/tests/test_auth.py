from httpx import AsyncClient
from tests.entity_creators import create_user
from tests.factories import TestUser

from app.auth.auth_service import create_access_token


async def test_get_user_profile(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])
    token = create_access_token(user_db.user_name)

    response = await client.get('/auth/profile', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    assert response.json() == user_db.model_dump(exclude={'password'})


async def test_get_user_profile_bad_token(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])
    token = create_access_token(user_db.user_name)

    response = await client.get('/auth/profile', headers={'Authorization': f'Bearer {token}1'})

    assert response.status_code == 401
    assert response.json() == {'detail': 'Could not validate credentials'}


async def test_get_user_profile_wrong_user_name(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])
    token = create_access_token(user_db.user_name + '1')

    response = await client.get('/auth/profile', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 401
    assert response.json() == {'detail': 'Could not validate credentials'}


async def test_get_token(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])

    response = await client.post('/auth/token', data={'username': user_db.user_name, 'password': users[0].password})

    assert response.status_code == 201
    assert 'access_token' in response.json()
    assert response.json()['token_type'] == 'bearer'


async def test_create_token_user_not_found(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])

    response = await client.post(
        '/auth/token',
        data={'username': user_db.user_name + '1', 'password': users[0].password},
    )

    assert response.status_code == 404
    assert response.json() == {'detail': 'User not found'}


async def test_create_token_with_wrong_pswd(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])

    response = await client.post(
        '/auth/token',
        data={'username': user_db.user_name, 'password': users[0].password + '1'},
    )

    assert response.status_code == 401
    assert response.json() == {'detail': 'Incorrect password'}


async def test_update_user_password(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])
    token = create_access_token(user_db.user_name)

    response = await client.post(
        '/auth/change-password',
        json={'old_password': users[0].password, 'new_password': 'new_password'},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200
    assert response.json() == user_db.model_dump(exclude={'password'})


async def test_update_user_password_incorrect_old(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])
    token = create_access_token(user_db.user_name)

    response = await client.post(
        '/auth/change-password',
        json={'old_password': users[0].password + '1', 'new_password': 'new_password'},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 401
    assert response.json() == {'detail': 'Incorrect old password'}


async def test_is_user_authorized(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])
    token = create_access_token(user_db.user_name)

    response = await client.get('/auth/is-user-logged-in', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    assert response.json() == user_db.model_dump(exclude={'password'})


async def test_is_user_authorized_bad_token(client: AsyncClient, users: tuple[TestUser], clear_tables):
    response = await client.get('/auth/is-user-logged-in', headers={'Authorization': 'Bearer 1'})

    assert response.status_code == 401
    assert response.json() == {'detail': 'Could not validate credentials'}


async def test_is_user_authorized_wrong_user_name(client: AsyncClient, users: tuple[TestUser], clear_tables):
    user_db = await create_user(users[0])
    token = create_access_token(user_db.user_name + '1')

    response = await client.get('/auth/is-user-logged-in', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 401
    assert response.json() == {'detail': 'Could not validate credentials'}
