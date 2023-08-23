import json

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import CarReadFactory, create_test_image

from app.cars.schemas import CarOut
from app.config import settings
from app.models import Car
from tests.entity_creators import create_car


async def test_create_car(client: AsyncClient, cars_factory: CarReadFactory, db: AsyncSession):
    filename = 'test.jpg'
    car = cars_factory.build()

    data = {
        'file': (filename, open(settings.TEST_DIR + filename, 'rb'), 'image/jpeg'),
        'car': (None, json.dumps(car.dict(exclude={'id', 'image'})), 'application/json'),
    }
    response = await client.post('/cars/', files=data)
    assert response.status_code == 201
    assert response.json() == car.dict(exclude={'id', 'image'})


async def test_get_cars(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    await create_car(db, cars[0])
    await create_car(db, cars[1])

    response = await client.get('/cars/')

    assert response.status_code == 200
    assert response.json() == [car.model_dump() for car in sorted(cars, key=lambda x: x.id)]


async def test_delete_car(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    await create_car(db, cars[0])
    await create_car(db, cars[1])
    await create_test_image(cars[0].car_number)
    query = select(Car)
    result = await db.execute(query)
    assert len(result.fetchall()) == 2

    response = await client.delete(f'/cars/{cars[0].id}')

    assert response.status_code == 204
    result = await db.execute(query)
    assert len(result.fetchall()) == 1


async def test_delete_car_not_found(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    await create_car(db, cars[0])
    await create_test_image(cars[0].car_number)

    response = await client.delete(f'/cars/{cars[0].id}1')

    assert response.status_code == 404
    assert response.json() == {'detail': 'Car not found'}


async def test_retrieve_car(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    await create_car(db, cars[0])

    response = await client.get(f'/cars/{cars[0].id}')

    assert response.status_code == 200
    assert response.json() == cars[0].model_dump()


async def test_retrieve_car_not_found(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    await create_car(db, cars[0])

    response = await client.get(f'/cars/{cars[0].id}1')

    assert response.status_code == 404
    assert response.json() == {'detail': 'Car not found'}


async def test_update_car(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    filename = 'test.jpg'
    await create_car(db, cars[0])

    data = {
        'file': (filename, open(settings.TEST_DIR + filename, 'rb'), 'image/jpeg'),
        'car': (None, json.dumps({'car_description': 'Bmw Updated', 'engine': '4.0L'}), 'application/json'),
    }
    response = await client.patch(f'/cars/{cars[0].id}', files=data)
    response_data = response.json()
    assert response.status_code == 200
    assert response_data['car_description'] == 'Bmw Updated'
    assert response_data['engine'] == '4.0L'
    assert response_data['year'] == cars[0].year


async def test_update_car_not_found(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    await create_car(db, cars[0])
    data = {
        'car': (None, json.dumps({'car_description': 'Bmw Updated', 'engine': '4.0L'}), 'application/json'),
    }

    response = await client.patch(f'/cars/{cars[0].id}1', files=data)

    assert response.status_code == 404
    assert response.json() == {'detail': 'Car not found'}
