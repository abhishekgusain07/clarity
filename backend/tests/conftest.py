import asyncio
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apply.config import get_settings
from apply.db.models import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch):
    """Isolate tests from the repo-root `.env` real-agents flag.

    Tests default to stubs (APPLY_USE_REAL_AGENTS=false) unless a specific
    test explicitly opts in via its own monkeypatch. Also clears the
    `get_settings` lru_cache around every test so env changes take effect
    and cached state never leaks across tests.
    """
    monkeypatch.setenv("APPLY_USE_REAL_AGENTS", "false")
    get_settings.cache_clear()  # type: ignore[attr-defined]
    yield
    get_settings.cache_clear()  # type: ignore[attr-defined]


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    # Ensure a clean schema for this test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()
