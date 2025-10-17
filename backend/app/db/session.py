from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ..core.config import settings


def _build_engine_config(database_url: str):
    url = make_url(database_url)
    query = dict(url.query)
    ssl_mode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    connect_args: dict[str, object] = {}

    target_ssl_mode = (ssl_mode or "require").lower()
    if target_ssl_mode == "require":
        connect_args["ssl"] = True
    elif target_ssl_mode not in {"disable", "allow"}:
        connect_args["ssl"] = True

    sanitized_url = url.set(query=query)
    return sanitized_url, connect_args


engine_url, connect_args = _build_engine_config(settings.database_url)
engine = create_async_engine(engine_url, echo=False, future=True, connect_args=connect_args)
AsyncSessionMaker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with AsyncSessionMaker() as session:
        yield session
