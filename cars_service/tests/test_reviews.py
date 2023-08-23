from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.cars.schemas import CarOut
from app.reviews.schemas import ReviewIn
from tests.conftest import CarReadFactory, ReviewInFactory

from tests.entity_creators import prepare_reviews, create_car


async def test_create_review(
        client: AsyncClient,
        review_factory: ReviewInFactory,
        db: AsyncSession,
        cars_factory: CarReadFactory,
):
    review_1 = review_factory.build()
    car = await create_car(db, cars_factory.build())
    review_input = review_1.model_dump(exclude={'car_id', 'parent_id'}) | {'car_id': car.id}

    response = await client.post('/reviews/', json=review_input)
    response_data = response.json()

    assert response.status_code == 201
    assert response_data['stars'] == review_1.stars
    assert response_data['car_id'] == car.id
    assert response_data['comment'] == review_1.comment


async def test_get_reviews(client: AsyncClient, reviews: tuple[ReviewIn], db: AsyncSession, cars: tuple[CarOut]):
    review_db_1, review_db_2 = await prepare_reviews(db, reviews, cars)

    response = await client.get('/reviews/')

    assert response.status_code == 200
    response_data = response.json()
    assert response_data[0]['comment'] == reviews[0].comment
    assert response_data[0]['stars'] == reviews[0].stars
    assert response_data[0]['car_id'] == review_db_1.car_id
    assert response_data[0]['parent_id'] is None

    sub_review = response_data[0]['sub_reviews'][0]
    assert sub_review['comment'] == review_db_2.comment
    assert sub_review['stars'] == review_db_2.stars
    assert sub_review['car_id'] == review_db_2.car_id
    assert sub_review['parent_id'] == review_db_2.parent_id


async def test_delete_reviews(client: AsyncClient, reviews: tuple[ReviewIn], db: AsyncSession, cars: tuple[CarOut]):
    review_db_1, review_db_2 = await prepare_reviews(db, reviews, cars)

    response = await client.delete(f'/reviews/{review_db_2.id}')

    assert response.status_code == 204


async def test_delete_reviews_not_found(
        client: AsyncClient,
        reviews: tuple[ReviewIn],
        db: AsyncSession,
        cars: tuple[CarOut],
):
    review_db_1, review_db_2 = await prepare_reviews(db, reviews, cars)

    response = await client.delete(f'/reviews/{review_db_1.id}1')

    assert response.status_code == 404
    assert response.json() == {'detail': 'Review not found'}


async def test_delete_reviews_with_sub_reviews(
        client: AsyncClient,
        reviews: tuple[ReviewIn],
        db: AsyncSession,
        cars: tuple[CarOut],
):
    review_db_1, review_db_2 = await prepare_reviews(db, reviews, cars)

    response = await client.delete(f'/reviews/{review_db_1.id}')

    assert response.status_code == 400
    assert response.json() == {'detail': 'You can not delete review with sub reviews'}


async def test_update_review(client: AsyncClient, reviews: tuple[ReviewIn], db: AsyncSession, cars: tuple[CarOut]):
    review_db_1, review_db_2 = await prepare_reviews(db, reviews, cars)

    response = await client.patch(f'/reviews/{review_db_2.id}', json={'stars': 1})

    assert response.status_code == 200
    assert response.json()['stars'] == 1


async def test_update_review_not_found(
        client: AsyncClient,
        reviews: tuple[ReviewIn],
        db: AsyncSession,
        cars: tuple[CarOut],
):
    review_db_1, review_db_2 = await prepare_reviews(db, reviews, cars)

    response = await client.patch(f'/reviews/{review_db_1.id}1', json={'stars': 1})

    assert response.status_code == 404
    assert response.json() == {'detail': 'Review not found'}
