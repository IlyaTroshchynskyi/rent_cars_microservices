from typing import Annotated

from fastapi import Depends
from passlib.context import CryptContext

from app.db import get_user_table, SingletonUserTable


def get_crypto_context() -> CryptContext:
    return CryptContext(schemes=['bcrypt'], deprecated='auto')


password_context = Annotated[CryptContext, Depends(get_crypto_context)]
user_table = Annotated[SingletonUserTable, Depends(get_user_table)]
