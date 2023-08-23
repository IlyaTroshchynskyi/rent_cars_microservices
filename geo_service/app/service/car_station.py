import json
import uuid

from redis.asyncio import Redis

from app.car_stations.schemas import CarStationUpdate, CarStationIn, CarStationOut
from app.custom_exceptions import NotFoundError


async def get_car_stations(db: Redis) -> list[CarStationOut]:
    car_stations = await db.mget(await db.keys('*'))
    return [CarStationOut.model_validate_json(car_station) for car_station in car_stations]


async def create_car_station(db: Redis, item: CarStationIn) -> CarStationIn:
    _id = str(uuid.uuid4())
    await db.set(_id, item.model_dump_json())
    car_station = await db.get(_id)
    return CarStationIn.model_validate_json(car_station)


async def delete_car_station(db: Redis, station_id: str):
    if not await db.delete(station_id):
        raise NotFoundError


async def retrieve_car_station(db: Redis, station_id: str) -> CarStationOut:
    car_station_str = await db.get(station_id)
    if car_station_str:
        return CarStationOut.model_validate_json(car_station_str)
    raise NotFoundError


async def update_car_station(db: Redis, station_id: str, car_station_data: CarStationUpdate) -> CarStationOut:
    car_station = await retrieve_car_station(db, station_id)

    dict_car_station = car_station.model_dump()
    dict_car_station.update(car_station_data.model_dump(exclude_unset=True))

    await db.set(station_id, json.dumps(dict_car_station))
    car_station_updated = await retrieve_car_station(db, station_id)
    return car_station_updated
