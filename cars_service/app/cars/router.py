from typing import Annotated

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi import Response

from app.cars.schemas import CarIn, CarOut, CarUpdate, CarFiltering, CarUpdateStatus
from app.common.dependency import db_dependency
from app.custom_exceptions import NotFoundError
from app.dao.car import (
    create_car,
    delete_car_by_id,
    get_cars,
    is_car_station_exists,
    retrieve_car_by_id,
    update_car_by_id,
    update_cars_status,
)

router = APIRouter(prefix='/cars', tags=['Cars'])


@router.get('/', response_model=list[CarOut])
async def get_all_cars(db: db_dependency, query_param: Annotated[CarFiltering, Depends()]):
    return await get_cars(db, query_param)


@router.post('/', response_model=CarIn, status_code=201)
async def create_new_car(file: UploadFile, db: db_dependency, car: CarIn = Depends(CarIn.as_form)):
    if not await is_car_station_exists(car.car_station_id):
        raise HTTPException(status_code=404, detail='Car station not found')

    car = await create_car(db, car, file)
    return car


@router.delete('/{car_id}', response_class=Response, status_code=204)
async def delete(car_id: int, db: db_dependency):
    try:
        await delete_car_by_id(db, car_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail='Car not found')


@router.get('/{car_id}', response_model=CarOut)
async def retrieve_car(car_id: int, db: db_dependency):
    try:
        return await retrieve_car_by_id(db, car_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail='Car not found')


@router.patch('/{car_id}', response_model=CarUpdate)
async def update_car(
        car_id: int,
        db: db_dependency,
        car: CarUpdate | None = Depends(CarUpdate.as_form),
        file: UploadFile = File(None),
):
    if car.car_station_id and not await is_car_station_exists(car.car_station_id):
        raise HTTPException(status_code=404, detail='Car station not found')

    try:
        return await update_car_by_id(db, car_id, car, file)
    except NotFoundError:
        raise HTTPException(status_code=404, detail='Car not found')


@router.patch('/car-status/',  response_model=list[CarUpdate])
async def update_car_status_by_mult_criteria(
        db: db_dependency,
        car: CarUpdateStatus,
        car_ids: Annotated[list[int], Query()],
):
    try:
        return await update_cars_status(db, car, car_ids)
    except NotFoundError:
        raise HTTPException(status_code=404, detail='Car not found')
