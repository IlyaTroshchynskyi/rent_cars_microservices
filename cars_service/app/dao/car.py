from typing import Sequence

import aiofiles
import aiofiles.os as aio_os
from fastapi import UploadFile
from httpx import AsyncClient
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cars.schemas import CarUpdate, CarIn, CarFiltering, CarUpdateStatus
from app.custom_exceptions import NotFoundError
from app.config import get_settings
from app.custom_metrics import update_count_car_in_state, execution_time
from app.dao.car_filter import CarQueryBuilder
from app.models import Car


async def get_cars(db: AsyncSession, params: CarFiltering) -> Sequence[Car]:
    query = CarQueryBuilder(params).build_query()
    result = await db.execute(query)
    return result.scalars().all()


@execution_time.time()
async def create_car(db: AsyncSession, car: CarIn, file: UploadFile) -> Car:
    file_name = car.car_number.replace(' ', '') + '.jpg'
    await write_car_image(get_settings().STATIC_DIR + file_name, file)

    query = insert(Car).values(**car.model_dump(), image=get_settings().STATIC_URL + file_name).returning(Car)
    result = await db.execute(query)
    result = result.scalar()
    await db.commit()
    return result


async def write_car_image(full_path: str, file: UploadFile):
    async with aiofiles.open(full_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)


async def delete_car_image(full_path: str):
    await aio_os.remove(full_path)


async def delete_car_by_id(db: AsyncSession, car_id: int) -> Car:
    query = delete(Car).where(Car.id == car_id).returning(Car)
    car = await db.execute(query)
    await db.commit()
    car = car.scalar()
    if car:
        filename = car.car_number + '.jpg'
        await delete_car_image(get_settings().STATIC_DIR + filename)
        return car
    raise NotFoundError


async def retrieve_car_by_id(db: AsyncSession, car_id: int) -> Car:
    query = select(Car).where(Car.id == car_id)
    result = await db.execute(query)
    car = result.scalar()
    if car:
        return car
    raise NotFoundError


async def update_car_by_id(db: AsyncSession, car_id: int, car: CarUpdate, file: UploadFile) -> Car:
    query = update(Car).where(Car.id == car_id).values(**car.model_dump(exclude_none=True)).returning(Car)
    result = await db.execute(query)
    await db.commit()
    db_car = result.scalar()
    update_count_car_in_state(car.status, 1)
    if db_car:
        if file:
            await write_car_image(get_settings().STATIC_DIR + db_car.car_number.replace(' ', '') + '.jpg', file)
        return db_car
    raise NotFoundError


async def update_cars_status(db: AsyncSession, car: CarUpdateStatus, car_ids: list[int]) -> list[Car]:
    # need to check if object exists in one transaction
    for _id in car_ids:
        await retrieve_car_by_id(db, _id)
    update_count_car_in_state(car.status, len(car_ids))

    query = update(Car).where(Car.id.in_(car_ids)).values(**car.model_dump()).returning(Car)
    result = await db.execute(query)
    await db.commit()
    return result.scalars()


async def is_car_station_exists(car_station_id: int) -> bool:
    async with AsyncClient() as client:
        response = await client.get(f'{get_settings().GEO_SERVICE_BASE_URL}{car_station_id}')

    if response.status_code == 200:
        return True
    return False
