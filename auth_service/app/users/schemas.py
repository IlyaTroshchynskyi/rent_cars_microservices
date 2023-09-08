from enum import auto, StrEnum
import re

from pydantic import BaseModel, Field, field_validator


class RoleEnum(StrEnum):
    EMPLOYEE = auto()
    CUSTOMER = auto()


class UserBaseModel(BaseModel):
    @field_validator('phone', check_fields=False)
    def validate_phone(cls, phone: str):
        return _validate_phone(phone)

    @field_validator('passport', check_fields=False)
    def validate_passport(cls, passport: str):
        return _validate_passport(passport)


class UserIn(UserBaseModel):
    user_name: str = Field(min_length=1, max_length=32)
    first_name: str = Field(min_length=1, max_length=32)
    last_name: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=32)
    phone: str
    passport: str
    role: RoleEnum = RoleEnum.CUSTOMER


class UserOut(BaseModel):
    id: str
    user_name: str
    first_name: str
    last_name: str
    phone: str
    passport: str
    role: RoleEnum
    order_ids: list[str] | None = []


class UserUpdate(UserBaseModel):
    user_name: str | None = Field(min_length=1, max_length=32, default=None)
    first_name: str | None = Field(min_length=1, max_length=32, default=None)
    last_name: str | None = Field(min_length=1, max_length=32, default=None)
    phone: str | None = None
    passport: str | None = None
    role: RoleEnum | None = None
    order_ids: list[str] | None = None


def _validate_phone(phone: str):
    pattern = r'^\+380[0-9]{9}$'
    if not bool(re.match(pattern, phone)):
        raise ValueError('Format for phone should be like +380XXXXXXXXX')
    return phone


def _validate_passport(passport: str):
    pattern = r'^(\d{5})|([A-Z]{2}\d{4})$'
    if not bool(re.match(pattern, passport)):
        raise ValueError('Format for passport  should be 5 digits or two big letter with 6 digits')
    return passport


class UserUpdateParams(BaseModel):
    set_expression: str
    attribute_values: dict
    attribute_names: dict
