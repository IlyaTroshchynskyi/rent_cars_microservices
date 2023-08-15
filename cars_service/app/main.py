from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.cars.router import router as car_router
from app.config import settings

app = FastAPI()

app.include_router(car_router)

app.mount('/static', StaticFiles(directory=settings.STATIC_DIR), name='static')
