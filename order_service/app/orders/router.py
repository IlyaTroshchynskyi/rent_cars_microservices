from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Response

from app.custom_exceptions import CarServiceError, OrderNotFoundError
from app.dao.order import (
    create_order,
    delete_order,
    get_orders,
    retrieve_order_by_id,
    update_order_by_id,
    retrieve_order_and_cars,
)
from app.orders.schemas import OrderCreate, OrderCreateReturn, OrderOut, OrderUpdate, OrderCarOut

router = APIRouter(prefix='/orders', tags=['Orders'])


@router.get('/', response_model=list[OrderOut])
async def get_all_orders():
    return await get_orders()


@router.post('/', response_model=OrderCreateReturn, status_code=201)
async def create_new_order(order: OrderCreate):
    try:
        return await create_order(order)
    except CarServiceError as error:
        raise HTTPException(status_code=error.args[0], detail=error.args[1])


@router.delete('/{order_id}', response_class=Response,  status_code=204)
async def delete_order_by_id(order_id: PydanticObjectId):
    try:
        order = await retrieve_order_by_id(order_id)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail='Order not found')
    await delete_order(order)


@router.get('/{order_id}', response_model=OrderCarOut, responses={
    500: {'description': 'Internal Server Error'},
    404: {'description': 'Cars not found'},
    200: {'description': 'Car found'},
})
async def retrieve_order_with_cars(order_id: PydanticObjectId):
    try:
        return await retrieve_order_and_cars(order_id)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail='Order not found')
    except CarServiceError as error:
        raise HTTPException(status_code=error.args[0], detail=error.args[1])


@router.patch('/{order_id}', response_model=OrderCreateReturn, responses={
    500: {'description': 'Internal Server Error'},
    404: {'description': 'Cars not found'},
    200: {'description': 'Car updated'},
})
async def update_order(order_id: PydanticObjectId, order: OrderUpdate):
    try:
        return await update_order_by_id(order_id, order)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail='Order not found')
    except CarServiceError as error:
        raise HTTPException(status_code=error.args[0], detail=error.args[1])
