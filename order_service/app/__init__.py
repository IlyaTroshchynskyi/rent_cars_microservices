from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.db import init_db
from app.orders.router import router as order_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(order_router)

    instrumentator = Instrumentator().instrument(app)
    instrumentator.expose(app)
    return app
