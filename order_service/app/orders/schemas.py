from datetime import datetime, timedelta
from enum import auto, StrEnum

from beanie import PydanticObjectId
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field, model_validator


OrderDictSerialized = dict


class OrderStatusEnum(StrEnum):
    RESERVATION = auto()
    PAID = auto()


def _replace_timezone(value: datetime):
    """
    Update value from 2023-08-19T13:50:09.696000Z to 2023-08-19T13:50:09.696000
    """
    return value.replace(tzinfo=None)


class CarOut(BaseModel):
    id: int
    car_description: str
    car_number: str
    transmission: str
    engine: str
    year: int
    status: str
    image: str
    rental_cost: int
    car_station_id: int


class BaseOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, json_encoders={datetime: _replace_timezone})

    def serializable_dict(self, **kwargs) -> OrderDictSerialized:
        default_dict = super().model_dump(**kwargs)
        return jsonable_encoder(default_dict)


class OrderOut(BaseOrder):
    id: PydanticObjectId = Field(alias='_id')
    rental_date_start: datetime
    rental_date_end: datetime
    rental_time: int
    total_cost: float
    prepayment: int
    status: OrderStatusEnum
    manager_id: int | None = None
    owner_id: int
    order_cars: list[int]


class OrderCarOut(OrderOut):
    order_cars: list[CarOut]


class BaseOrderIn(BaseOrder):
    rental_date_start: datetime
    rental_date_end: datetime
    prepayment: int = Field(ge=0, le=10_000)
    status: OrderStatusEnum
    owner_id: int

    @model_validator(mode='after')
    @classmethod
    def validate_date_rental_dates(cls, values):
        return _check_date_rental_dates(values)


class OrderCreate(BaseOrderIn):
    order_cars: list[int]


class OrderCreateReturn(BaseOrderIn):
    rental_time: int
    total_cost: float
    order_cars: list[int]


class OrderUpdate(BaseOrder):
    rental_date_start: datetime | None = None
    rental_date_end: datetime | None = None
    prepayment: int | None = Field(ge=0, le=10_000, default=None)
    status: OrderStatusEnum | None = None
    order_cars: list[int] | None = None

    @model_validator(mode='after')
    @classmethod
    def validate_date_rental_dates(cls, values):
        return _check_date_rental_dates(values)


def _check_date_rental_dates(values):
    if values.order_cars and (not values.rental_date_start or not values.rental_date_end):
        raise ValueError('When you specify list cars you should specify and rental date')

    if not (values.rental_date_start and values.rental_date_end):
        return values

    if values.rental_date_start > values.rental_date_end:
        raise ValueError('Rental date start can not be higher than Rental date end')

    # need replace because TypeError: can't compare offset-naive and offset-aware datetimes
    if values.rental_date_start.replace(tzinfo=None) < datetime.now():
        raise ValueError('Rental date start can not be less than today')

    diff: timedelta = values.rental_date_end - values.rental_date_start
    if diff.days < 1 or diff.days > 30:
        raise ValueError('Rent period must be between 1 and 30 days')
    return values
