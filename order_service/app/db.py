from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.models import gather_documents


async def init_db():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(database=getattr(client, settings.MONGODB_DB_NAME), document_models=gather_documents())
