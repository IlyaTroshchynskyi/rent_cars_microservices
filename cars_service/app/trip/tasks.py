import asyncio
import random

from aio_pika import DeliveryMode, Message
from aio_pika.pool import Pool

from app.config import get_settings
from app.trip.schemas import CoordinateMessage


async def start_trip(car_number: str, rabbit_pool: Pool):
    settings = get_settings()

    async with rabbit_pool.acquire() as connection:
        channel = await connection.channel()
        await channel.declare_queue(settings.QUEUE_NAME, durable=True)

        for _ in range(5):
            msg = _form_message(car_number)
            await channel.default_exchange.publish(
                Message(body=msg.model_dump_json().encode(), delivery_mode=DeliveryMode.PERSISTENT),
                routing_key=settings.QUEUE_NAME,
            )
            await asyncio.sleep(1)


def _form_message(car_number: str) -> CoordinateMessage:
    msg = CoordinateMessage(
        car_number=car_number,
        latitude=random.uniform(-90, 90),
        longitude=random.uniform(-180, 180),
    )
    return msg
