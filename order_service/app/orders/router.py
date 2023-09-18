from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Response

from app.custom_exceptions import CarServiceError, NotOwnerError, OrderNotFoundError
from app.dao.order import (
    create_order,
    delete_order,
    get_orders,
    retrieve_order_and_cars,
    retrieve_order_by_id,
    update_order_by_id,
)
from app.dependency import current_user
from app.orders.schemas import OrderCarOut, OrderCreate, OrderCreateReturn, OrderOut, OrderUpdate

router = APIRouter(prefix='/orders', tags=['Orders'])


@router.get('/', response_model=list[OrderOut])
async def get_all_orders():
    return await get_orders()


@router.post('/', response_model=OrderCreateReturn, status_code=201)
async def create_new_order(order: OrderCreate, user: current_user):
    try:
        return await create_order(order, user.id)
    except CarServiceError as error:
        raise HTTPException(status_code=error.args[0], detail=error.args[1])


@router.delete('/{order_id}', response_class=Response, status_code=204)
async def delete_order_by_id(order_id: PydanticObjectId, user: current_user):
    try:
        order = await retrieve_order_by_id(order_id, user.id)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail='Order not found')
    except NotOwnerError:
        raise HTTPException(status_code=403, detail='User is not owner of order')
    await delete_order(order)


@router.get('/{order_id}', response_model=OrderCarOut, responses={
    500: {'description': 'Internal Server Error'},
    404: {'description': 'Cars not found'},
    403: {'description': 'User is not owner'},
    200: {'description': 'Car found'},
})
async def retrieve_order_with_cars(order_id: PydanticObjectId, user: current_user):
    try:
        return await retrieve_order_and_cars(order_id, user.id)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail='Order not found')
    except CarServiceError as error:
        raise HTTPException(status_code=error.args[0], detail=error.args[1])
    except NotOwnerError:
        raise HTTPException(status_code=403, detail='User is not owner of order')


@router.patch('/{order_id}', response_model=OrderCreateReturn, responses={
    500: {'description': 'Internal Server Error'},
    404: {'description': 'Cars not found'},
    403: {'description': 'User is not owner'},
    200: {'description': 'Car updated'},
})
async def update_order(order_id: PydanticObjectId, order: OrderUpdate, user: current_user):
    try:
        return await update_order_by_id(order_id, order, user.id)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail='Order not found')
    except CarServiceError as error:
        raise HTTPException(status_code=error.args[0], detail=error.args[1])
    except NotOwnerError:
        raise HTTPException(status_code=403, detail='User is not owner of order')
