from unittest.mock import patch

from httpx import AsyncClient


async def test_run_trip(client: AsyncClient):
    with patch('app.trip.router.start_trip') as start_trip_mock:
        response = await client.post('/trip/', params={'car_number': '1'})

    assert response.status_code == 200
    assert response.json() == {'message': 'Start trip for car 1'}
    start_trip_mock.assert_called()
