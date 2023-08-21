import asyncio

from httpx import AsyncClient


async def send_request(url: str, ids: list[int] = None):
    async with AsyncClient() as client:
        if ids:
            requests = [fetch_result(f'{url}/{_id}', client) for _id in ids]
            result = await asyncio.gather(*requests)
        else:
            result = await asyncio.gather(fetch_result(url, client))
    return result


async def fetch_result(url: str, client: AsyncClient):
    return await client.get(url)


async def result_to_json1(results: list) -> list[dict]:
    return [item.json() for item in results]


async def result_to_json():
    return [{'rental_cost': 5}, {'rental_cost': 10}]
