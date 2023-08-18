from datetime import datetime
from enum import auto, StrEnum
import sys
from typing import Optional, TypeVar

from beanie import Document


class OrderStatusEnum(StrEnum):
    RESERVATION = auto()
    PAID = auto()


class Order(Document):
    rental_date_start: datetime
    rental_date_end: datetime
    rental_time: int
    total_cost: float
    prepayment: int
    status: OrderStatusEnum
    manager_id: Optional[int] = None
    owner_id: int
    order_cars: list[int]

    class Settings:
        name = 'orders'


ModelClasses = TypeVar('ModelClasses', bound=Document)


def gather_documents() -> list[ModelClasses]:
    """Returns a list of all MongoDB document models defined in `models` module."""
    from inspect import getmembers, isclass
    return [
        doc
        for _, doc in getmembers(sys.modules[__name__], isclass)
        if issubclass(doc, Document) and doc.__name__ != 'Document'
    ]
