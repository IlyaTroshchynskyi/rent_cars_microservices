import json
from dataclasses import dataclass

from datetime import date
from enum import auto, StrEnum
import re
from typing import Annotated

from fastapi import Query, Form
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

    @classmethod
    def as_form(
            cls,
            car_description: str = Form(),
            car_number: str = Form(),
            transmission: CarTransmissionEnum = Form(),
            engine: str = Form(),
            year: int = Form(),
            status: CarStatusEnum = Form(),
            rental_cost: int = Form(),
            car_station_id: int = Form()

    ):
        return cls(
            car_description=car_description, car_number=car_number, transmission=transmission, engine=engine,
            year=year, status=status, rental_cost=rental_cost, car_station_id=car_station_id
        )


class CarUpdate(CarBaseModel):
    car_description: str | None = Field(min_length=1, max_length=32, default=None)
    transmission: CarTransmissionEnum | None = None
    engine: str | None = Field(min_length=1, max_length=16, default=None)
    year: int | None = Field(ge=2000, le=date.today().year, default=None)
    status: CarStatusEnum | None = None
    rental_cost: int | None = Field(ge=0, le=5000, default=None)
    car_station_id: int | None = None

    @classmethod
    def as_form(
            cls,
            car_description: str | None = Form(default=None),
            transmission: CarTransmissionEnum | None = Form(default=None),
            engine: str | None = Form(default=None),
            year: int | None = Form(default=None),
            status: CarStatusEnum | None = Form(default=None),
            rental_cost: int | None = Form(default=None),
            car_station_id: int | None = Form(default=None),

    ):
        return cls(
            car_description=car_description, transmission=transmission, engine=engine,
            year=year, status=status, rental_cost=rental_cost, car_station_id=car_station_id
        )


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


@dataclass
class CarFiltering:
    car_ids: Annotated[list[int], Query()] = None
    engine: str | None = None
    year_start: int | None = None
    year_end: int | None = None
    transmission: CarTransmissionEnum | None = None
    car_number: str | None = None
    status: CarStatusEnum | None = None
    rental_cost_start: int | None = None
    rental_cost_end: int | None = None


class CarUpdateStatus(BaseModel):
    status: CarStatusEnum

    model_config = ConfigDict(from_attributes=True)
