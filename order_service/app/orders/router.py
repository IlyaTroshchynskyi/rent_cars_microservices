from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Response

from app.dao.order import create_order, delete_order, get_orders, retrieve_order, update_order
from app.orders.schemas import OrderCreate, OrderCreateReturn, OrderRead, OrderUpdate

router = APIRouter(prefix='/orders', tags=['Orders'])


@router.get('/', response_model=list[OrderRead])
async def get():
    return await get_orders()


@router.post('/', response_model=OrderCreateReturn, status_code=201)
async def create(order: OrderCreate):
    order_result = await create_order(order)
    return order_result


@router.delete('/{order_id}', response_class=Response,  status_code=204)
async def delete(order_id: PydanticObjectId):
    order = await retrieve_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    await delete_order(order)


@router.get('/{order_id}', response_model=OrderRead)
async def retrieve(order_id: PydanticObjectId):
    if order := await retrieve_order(order_id):
        return order
    raise HTTPException(status_code=404, detail='Order not found')


@router.patch('/{order_id}', response_model=OrderCreateReturn)
async def update(order_id: PydanticObjectId, order: OrderUpdate):
    if order := await update_order(order_id, order):
        return order
    raise HTTPException(status_code=404, detail='Order not found')
