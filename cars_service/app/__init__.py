
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from app.cars.router import router as car_router
from app.reviews.router import router as review_router
from app.trip.router import router as trip_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI()
    app.include_router(car_router)
    app.include_router(review_router)
    app.include_router(trip_router)

    app.mount('/static', StaticFiles(directory=settings.STATIC_DIR), name='static')
    return app
