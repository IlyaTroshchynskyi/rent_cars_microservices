from prometheus_client import Counter, Summary

from app.cars.schemas import CarStatusEnum


booked_car = Counter('number_booked_car', 'Number booked car', labelnames=('booked_car',))

active_car = Counter('number_active_car', 'Number active car', labelnames=('active_car',))

other_state_car = Counter('number_other_state_car', 'Number other state car', labelnames=('other_car',))

execution_time = Summary('car_create_processing_seconds', 'Time spent processing create car')


def update_count_car_in_state(status: CarStatusEnum, count: int):
    if not status:
        return
    if status == CarStatusEnum.ACTIVE:
        active_car.labels(status).inc(count)
    elif status == CarStatusEnum.BUSY:
        booked_car.labels(status).inc(count)
    else:
        other_state_car.labels('other').inc(count)
