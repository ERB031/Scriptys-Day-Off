from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ..core.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionMaker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with AsyncSessionMaker() as session:
        yield session

