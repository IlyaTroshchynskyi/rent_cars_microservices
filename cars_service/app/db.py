from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

from app.config import get_settings

settings = get_settings()


engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)


async def get_session() -> AsyncSession:
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
