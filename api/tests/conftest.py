import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from drillsense.database import get_session
from drillsense.main import app
from drillsense.models import Base

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DB_URL, echo=False)
test_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session() as s:
        yield s


@pytest.fixture
def sample_device_payload() -> dict:
    return {
        "name": f"Test Rig {uuid.uuid4().hex[:6]}",
        "device_type": "drilling_rig",
        "location": "Test Platform",
    }


@pytest.fixture
def sample_telemetry_reading() -> dict:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "rpm": 120.0,
        "wob": 35.0,
        "torque": 22.0,
        "mud_flow_rate": 2800.0,
        "vibration": 3.5,
    }
