from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.auth_service import authenticate_user, create_access_token, get_current_user, update_user_password
from app.auth.schemas import Token, UpdatePassword
from app.custom_exceptions import (
    BadCredentialsError,
    InvalidCurrentPasswordError,
    InvalidOldPasswordError,
    UserNotFoundError,
)
from app.dependency import password_context, user_table
from app.users.schemas import UserOut, UserWithPasswd


router = APIRouter(tags=['Auth'])


@router.get('/profile', response_model=UserOut)
async def get_current_user_profile(current_user: Annotated[UserWithPasswd, Depends(get_current_user)]):
    return current_user


@router.post('/token', response_model=Token, status_code=201)
async def create_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: user_table,
        pwd_context: password_context,
):
    try:
        user = await authenticate_user(db.table, form_data.username, form_data.password, pwd_context)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail='User not found')
    except InvalidCurrentPasswordError:
        raise HTTPException(401, 'Incorrect password', {'WWW-Authenticate': 'Bearer'})

    access_token = create_access_token(user.user_name)
    return Token(access_token=access_token, token_type='bearer')


@router.post('/change-password', response_model=UserOut)
async def update_password(
        db: user_table,
        passwords: UpdatePassword,
        pwd_context: password_context,
        current_user: Annotated[UserWithPasswd, Depends(get_current_user)],
):
    try:
        return await update_user_password(db.table, passwords, pwd_context, current_user)
    except InvalidOldPasswordError:
        raise HTTPException(401, 'Incorrect old password')


@router.get('/is-user-logged-in', response_model=UserOut)
async def is_user_authorized(current_user: Annotated[UserWithPasswd, Depends(get_current_user)]):
    """This endpoint to validate token for other services"""
    try:
        return current_user
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail='User not found')
    except BadCredentialsError:
        raise HTTPException(401, 'Could not validate credentials', {'WWW-Authenticate': 'Bearer'})
