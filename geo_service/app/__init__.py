from fastapi import FastAPI

from app.car_stations.router import router as car_stations_router
from app.redis_client import get_redis_client


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(car_stations_router)

    @app.on_event("shutdown")
    async def shutdown_event():
        client = get_redis_client()
        await client.close()

    return app
