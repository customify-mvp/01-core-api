"""Shared pytest fixtures."""

import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.infrastructure.database.session import Base, get_db_session

# Test database URL - use customify-postgres as host when running inside Docker
TEST_DATABASE_URL = "postgresql+asyncpg://customify:customify123@customify-postgres:5432/customify_test"


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async def override_get_db_session():
        yield db_session
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@test.com",
        "password": "Test1234",
        "full_name": "Test User"
    }


@pytest.fixture
async def authenticated_client(client, test_user_data) -> AsyncGenerator[tuple[AsyncClient, dict], None]:
    """Create authenticated test client."""
    # Register
    register_response = await client.post(
        "/api/v1/auth/register",
        json=test_user_data
    )
    assert register_response.status_code == 201
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    yield client, headers
