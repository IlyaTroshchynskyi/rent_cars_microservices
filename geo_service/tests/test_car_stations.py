from httpx import AsyncClient
from redis.asyncio import Redis

from app.car_stations.schemas import CarStationIn


async def test_create_cart_station(client: AsyncClient, car_stations: list[tuple[str, CarStationIn]]):
    response = await client.post(
        '/car-station/',
        json=car_stations[0][1].model_dump()
    )
    assert response.status_code == 201
    assert response.json() == car_stations[0][1].model_dump()


async def test_get_car_stations(client: AsyncClient, car_stations: list[tuple[str, CarStationIn]]):
    response = await client.get('/car-station/')

    assert response.status_code == 200
    assert response.json() == [car_stations[0][1].model_dump()]


async def test_delete_cart_station(client: AsyncClient, car_stations: list[tuple[str, CarStationIn]]):
    response = await client.delete(f'/car-station/{car_stations[0][0]}')

    assert response.status_code == 204


async def test_delete_cart_station_not_found(client: AsyncClient, car_stations: list[tuple[str, CarStationIn]]):
    response = await client.delete('/car-station/1')

    assert response.status_code == 404
    assert response.json() == {'detail': 'Car station not found'}


async def test_retrieve_cart_station(client: AsyncClient, car_stations: list[tuple[str, CarStationIn]]):
    response = await client.get(f'/car-station/{car_stations[0][0]}')

    assert response.status_code == 200
    assert response.json() == car_stations[0][1].model_dump()


async def test_retrieve_cart_station_not_found(
        client: AsyncClient,
        car_stations: list[tuple[str, CarStationIn]],
):
    response = await client.get('/car-station/1')

    assert response.status_code == 404
    assert response.json() == {'detail': 'Car station not found'}


async def test_update_cart_station(
        client: AsyncClient,
        car_stations: list[tuple[str, CarStationIn]],
        redis_client: Redis,
):
    response = await client.patch(f'/car-station/{car_stations[0][0]}', json={'address': 'Street Updated'})

    assert response.status_code == 200
    assert response.json()['address'] == 'Street Updated'
    assert response.json()['working_hours'] == car_stations[0][1].working_hours


async def test_update_wrong_working_hours(client: AsyncClient, car_stations: list[tuple[str, CarStationIn]]):
    response = await client.patch(f'/car-station/{car_stations[0][0]}', json={'working_hours': '10:000:23'})
    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'Value error, Must be such format H:M-H:M'


async def test_update_not_found(client: AsyncClient, car_stations: list[tuple[str, CarStationIn]]):
    response = await client.patch('/car-station/1', json={'working_hours': '10:00-23:23'})
    assert response.status_code == 404
    assert response.json() == {'detail': 'Car station not found'}
