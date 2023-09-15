from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from mypy_boto3_dynamodb.service_resource import Table
from passlib.context import CryptContext
from starlette.concurrency import run_in_threadpool

from app.auth.schemas import UpdatePassword
from app.config import get_settings
from app.custom_exceptions import InvalidCurrentPasswordError, InvalidOldPasswordError, UserNotFoundError
from app.dao.users import get_user_by_username
from app.dependency import user_table
from app.users.schemas import UserWithPasswd


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')


async def authenticate_user(
        user_table: Table,
        username: str, password: str,
        pwd_context: CryptContext,
) -> UserWithPasswd:
    user = await get_user_by_username(user_table, username)
    if not verify_password(pwd_context, password, user.password):
        raise InvalidCurrentPasswordError
    return user


def verify_password(pwd_context: CryptContext, plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(username: str) -> str:
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now() + access_token_expires
    claims = {'sub': username, 'exp': expire}
    encoded_jwt = jwt.encode(claims, settings.SECRET_KEY, algorithm='HS256')
    return encoded_jwt


async def get_current_user(db: user_table, token: Annotated[str, Depends(oauth2_scheme)]) -> UserWithPasswd:
    credentials_exception = HTTPException(401, 'Could not validate credentials', {'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(token,  get_settings().SECRET_KEY, algorithms=['HS256'])
        username = payload.get('sub')
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    try:
        user = await get_user_by_username(db.table, username)
    except UserNotFoundError:
        raise credentials_exception
    return user


async def update_user_password(
        db: Table,
        passwords: UpdatePassword,
        pwd_context: CryptContext,
        user: UserWithPasswd,
) -> UserWithPasswd:
    if not pwd_context.verify(passwords.old_password, user.password):
        raise InvalidOldPasswordError

    await run_in_threadpool(
        db.update_item,
        Key={'id': user.id},
        UpdateExpression='set #password = :password',
        ExpressionAttributeValues={':password': pwd_context.hash(passwords.new_password)},
        ExpressionAttributeNames={'#password': 'password'},
    )
    return user
