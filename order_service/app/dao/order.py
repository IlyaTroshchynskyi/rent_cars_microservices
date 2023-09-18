from beanie import PydanticObjectId

from app.custom_exceptions import NotOwnerError, OrderNotFoundError
from app.custom_metrics import total_orders
from app.dao.car import get_order_cars, update_cars_status
from app.models import Order
from app.orders.schemas import CarStatusEnum, OrderCarOut, OrderCreate, OrderUpdate


async def get_orders() -> list[Order]:
    order = await Order.find_all().to_list()
    return order


async def create_order(order: OrderCreate, customer_id: str) -> Order:
    rental_time = order.rental_date_end - order.rental_date_start
    total = await _count_order_total(order.order_cars, rental_time.days)
    order_db = Order(**order.model_dump(), rental_time=rental_time.days, total_cost=total, customer_id=customer_id)
    await update_cars_status(order.order_cars, CarStatusEnum.ACTIVE)
    total_orders.labels('total_orders').inc(total)
    return await order_db.insert()


async def delete_order(order: Order):
    await order.delete()


async def retrieve_order_by_id(order_id: PydanticObjectId, customer_id: str) -> Order:
    if order := await Order.get(order_id):
        if order.customer_id != customer_id:
            raise NotOwnerError

        return order
    raise OrderNotFoundError


async def retrieve_order_and_cars(order_id: PydanticObjectId, customer_id: str) -> OrderCarOut:
    db_order = await retrieve_order_by_id(order_id, customer_id)
    cars = await get_order_cars(db_order.order_cars)
    return OrderCarOut(**db_order.model_dump(exclude={'order_cars'}), order_cars=cars)


async def update_order_by_id(order_id: PydanticObjectId, order: OrderUpdate, customer_id: str) -> Order:
    order_db = await Order.get(order_id)
    if not order_db:
        raise OrderNotFoundError
    if order_db.customer_id != customer_id:
        raise NotOwnerError

    update_query = {'$set': {
        field: value for field, value in order.model_dump(exclude_unset=True).items()
    }}

    if order.rental_date_end and order.rental_date_end:
        rental_time = order.rental_date_end - order.rental_date_start
        total = await _count_order_total(order.order_cars or order_db.order_cars, rental_time.days)
        update_query['$set'].update({'total_cost': total, 'rental_time': rental_time.days})

    await order_db.update(update_query)

    # Need extra query because when I update_order list response has not updated list of values
    order = await Order.get(order_id)
    return order


async def _count_order_total(car_ids: list[int], rental_time: int) -> int:
    total = 0
    cars = await get_order_cars(car_ids)
    for car in cars:
        total += car.rental_cost * rental_time

    return total
