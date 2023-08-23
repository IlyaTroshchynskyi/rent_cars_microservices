import json
from datetime import date
from enum import auto, StrEnum
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CarStatusEnum(StrEnum):
    ACTIVE = auto()
    BROKEN = auto()
    REPAIRING = auto()
    BUSY = auto()


class CarTransmissionEnum(StrEnum):
    MECHANICAL = auto()
    AUTOMATIC = auto()


class CarBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator('car_number', check_fields=False)
    def validate_car_number(cls, value):
        return _validate_car_number(value)

    @field_validator('engine', check_fields=False)
    def validate_engine(cls, value):
        return _validate_engine(value)

    @model_validator(mode='before')
    @classmethod
    def to_py_dict(cls, data: str | dict):
        return json.loads(data) if isinstance(data, str) else data


class CarOut(BaseModel):
    id: int
    car_description: str
    car_number: str
    transmission: CarTransmissionEnum
    engine: str
    year: int
    status: CarStatusEnum
    image: str
    rental_cost: int
    car_station_id: int

    model_config = ConfigDict(from_attributes=True)


class CarIn(CarBaseModel):
    car_description: str = Field(min_length=1, max_length=32)
    car_number: str = Field(min_length=1, max_length=16)
    transmission: CarTransmissionEnum = CarTransmissionEnum.AUTOMATIC
    engine: str = Field(min_length=1, max_length=16)
    year: int = Field(ge=2000, le=date.today().year)
    status: CarStatusEnum = CarStatusEnum.ACTIVE
    rental_cost: int = Field(ge=0, le=5000)
    car_station_id: int


class CarUpdate(CarBaseModel):
    car_description: str | None = Field(min_length=1, max_length=32, default=None)
    transmission: CarTransmissionEnum | None = None
    engine: str | None = Field(min_length=1, max_length=16, default=None)
    year: int | None = Field(ge=2000, le=date.today().year, default=None)
    status: CarStatusEnum | None = None
    rental_cost: int | None = Field(ge=0, le=5000, default=None)
    car_station_id: int | None = None


def _validate_car_number(value):
    pattern = r'^[A-Z]{2}\d{4}[A-Z]{2}$'
    if not bool(re.match(pattern, value)):
        raise ValueError('Format for car number should be AE2321AE')
    return value


def _validate_engine(value):
    pattern = r'^[1-6]{1}\.[0-9]{1}L$'
    if not bool(re.match(pattern, value)):
        raise ValueError('Format for engine should be like 1.9L')
    return value
