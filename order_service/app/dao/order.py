from beanie import PydanticObjectId

from app.common.send_resquest import result_to_json
from app.models import Order
from app.orders.schemas import OrderCreate, OrderUpdate


async def get_orders() -> list[Order]:
    order = await Order.find_all().to_list()
    return order


async def create_order(data: OrderCreate) -> Order:
    rental_time = data.rental_date_end - data.rental_date_start
    total = await _count_order_total(data.order_cars, rental_time.days)
    order = Order(**data.dict(), rental_time=rental_time.days, total_cost=total)
    return await order.insert()


async def delete_order(order: Order):
    await order.delete()


async def retrieve_order(order_id: PydanticObjectId) -> Order:
    order = await Order.get(order_id)
    return order


async def update_order(order_id: PydanticObjectId, data: OrderUpdate) -> Order | None:
    order = await Order.get(order_id)
    if not order:
        return
    update_query = {'$set': {
        field: value for field, value in data.model_dump(exclude_unset=True).items()
    }}

    if data.rental_date_end and data.rental_date_end:
        rental_time = data.rental_date_end - data.rental_date_start
        total = await _count_order_total(data.order_cars or order.order_cars, rental_time.days)
        update_query['$set'].update({'total_cost': total, 'rental_time': rental_time.days})

    await order.update(update_query)

    # Need extra query because when I update list response has not updated list of values
    order = await Order.get(order_id)
    return order


async def _count_order_total(car_ids: list[int], rental_time: int) -> int:
    total = 0
    cars = await result_to_json()  # simulate another service
    for car in cars:
        total += car['rental_cost'] * rental_time

    return total
