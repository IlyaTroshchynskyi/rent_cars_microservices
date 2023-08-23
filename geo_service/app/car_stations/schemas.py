import re

from pydantic import BaseModel, Field, field_validator, ConfigDict


class CarStationOut(BaseModel):
    name: str
    address: str
    working_hours: str
    latitude: float
    longitude: float
    city: str

    model_config = ConfigDict(populate_by_name=True)


class CarStationIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    address: str = Field(min_length=1, max_length=128)
    working_hours: str = Field(min_length=1, max_length=32)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    city: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('working_hours')
    def validate_format(cls, value):
        return _validate_format(value)


class CarStationUpdate(BaseModel):
    address: str | None = Field(min_length=1, max_length=128, default=None)
    working_hours: str | None = Field(min_length=1, max_length=32, default=None)
    latitude: float | None = Field(ge=-90, le=90, default=None)
    longitude: float | None = Field(ge=-180, le=180, default=None)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('working_hours')
    def validate_format(cls, value):
        return _validate_format(value)


def _validate_format(value):
    pattern = r'^\d{2}:\d{2}-\d{2}:\d{2}$'

    if re.match(pattern, value):
        return value
    raise ValueError('Must be such format H:M-H:M')
