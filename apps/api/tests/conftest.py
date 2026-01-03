"""Pytest configuration and shared fixtures."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from typing import AsyncGenerator
import uuid

from src.main import app
from src.core.database import Base, get_db
from src.models import Clinic


# Test database URL (use SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Monkey-patch JSONB to be compatible with SQLite for testing
# This needs to happen before models are imported
JSONB = JSON


@pytest.fixture
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async test database session."""
    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session


@pytest.fixture
async def test_clinic(async_session) -> Clinic:
    """Create a test clinic with API key."""
    clinic = Clinic(
        id=uuid.uuid4(),
        name="Test Dental Clinic",
        api_key="test_clinic_api_key_12345",
        timezone="Australia/Sydney",
        settings={},
    )
    async_session.add(clinic)
    await async_session.commit()
    await async_session.refresh(clinic)
    return clinic


@pytest.fixture
async def client(async_session, test_clinic) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with database override."""

    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
