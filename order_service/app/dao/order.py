from beanie import PydanticObjectId


from app.custom_exceptions import OrderNotFoundError
from app.dao.car import get_order_cars
from app.models import Order
from app.orders.schemas import OrderCreate, OrderUpdate, OrderCarOut


async def get_orders() -> list[Order]:
    order = await Order.find_all().to_list()
    return order


async def create_order(data: OrderCreate) -> Order:
    rental_time = data.rental_date_end - data.rental_date_start
    total = await _count_order_total(data.order_cars, rental_time.days)
    order = Order(**data.model_dump(), rental_time=rental_time.days, total_cost=total)
    return await order.insert()


async def delete_order(order: Order):
    await order.delete()


async def retrieve_order_by_id(order_id: PydanticObjectId) -> Order:
    if order := await Order.get(order_id):
        return order
    raise OrderNotFoundError


async def retrieve_order_and_cars(order_id: PydanticObjectId) -> OrderCarOut:
    db_order = await retrieve_order_by_id(order_id)
    cars = await get_order_cars(db_order.order_cars)
    return OrderCarOut(**db_order.model_dump(exclude={'order_cars'}), order_cars=cars)


async def update_order_by_id(order_id: PydanticObjectId, data: OrderUpdate) -> Order:
    order = await Order.get(order_id)
    if not order:
        raise OrderNotFoundError

    update_query = {'$set': {
        field: value for field, value in data.model_dump(exclude_unset=True).items()
    }}

    if data.rental_date_end and data.rental_date_end:
        rental_time = data.rental_date_end - data.rental_date_start
        total = await _count_order_total(data.order_cars or order.order_cars, rental_time.days)
        update_query['$set'].update({'total_cost': total, 'rental_time': rental_time.days})

    await order.update(update_query)

    # Need extra query because when I update_order list response has not updated list of values
    order = await Order.get(order_id)
    return order


async def _count_order_total(car_ids: list[int], rental_time: int) -> int:
    total = 0
    cars = await get_order_cars(car_ids)
    for car in cars:
        total += car.rental_cost * rental_time

    return total
