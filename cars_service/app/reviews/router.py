from fastapi import APIRouter, HTTPException, Response

from app.common.dependency import db_dependency
from app.custom_exceptions import SubReviewExistError, NotFoundError
from app.dao.reviews import create_review, delete_review_by_id, get_reviews, update_review_by_id
from app.reviews.schemas import ReviewOut, ReviewIn, ReviewUpdate


router = APIRouter(prefix='/reviews', tags=['Review'])


@router.get('/', response_model=list[ReviewOut])
async def get_all_reviews(db: db_dependency):
    return await get_reviews(db)


@router.post('/', response_model=ReviewOut, status_code=201)
async def create_new_review(review: ReviewIn, db: db_dependency):
    result = await create_review(db, review)
    return result


@router.delete('/{review_id}', response_class=Response, status_code=204)
async def delete_review(review_id: int, db: db_dependency):
    try:
        await delete_review_by_id(db, review_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail='Review not found')
    except SubReviewExistError:
        raise HTTPException(status_code=400, detail='You can not delete review with sub reviews')


@router.patch('/{review_id}', response_model=ReviewOut)
async def update_review(review_id: int, review: ReviewUpdate, db: db_dependency):
    try:
        return await update_review_by_id(db, review_id, review)
    except NotFoundError:
        raise HTTPException(status_code=404, detail='Review not found')
