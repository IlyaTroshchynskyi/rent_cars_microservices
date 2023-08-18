from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi import Response

from app.cars.schemas import CarCreate, CarRead, CarUpdate
from app.common.dependency import db_dependency
from app.config import settings
from app.dao.car import (
    create_car,
    delete_car,
    delete_car_image,
    get_cars,
    is_car_station_exists,
    retrieve_car,
    update_car,
    write_car_image,
)

router = APIRouter(prefix='/cars', tags=['Cars'])


@router.get('/', response_model=list[CarRead])
async def get(db: db_dependency):
    return await get_cars(db)


@router.post('/', response_model=CarCreate, status_code=201)
async def create(file: UploadFile, db: db_dependency, car: CarCreate = Depends()):
    if not car.car_station_id or not await is_car_station_exists(car.car_station_id):
        raise HTTPException(status_code=404, detail='Car station not found')

    car = await create_car(db, car, file)
    return car


@router.delete('/{car_id}', response_class=Response, status_code=204)
async def delete(car_id: int, db: db_dependency):
    car = await delete_car(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail='Car not found')
    filename = car.car_number + '.jpg'
    await delete_car_image(settings.STATIC_DIR + filename)


@router.get('/{car_id}', response_model=CarRead)
async def retrieve(car_id: int, db: db_dependency):
    if car := await retrieve_car(db, car_id):
        return car
    raise HTTPException(status_code=404, detail='Car not found')


@router.patch('/{car_id}', response_model=CarUpdate)
async def update(car_id: int, car: CarUpdate, db: db_dependency):
    if car.car_station_id and not await is_car_station_exists(car.car_station_id):
        raise HTTPException(status_code=404, detail='Car station not found')
    if car := await update_car(db, car_id, car):
        return car
    raise HTTPException(status_code=404, detail='Car not found')


@router.patch('/update_image/{car_id}', response_model=CarRead)
async def update_image(car_id: int, file: UploadFile, db: db_dependency):
    if car := await retrieve_car(db, car_id):
        await write_car_image(settings.STATIC_DIR + car.car_number.replace(' ', '') + '.jpg', file)
        return car
    raise HTTPException(status_code=404, detail='Car not found')
