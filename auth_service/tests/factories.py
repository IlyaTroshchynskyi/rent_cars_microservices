import random
import uuid

from faker import Faker
from pydantic import BaseModel, Field

from app.users.schemas import RoleEnum

fake = Faker()


class TestUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_name: str = Field(default_factory=fake.name)
    first_name: str = Field(default_factory=fake.first_name)
    last_name: str = Field(default_factory=fake.last_name)
    phone: str = Field(default_factory=lambda: random.choice(['+380661122333', '+380661122334']))
    passport: str = Field(default=random.choice(['AM1234', 'AX2345']))
    password: str = Field(default_factory=fake.password)
    role: RoleEnum = RoleEnum.CUSTOMER
    order_ids: list[str] = ['1', '2']
