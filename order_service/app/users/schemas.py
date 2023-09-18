from enum import auto, StrEnum

from pydantic import BaseModel


class RoleEnum(StrEnum):
    EMPLOYEE = auto()
    CUSTOMER = auto()


class UserOut(BaseModel):
    id: str
    user_name: str
    first_name: str
    last_name: str
    phone: str
    passport: str
    role: RoleEnum
    order_ids: list[str] | None = []
