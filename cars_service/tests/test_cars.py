from io import BytesIO
from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import CarReadFactory, create_test_image

from app.cars.schemas import CarOut
from tests.entity_creators import create_car
from app.models import Car


async def test_create_car(client: AsyncClient, cars_factory: CarReadFactory, db: AsyncSession):
    filename = 'test.jpg'
    car = cars_factory.build()
    file_content = b'This is the content of the file.'
    file_obj = BytesIO(file_content)

    with patch('app.cars.router.is_car_station_exists') as is_car_station_exists_mock:
        is_car_station_exists_mock.return_value = True
        files = {'file': (filename, file_obj, 'image/jpeg')}
        response = await client.post('/cars/',  data=car.dict(exclude={'id', 'image'}), files=files)

    assert response.status_code == 201
    assert response.json() == car.dict(exclude={'id', 'image'})
    is_car_station_exists_mock.assert_called()


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

    with patch('app.cars.router.is_car_station_exists') as is_car_station_exists_mock:
        is_car_station_exists_mock.return_value = True
        file_content = b'This is the content of the file.'
        file_obj = BytesIO(file_content)

        response = await client.patch(
            f'/cars/{cars[0].id}',
            data={'car_description': 'Bmw Updated', 'engine': '4.0L', 'car_station_id': 1},
            files={'file': (filename, file_obj, 'image/jpeg')},
        )

    response_data = response.json()
    assert response.status_code == 200
    assert response_data['car_description'] == 'Bmw Updated'
    assert response_data['engine'] == '4.0L'
    assert response_data['year'] == cars[0].year
    is_car_station_exists_mock.assert_called()


async def test_update_car_not_found(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    await create_car(db, cars[0])

    response = await client.patch(f'/cars/{cars[0].id}1', data={'car_description': 'Bmw Updated', 'engine': '4.0L'})

    assert response.status_code == 404
    assert response.json() == {'detail': 'Car not found'}


async def test_get_cars_by_transmission(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    cars[1].transmission = 'mechanical'
    cars[0].transmission = 'automatic'
    await create_car(db, cars[0])
    await create_car(db, cars[1])

    response = await client.get('/cars/', params={'transmission': 'mechanical'})

    assert response.status_code == 200
    assert response.json() == [cars[1].model_dump()]


async def test_get_cars_by_rental_cost(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    cars[1].rental_cost = 5
    cars[0].rental_cost = 10
    await create_car(db, cars[0])
    await create_car(db, cars[1])

    response = await client.get('/cars/', params={'rental_cost_start': 5, 'rental_cost_end': 9})

    assert response.status_code == 200
    assert response.json() == [cars[1].model_dump()]


async def test_get_cars_by_ids(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    car_1 = await create_car(db, cars[0])
    await create_car(db, cars[1])

    response = await client.get('/cars/', params={'car_ids': [car_1.id]})

    assert response.status_code == 200
    assert response.json() == [cars[0].model_dump()]


async def test_get_cars_by_mult_params(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    cars[0].status = 'active'
    cars[0].engine = '3.5L'
    cars[1].engine = '3.5L'
    cars[1].status = 'active'
    await create_car(db, cars[0])
    await create_car(db, cars[1])

    response = await client.get('/cars/', params={'status': 'active', 'engine': '3.5L'})

    assert response.status_code == 200
    assert response.json() == [cars[1].model_dump(), cars[0].model_dump()]


async def test_update_car_status(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    cars[0].status = 'active'
    cars[1].status = 'active'
    car1_db = await create_car(db, cars[0])
    car2_db = await create_car(db, cars[1])

    response = await client.patch(
        '/cars/car-status/',
        params={'car_ids': [car1_db.id, car2_db.id]},
        json={'status': 'busy'},
    )

    assert response.status_code == 200
    assert response.json()[0]['status'] == 'busy'
    assert response.json()[1]['status'] == 'busy'


async def test_update_car_status_car_not_found(client: AsyncClient, cars: tuple[CarOut], db: AsyncSession):
    cars[0].status = 'active'
    cars[1].status = 'active'
    car1_db = await create_car(db, cars[0])
    await create_car(db, cars[1])

    response = await client.patch(
        '/cars/car-status/',
        params={'car_ids': [car1_db.id, -2]},
        json={'status': 'busy'},
    )

    assert response.status_code == 404
    assert response.json() == {'detail': 'Car not found'}
