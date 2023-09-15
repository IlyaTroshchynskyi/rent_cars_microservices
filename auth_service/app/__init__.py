from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.users.router import router as user_router


def create_app() -> FastAPI:
    app = FastAPI()
    auth_app = FastAPI()
    app.include_router(user_router)
    auth_app.include_router(auth_router)
    app.mount('/auth', auth_app)
    return app
