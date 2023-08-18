from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.orders.router import router as order_router
from app.db import init_db


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(order_router)
    return app
