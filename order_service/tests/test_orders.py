
from datetime import datetime, timedelta
from unittest.mock import patch

from httpx import AsyncClient
from pytest_httpx import HTTPXMock
from tests.conftest import CarReadFactory, OrderCreateFactory, UserOutFactory
from tests.factories import UserMockResponse

from app.custom_exceptions import CarServiceError
from app.models import Order
from app.orders.schemas import OrderDictSerialized


async def test_create_order(client: AsyncClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())
    order = OrderCreateFactory().build().serializable_dict()
    car = CarReadFactory().build()
    car.rental_cost = 25
    with (
        patch('app.dao.order.get_order_cars') as get_order_cars_mock,
        patch('app.dao.order.update_cars_status') as update_cars_status_mock,
    ):
        get_order_cars_mock.return_value = [car]

        response = await client.post('/orders/', json=order, headers={'auth-token': 'token'})

    result = response.json()
    rental_time = result.pop('rental_time')
    total_cost = result.pop('total_cost')
    customer_id = result.pop('customer_id')

    assert response.status_code == 201
    assert result == order
    assert rental_time == 3
    assert total_cost == 75
    assert isinstance(customer_id, str)
    get_order_cars_mock.assert_awaited_once()
    update_cars_status_mock.assert_awaited_once()


async def test_create_order_user_not_found(client: AsyncClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(**UserMockResponse(status_code=404).model_dump(), json={'detail': 'User not found'})

    order = OrderCreateFactory().build().serializable_dict()
    response = await client.post('/orders/', json=order, headers={'auth-token': 'token'})

    assert response.status_code == 404
    assert response.json() == {'detail': 'User not found'}


async def test_create_order_raise_car_not_found(client: AsyncClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())
    order = OrderCreateFactory().build().serializable_dict()

    with (
        patch('app.dao.order.get_order_cars') as get_order_cars_mock,
        patch('app.dao.order.update_cars_status') as update_cars_status_mock,
    ):
        update_cars_status_mock.side_effect = CarServiceError(404, 'One ore more cars not found')

        response = await client.post('/orders/', json=order, headers={'auth-token': 'token'})

    assert response.status_code == 404
    assert response.json() == {'detail': 'One ore more cars not found'}
    get_order_cars_mock.assert_awaited_once()
    update_cars_status_mock.assert_awaited_once()


async def test_create_order_not_found_car(client: AsyncClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())
    order = OrderCreateFactory().build().serializable_dict()

    with patch('app.dao.order.get_order_cars') as get_order_cars_mock:
        get_order_cars_mock.side_effect = CarServiceError(500, 'Internal Server Error')

        response = await client.post('/orders/', json=order, headers={'auth-token': 'token'})

    assert response.status_code == 500
    assert response.json() == {'detail': 'Internal Server Error'}


async def test_get_orders(client: AsyncClient, orders: list[OrderDictSerialized]):
    result = await client.get('/orders/')

    assert result.status_code == 200
    assert result.json() == orders


async def test_delete_order(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        **UserMockResponse().model_dump(),
        json=UserOutFactory.build().model_dump(exclude={'customer_id'}) | {'id': orders[0]['customer_id']},
    )
    assert await Order.find_all().count() == 2
    response = await client.delete(f'/orders/{orders[0]["_id"]}', headers={'auth-token': 'token'})

    assert response.status_code == 204
    assert await Order.find_all().count() == 1


async def test_delete_order_not_owner(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())
    assert await Order.find_all().count() == 2
    response = await client.delete(f'/orders/{orders[1]["_id"]}', headers={'auth-token': 'token'})

    assert response.status_code == 403
    assert response.json() == {'detail': 'User is not owner of order'}
    assert await Order.find_all().count() == 2


async def test_delete_order_not_found(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())
    response = await client.delete('/orders/64df90203d15b134f47e4a9f', headers={'auth-token': 'token'})

    assert response.status_code == 404
    assert response.json() == {'detail': 'Order not found'}


async def test_retrieve_order_with_cars(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        **UserMockResponse().model_dump(),
        json=UserOutFactory.build().model_dump(exclude={'customer_id'}) | {'id': orders[0]['customer_id']},
    )
    car = CarReadFactory.build()
    with patch('app.dao.order.get_order_cars') as get_order_cars_mock:
        get_order_cars_mock.return_value = [car.model_dump()]
        response = await client.get(f'/orders/{orders[0]["_id"]}', headers={'auth-token': 'token'})

    assert response.status_code == 200
    result = response.json()

    cars = result.pop('order_cars')
    order = orders[0]
    order.pop('order_cars')
    assert result == order
    assert cars == [car.model_dump()]


async def test_retrieve_order_with_cars_not_owner(
        client: AsyncClient,
        orders: list[OrderDictSerialized],
        httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())
    car = CarReadFactory.build()
    with patch('app.dao.order.get_order_cars') as get_order_cars_mock:
        get_order_cars_mock.return_value = [car.model_dump()]
        response = await client.get(f'/orders/{orders[1]["_id"]}', headers={'auth-token': 'token'})

    assert response.status_code == 403
    assert response.json() == {'detail': 'User is not owner of order'}


async def test_retrieve_order_with_cars_serv_error(
        client: AsyncClient,
        orders: list[OrderDictSerialized],
        httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        **UserMockResponse().model_dump(),
        json=UserOutFactory.build().model_dump(exclude={'customer_id'}) | {'id': orders[0]['customer_id']},
    )
    with patch('app.dao.order.get_order_cars') as get_order_cars_mock:
        get_order_cars_mock.side_effect = CarServiceError(500, 'Internal Server Error')
        response = await client.get(f'/orders/{orders[0]["_id"]}', headers={'auth-token': 'token'})

    assert response.status_code == 500
    assert response.json() == {'detail': 'Internal Server Error'}


async def test_retrieve_order_not_found(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        **UserMockResponse().model_dump(),
        json=UserOutFactory.build().model_dump(exclude={'customer_id'}) | {'id': orders[0]['customer_id']},
    )
    response = await client.get('/orders/64df90203d15b134f47e4a9f', headers={'auth-token': 'token'})

    assert response.status_code == 404
    assert response.json() == {'detail': 'Order not found'}


async def test_update_order_prepayment(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        **UserMockResponse().model_dump(),
        json=UserOutFactory.build().model_dump(exclude={'customer_id'}) | {'id': orders[0]['customer_id']},
    )
    response = await client.patch(
        f'/orders/{orders[0]["_id"]}',
        json={'prepayment': 123},
        headers={'auth-token': 'token'},
    )

    response_data = response.json()
    assert response.status_code == 200
    assert response_data['prepayment'] == 123


async def test_update_order_not_found(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        **UserMockResponse().model_dump(),
        json=UserOutFactory.build().model_dump(exclude={'customer_id'}) | {'id': orders[0]['customer_id']},
    )
    response = await client.patch(
        '/orders/64df90203d15b134f47e4a9f',
        json={'prepayment': 123},
        headers={'auth-token': 'token'},
    )

    assert response.status_code == 404
    assert response.json() == {'detail': 'Order not found'}


async def test_update_order_rental_date(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        **UserMockResponse().model_dump(),
        json=UserOutFactory.build().model_dump(exclude={'customer_id'}) | {'id': orders[0]['customer_id']},
    )
    car = CarReadFactory().build()
    car.rental_cost = 25

    with patch('app.dao.order.get_order_cars') as get_order_cars_mock:
        get_order_cars_mock.return_value = [car]
        response = await client.patch(
            f'/orders/{orders[0]["_id"]}',
            json={
                'rental_date_start': str(datetime.now() + timedelta(seconds=10)),
                'rental_date_end': str(datetime.now() + timedelta(days=6, hours=1))
            },
            headers={'auth-token': 'token'},
        )

    response_data = response.json()
    assert response.status_code == 200
    assert response_data['rental_time'] == 6
    assert response_data['total_cost'] == 150


async def test_update_order_car_service_error(
        client: AsyncClient,
        orders: list[OrderDictSerialized],
        httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        **UserMockResponse().model_dump(),
        json=UserOutFactory.build().model_dump(exclude={'customer_id'}) | {'id': orders[0]['customer_id']},
    )
    with patch('app.dao.order.get_order_cars') as get_order_cars_mock:
        get_order_cars_mock.side_effect = CarServiceError(404, 'Cars not found')
        response = await client.patch(
            f'/orders/{orders[0]["_id"]}',
            json={
                'rental_date_start': str(datetime.now() + timedelta(seconds=10)),
                'rental_date_end': str(datetime.now() + timedelta(days=6, hours=1))
            },
            headers={'auth-token': 'token'},
        )

    assert response.status_code == 404
    assert response.json() == {'detail': 'Cars not found'}


async def test_update_order_no_rental_date(
        client: AsyncClient,
        orders: list[OrderDictSerialized],
        httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())

    response = await client.patch(
        f'/orders/{orders[0]["_id"]}',
        json={'order_cars': [1]},
        headers={'auth-token': 'token'},
    )
    assert response.status_code == 422
    msg = 'Value error, When you specify list cars you should specify and rental date'
    assert response.json()['detail'][0]['msg'] == msg


async def test_update_order_rental_date_start_less_today(
        client: AsyncClient,
        orders: list[OrderDictSerialized],
        httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())
    response = await client.patch(
        f'/orders/{orders[0]["_id"]}',
        json={
            'rental_date_start': str(datetime.now() - timedelta(seconds=10)),
            'rental_date_end': str(datetime.now() + timedelta(days=6, hours=1)),
        },
        headers={'auth-token': 'token'},
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'Value error, Rental date start can not be less than today'


async def test_update_order_diff_days(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())
    response = await client.patch(
        f'/orders/{orders[0]["_id"]}',
        json={
            'rental_date_start': str(datetime.now() + timedelta(seconds=10)),
            'rental_date_end': str(datetime.now() + timedelta(hours=1)),
        },
        headers={'auth-token': 'token'},
    )

    assert response.status_code == 422
    assert response.json()['detail'][0]['msg'] == 'Value error, Rent period must be between 1 and 30 days'


async def test_update_order_not_owner(client: AsyncClient, orders: list[OrderDictSerialized], httpx_mock: HTTPXMock):
    httpx_mock.add_response(**UserMockResponse().model_dump(), json=UserOutFactory.build().model_dump())
    response = await client.patch(
        f'/orders/{orders[1]["_id"]}',
        json={'prepayment': 123},
        headers={'auth-token': 'token'},
    )

    assert response.status_code == 403
    assert response.json() == {'detail': 'User is not owner of order'}
