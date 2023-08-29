import asyncio

from aio_pika.abc import AbstractIncomingMessage

from app.config import get_settings
from app.rebbit_connection import get_connection_pool


async def on_message(message: AbstractIncomingMessage):
    await asyncio.sleep(1)
    print(f' [x] Received {message.body}')
    await message.ack()


async def handle_car_trip(rabbit_pool):
    async with rabbit_pool.acquire() as connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(get_settings().QUEUE_NAME, durable=True)

        # Start listening the queue with name 'task_queue'
        await queue.consume(on_message)
        await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(handle_car_trip(get_connection_pool()))
