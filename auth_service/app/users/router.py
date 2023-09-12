from fastapi import APIRouter, HTTPException
from fastapi import Response

from app.custom_exceptions import UserNotFoundError
from app.dao.users import create_user, delete_user_by_id, get_user_by_id, get_users, update_user_by_id
from app.dependency import password_context, user_table
from app.users.schemas import UserIn, UserOut, UserUpdate


router = APIRouter(prefix='/users', tags=['Users'])


@router.get('/', response_model=list[UserOut])
async def get_all_users(db: user_table):
    return await get_users(db.table)


@router.post('/', response_model=UserOut, status_code=201)
async def create_new_user(user: UserIn, db: user_table, pwd_context: password_context):
    return await create_user(db.table, user, pwd_context)


@router.get('/{user_id}', response_model=UserOut)
async def get_user(user_id: str, db: user_table):
    try:
        return await get_user_by_id(db.table, user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail='User not found')


@router.delete('/{user_id}', response_class=Response, status_code=204)
async def delete_user(user_id: str, db: user_table):
    try:
        await delete_user_by_id(db.table, user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail='User not found')


@router.patch('/{user_id}', response_model=UserOut)
async def update_user(user_id: str, db: user_table, user: UserUpdate):
    try:
        return await update_user_by_id(db.table, user_id, user)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail='User not found')
