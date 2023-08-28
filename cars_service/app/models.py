from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import backref, DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CommonFieldsMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Car(Base, CommonFieldsMixin):
    __tablename__ = 'cars'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    car_description: Mapped[str] = mapped_column(String(32), nullable=False)
    car_number: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    transmission: Mapped[str] = mapped_column(String(16), nullable=False)
    engine: Mapped[str] = mapped_column(String(16), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM('active', 'broken', 'repairing', 'busy', name='status_car'),
        nullable=False,
    )
    image: Mapped[str] = mapped_column(String(64), nullable=True)
    rental_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    car_station_id: Mapped[int] = mapped_column(Integer, nullable=True)

    def __str__(self):
        return f'{self.car_description} - {self.car_number}'


class Review(Base, CommonFieldsMixin):
    # https://docs.sqlalchemy.org/en/20/orm/join_conditions.html#handling-multiple-join-pathsselfjoin
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment: Mapped[str] = mapped_column(Text)
    stars: Mapped[int] = mapped_column(Integer)
    car_id: Mapped[int] = mapped_column(Integer, ForeignKey('cars.id', ondelete='CASCADE'))
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey('reviews.id'), nullable=True)
    sub_reviews: Mapped[list['Review']] = relationship('Review', backref=backref('parent', remote_side='Review.id'))

    def __str__(self):
        return f'{self.comment} - {self.stars}'
