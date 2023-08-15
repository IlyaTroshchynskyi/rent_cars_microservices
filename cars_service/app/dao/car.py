from typing import Sequence

import aiofiles
import aiofiles.os as aio_os
from fastapi import UploadFile
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cars import schemas
from app.config import settings
from app.models import Car


async def get_cars(db: AsyncSession) -> Sequence[Car]:
    query = select(Car).order_by(Car.id)
    result = await db.execute(query)
    return result.scalars().all()


async def create_car(db: AsyncSession, car: schemas.CarCreate, file: UploadFile) -> Car:
    file_name = car.car_number.replace(' ', '') + '.jpg'
    await write_car_image(settings.STATIC_DIR + file_name, file)

    query = insert(Car).values(**car.dict(), image=settings.STATIC_URL + file_name).returning(Car)
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


async def delete_car(db: AsyncSession, car_id: int) -> Car:
    query = delete(Car).where(Car.id == car_id).returning(Car)
    car = await db.execute(query)
    await db.commit()
    return car.scalar()


async def retrieve_car(db: AsyncSession, car_id: int) -> Car:
    query = select(Car).where(Car.id == car_id)
    result = await db.execute(query)
    return result.scalar()


async def update_car(db: AsyncSession, car_id: int, data: schemas.CarUpdate | dict) -> Car:
    query = update(Car).where(Car.id == car_id).values(**data.dict(exclude_unset=True)).returning(Car)
    result = await db.execute(query)
    await db.commit()
    return result.scalar()


async def is_car_station_exists(car_station_id: int) -> bool:
    return True
