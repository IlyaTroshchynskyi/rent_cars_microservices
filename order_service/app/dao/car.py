from httpx import AsyncClient

from app.config import get_settings
from app.custom_exceptions import CarServiceError
from app.orders.schemas import CarOut


async def get_order_cars(car_ids: list[int]) -> list[CarOut]:
    response_cars = await _request_cars(car_ids)

    if set(car_ids) != {car['id'] for car in response_cars}:
        raise CarServiceError(404, 'One ore more cars not found')

    return response_cars


async def _request_cars(car_ids) -> list[CarOut]:
    async with AsyncClient() as client:
        response = await client.get(get_settings().CAR_SERVICE_BASE_URL, params={'car_ids': car_ids})

    if response.status_code != 200:
        raise CarServiceError(500, 'Internal Server Error')
    return [CarOut(**car) for car in response.json()]
