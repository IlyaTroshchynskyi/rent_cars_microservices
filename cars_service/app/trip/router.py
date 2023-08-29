from fastapi import APIRouter, BackgroundTasks

from app.rabbit_connection import rabbit_dependency
from app.trip.tasks import start_trip


router = APIRouter(prefix='/trip', tags=['Trip'])


@router.post('/')
async def start_new_trip(car_number: str, task: BackgroundTasks,  rabbit_pool: rabbit_dependency):
    task.add_task(start_trip, car_number, rabbit_pool)
    return {'message': f'Start trip for car {car_number}'}
