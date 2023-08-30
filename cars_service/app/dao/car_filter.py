from sqlalchemy import select

from app.cars.schemas import CarFiltering
from app.models import Car


class CarQueryBuilder:
    def __init__(self, params: CarFiltering):
        self.params = params
        self._query = None

    def build_query(self):
        self._query = select(Car)
        (
            self._with_car_ids()
            ._with_engine()
            ._with_year_end()
            ._with_year_start()
            ._with_transmission()
            ._with_rental_cost_start()
            ._with_rental_cost_end()
            ._with_car_number()
            ._with_status()
        )
        return self._query.order_by(Car.id)

    def _with_car_ids(self):
        if self.params.car_ids:
            self._query = self._query.where(Car.id.in_(self.params.car_ids))
        return self

    def _with_year_end(self):
        if self.params.year_end:
            self._query = self._query.where(Car.year <= self.params.year_end)
        return self

    def _with_year_start(self):
        if self.params.year_start:
            self._query = self._query.where(Car.year >= self.params.year_start)
        return self

    def _with_engine(self):
        if self.params.engine:
            self._query = self._query.where(Car.engine == self.params.engine)
        return self

    def _with_transmission(self):
        if self.params.transmission:
            self._query = self._query.where(Car.transmission == self.params.transmission)
        return self

    def _with_car_number(self):
        if self.params.car_number:
            self._query = self._query.where(Car.car_number == self.params.car_number)
        return self

    def _with_status(self):
        if self.params.status:
            self._query = self._query.where(Car.status == self.params.status)
        return self

    def _with_rental_cost_start(self):
        if self.params.rental_cost_start:
            self._query = self._query.where(Car.rental_cost >= self.params.rental_cost_start)
        return self

    def _with_rental_cost_end(self):
        if self.params.rental_cost_end:
            self._query = self._query.where(Car.rental_cost <= self.params.rental_cost_end)
        return self
