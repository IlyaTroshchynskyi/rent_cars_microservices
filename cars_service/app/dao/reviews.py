from typing import Sequence

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.custom_exceptions import NotFoundError, SubReviewExistError
from app.models import Review
from app.reviews.schemas import ReviewIn, ReviewUpdate


async def get_reviews(db: AsyncSession) -> Sequence[Review]:
    query = select(Review).options(joinedload(Review.sub_reviews)).order_by(Review.id)
    result = await db.execute(query)
    return result.scalars().unique().all()


async def create_review(db: AsyncSession, item: ReviewIn) -> Review:
    query = insert(Review).values(**item.model_dump(exclude_unset=True)).returning(Review)
    result = await db.execute(query)
    review = result.scalar()
    await db.commit()
    return await _retrieve_review(db, review.id)


async def delete_review_by_id(db: AsyncSession, review_id: int):
    review = await _retrieve_review(db, review_id)
    if review.sub_reviews:
        raise SubReviewExistError

    query = delete(Review).where(Review.id == review_id)
    await db.execute(query)
    await db.commit()


async def _retrieve_review(db: AsyncSession, review_id: int) -> Review:
    query = select(Review).options(joinedload(Review.sub_reviews)).where(Review.id == review_id)
    result = await db.execute(query)
    review = result.scalar()
    if review:
        return review

    raise NotFoundError


async def update_review_by_id(db: AsyncSession, review_id: int, review_data: ReviewUpdate) -> Review:
    query = (
        update(Review).where(Review.id == review_id)
        .values(**review_data.model_dump(exclude_unset=True))
        .returning(Review)
    )
    result = await db.execute(query)
    review = result.scalar()
    if review is None:
        raise NotFoundError

    await db.commit()
    return await _retrieve_review(db, review.id)
