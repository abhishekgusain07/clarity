from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apply.config import get_settings


def _make_engine() -> tuple[async_sessionmaker[AsyncSession], object]:
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=(settings.apply_env == "dev"),
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return session_factory, engine


_session_factory, _engine = _make_engine()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session


def get_engine():
    return _engine
