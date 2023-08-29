from pydantic import BaseModel


class CoordinateMessage(BaseModel):
    car_number: str
    latitude: float
    longitude: float
