from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.cars.schemas import CarOut
from app.models import Car, Review
from app.reviews.schemas import ReviewIn


async def create_car(db, car):
    query = insert(Car).values(**car.dict()).returning(Car)
    result = await db.execute(query)
    car = result.scalar()
    return car


async def create_review(db: AsyncSession, review) -> Review:
    query = insert(Review).values(**review.model_dump(exclude_unset=True)).returning(Review)
    result = await db.execute(query)
    review = result.scalar()
    return review


async def prepare_reviews(db, reviews: tuple[ReviewIn], cars: tuple[CarOut]) -> list[Review]:
    car = await create_car(db, cars[0])
    review_input_1 = reviews[0].model_dump(exclude={'parent_id'})
    review_input_1['car_id'] = car.id
    review_db_1 = await create_review(db, ReviewIn(**review_input_1))

    review_input_2 = reviews[1].model_dump()
    review_input_2['car_id'] = car.id
    review_input_2['parent_id'] = review_db_1.id
    review_db_2 = await create_review(db, ReviewIn(**review_input_2))
    return [review_db_1, review_db_2]
