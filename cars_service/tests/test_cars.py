from httpx import AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import CarReadFactory, create_test_image

from app.cars.schemas import CarRead
from app.config import settings
from app.models import Car


async def create_car(db, car):
    query = insert(Car).values(**car.dict()).returning(Car)
    await db.execute(query)


async def test_create_car(client: AsyncClient, cars_factory: CarReadFactory, db: AsyncSession):
    filename = 'test.jpg'
    car = cars_factory.build()

    response = await client.post(
        '/cars/',
        params=car.dict(exclude={'id', 'image'}),
        files={'file': (filename, open(settings.TEST_DIR + filename, 'rb'), filename)},
    )

    assert response.status_code == 201
    assert response.json() == car.dict(exclude={'id', 'image'})


async def test_get_cars(client: AsyncClient, cars: tuple[CarRead], db: AsyncSession):
    await create_car(db, cars[0])
    await create_car(db, cars[1])

    response = await client.get('/cars/')

    assert response.status_code == 200
    assert response.json() == [car.dict() for car in sorted(cars, key=lambda x: x.id)]


async def test_delete_car(client: AsyncClient, cars: tuple[CarRead], db: AsyncSession):
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


async def test_retrieve_car(client: AsyncClient, cars: tuple[CarRead], db: AsyncSession):
    await create_car(db, cars[0])

    response = await client.get(f'/cars/{cars[0].id}')

    assert response.status_code == 200
    assert response.json() == cars[0].dict()


async def test_update_car(client: AsyncClient, cars: tuple[CarRead], db: AsyncSession):
    await create_car(db, cars[0])

    response = await client.patch(f'/cars/{cars[0].id}', json={'car_description': 'Bmw Updated', 'engine': '4.0L'})

    response_data = response.json()
    assert response.status_code == 200
    assert response_data['car_description'] == 'Bmw Updated'
    assert response_data['engine'] == '4.0L'
    assert response_data['year'] == cars[0].year


async def test_update_car_image(client: AsyncClient, cars: tuple[CarRead], db: AsyncSession):
    await create_car(db, cars[0])
    filename = 'test.jpg'

    response = await client.patch(
        f'/cars/update_image/{cars[0].id}',
        files={'file': (filename, open(settings.TEST_DIR + filename, 'rb'), filename)},
    )

    assert response.status_code == 200
