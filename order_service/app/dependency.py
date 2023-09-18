from typing import Annotated

from fastapi import Depends, Header, HTTPException
from httpx import AsyncClient

from app.config import get_settings
from app.users.schemas import UserOut


async def get_current_user(auth_token: Annotated[str, Header()]) -> UserOut:
    async with AsyncClient() as client:
        response = await client.get(
            f'{get_settings().AUTH_SERVICE_BASE_URL}is-user-logged-in',
            headers={'Authorization': f'Bearer {auth_token}'},
        )

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail='User not found')
    if response.status_code == 401:
        raise HTTPException(401, 'Could not validate credentials', {'WWW-Authenticate': 'Bearer'})
    if response.status_code == 200:
        return UserOut(**response.json())
    raise HTTPException(500, 'Internal Server Error')

current_user = Annotated[UserOut, Depends(get_current_user)]
