from fastapi import APIRouter, HTTPException, Response

from app.car_stations.schemas import CarStationIn, CarStationOut, CarStationUpdate
from app.custom_exceptions import NotFoundError
from app.service.car_station import (
    get_car_stations,
    create_car_station,
    retrieve_car_station,
    delete_car_station,
    update_car_station,
)
from app.redis_client import db_dependency


router = APIRouter(prefix='/car-station', tags=['Car Station'])


@router.get('/', response_model=list[CarStationOut])
async def get(db: db_dependency):
    return await get_car_stations(db)


@router.post('/', response_model=CarStationOut, status_code=201)
async def create(station: CarStationIn, db: db_dependency):
    return await create_car_station(db, station)


@router.delete('/{car_station_id}', response_class=Response, status_code=204)
async def delete(car_station_id: str, db: db_dependency):
    try:
        await delete_car_station(db, car_station_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail='Car station not found')


@router.get('/{car_station_id}', response_model=CarStationOut)
async def retrieve(car_station_id: str, db: db_dependency):
    try:
        return await retrieve_car_station(db, car_station_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail='Car station not found')


@router.patch('/{car_station_id}', response_model=CarStationOut)
async def update(station: CarStationUpdate, car_station_id: str, db: db_dependency):
    try:
        return await update_car_station(db, car_station_id, station)
    except NotFoundError:
        raise HTTPException(status_code=404, detail='Car station not found')
