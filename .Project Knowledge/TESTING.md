# Testing Strategy - Core API

**Propósito:** Estrategia de testing, fixtures, y mejores prácticas

---

## 🎯 Pirámide de Testing
```
        /\
       /  \      E2E Tests (5%)
      /────\     - Full user journeys
     /      \    - Slow, brittle
    /────────\   
   /          \  Integration Tests (25%)
  /────────────\ - API + DB + Redis
 /              \ - Medium speed
/────────────────\ 
   Unit Tests     Unit Tests (70%)
   (70%)          - Fast, isolated
                  - No external deps
```

**Targets:**
- Total coverage: >80%
- Unit tests: >90% coverage
- Integration: >70% coverage
- E2E: Critical paths only

---

## 🚀 Setup Testing
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific layer
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Watch mode (re-run on change)
ptw  # pytest-watch
```

---

## 📁 Estructura Tests
```
tests/
├── conftest.py              # Fixtures globales
├── unit/                    # Fast, isolated
│   ├── domain/
│   │   ├── test_entities.py
│   │   ├── test_value_objects.py
│   │   └── test_services.py
│   ├── application/
│   │   └── test_use_cases.py
│   └── shared/
│       └── test_utils.py
├── integration/             # With real DB/Redis
│   ├── conftest.py
│   ├── database/
│   │   └── test_repositories.py
│   ├── api/
│   │   ├── test_auth_endpoints.py
│   │   └── test_design_endpoints.py
│   └── cache/
│       └── test_redis.py
├── e2e/                     # Full flows
│   └── test_user_journey.py
└── fixtures/                # Test data factories
    ├── user_factory.py
    └── design_factory.py
```

---

## 🧪 Unit Tests (Fast, Isolated)

### Características
- ✅ NO external dependencies (no DB, Redis, APIs)
- ✅ Mock all I/O
- ✅ Test business logic only
- ✅ Run en <1s total

### Ejemplo: Test Domain Entity
```python
# tests/unit/domain/test_design.py

import pytest
from app.domain.entities.design import Design, DesignStatus

def test_design_create_valid():
    """Test creating valid design."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Hello",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    assert design.id is not None
    assert design.status == DesignStatus.DRAFT
    assert design.user_id == "user-123"

def test_design_create_invalid_product_type():
    """Test invalid product type raises error."""
    with pytest.raises(ValueError, match="Invalid product type"):
        Design.create(
            user_id="user-123",
            product_type="invalid",
            design_data={}
        )

def test_design_validate_text_too_long():
    """Test text length validation."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "x" * 101,  # Max 100
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    with pytest.raises(ValueError, match="Text too long"):
        design.validate()
```

### Ejemplo: Test Use Case (con mocks)
```python
# tests/unit/application/test_create_design_use_case.py

import pytest
from unittest.mock import AsyncMock, Mock
from app.application.use_cases.designs.create_design import CreateDesignUseCase
from app.domain.entities.design import Design
from app.domain.exceptions import QuotaExceededError

@pytest.fixture
def mock_design_repo():
    """Mock design repository."""
    repo = AsyncMock()
    repo.create.return_value = Design(
        id="design-123",
        user_id="user-123",
        product_type="t-shirt",
        design_data={},
        status="draft",
        preview_url=None,
        created_at="2025-01-01",
        updated_at="2025-01-01"
    )
    return repo

@pytest.fixture
def mock_subscription_repo():
    """Mock subscription repository."""
    repo = AsyncMock()
    # Return subscription with quota available
    subscription = Mock()
    subscription.is_active = True
    subscription.has_quota.return_value = True
    repo.get_by_user.return_value = subscription
    return repo

@pytest.mark.asyncio
async def test_create_design_success(mock_design_repo, mock_subscription_repo):
    """Test successful design creation."""
    use_case = CreateDesignUseCase(
        design_repo=mock_design_repo,
        subscription_repo=mock_subscription_repo,
        quota_checker=Mock(),
        ai_client=AsyncMock(),
        queue_client=AsyncMock()
    )
    
    design = await use_case.execute(
        user_id="user-123",
        product_type="t-shirt",
        design_data={},
        use_ai=False
    )
    
    assert design.id == "design-123"
    mock_design_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_create_design_quota_exceeded(mock_design_repo, mock_subscription_repo):
    """Test design creation when quota exceeded."""
    # Setup: subscription without quota
    subscription = Mock()
    subscription.is_active = True
    subscription.has_quota.return_value = False
    mock_subscription_repo.get_by_user.return_value = subscription
    
    use_case = CreateDesignUseCase(
        design_repo=mock_design_repo,
        subscription_repo=mock_subscription_repo,
        quota_checker=Mock(),
        ai_client=AsyncMock(),
        queue_client=AsyncMock()
    )
    
    with pytest.raises(QuotaExceededError):
        await use_case.execute(
            user_id="user-123",
            product_type="t-shirt",
            design_data={},
            use_ai=False
        )
```

---

## 🔗 Integration Tests (With Real Dependencies)

### Características
- ✅ Real DB (PostgreSQL en Docker)
- ✅ Real Redis
- ✅ Test full stack (endpoint → DB)
- ⚠️ Slower (~100ms per test)

### Setup (conftest.py)
```python
# tests/integration/conftest.py

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

from app.main import app
from app.infrastructure.database.session import Base, get_db_session
from app.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/customify_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback after each test

@pytest.fixture
async def client(db_session):
    """Create test HTTP client."""
    app.dependency_overrides[get_db_session] = lambda: db_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
async def auth_headers(client, db_session):
    """Create authenticated user and return headers."""
    # Create test user
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@test.com",
            "password": "Test1234",
            "full_name": "Test User"
        }
    )
    
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@test.com",
            "password": "Test1234"
        }
    )
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### Ejemplo: Test API Endpoint
```python
# tests/integration/api/test_design_endpoints.py

import pytest

@pytest.mark.asyncio
async def test_create_design_success(client, auth_headers):
    """Test POST /designs success."""
    response = await client.post(
        "/api/v1/designs",
        json={
            "product_type": "t-shirt",
            "design_data": {
                "text": "Hello",
                "font": "Bebas-Bold",
                "color": "#FF0000"
            },
            "use_ai_suggestions": False
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["product_type"] == "t-shirt"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_create_design_unauthorized(client):
    """Test POST /designs without auth."""
    response = await client.post(
        "/api/v1/designs",
        json={"product_type": "t-shirt", "design_data": {}}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_list_designs(client, auth_headers):
    """Test GET /designs pagination."""
    # Create 3 designs
    for i in range(3):
        await client.post(
            "/api/v1/designs",
            json={
                "product_type": "t-shirt",
                "design_data": {"text": f"Design {i}"}
            },
            headers=auth_headers
        )
    
    # List designs
    response = await client.get("/api/v1/designs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["designs"]) == 3
```

---

## 🎭 E2E Tests (Full User Journeys)

### Características
- ✅ Test complete user flows
- ✅ All systems integrated
- ⚠️ Slowest (seconds per test)
- ⚠️ Only critical paths

### Ejemplo: Complete User Journey
```python
# tests/e2e/test_user_journey.py

import pytest

@pytest.mark.asyncio
async def test_complete_user_journey(client):
    """
    Test: User registers → creates design → views designs
    """
    # 1. Register
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "journey@test.com",
            "password": "Test1234",
            "full_name": "Journey User"
        }
    )
    assert response.status_code == 201
    
    # 2. Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "journey@test.com", "password": "Test1234"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Get profile
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "journey@test.com"
    
    # 4. Create design
    response = await client.post(
        "/api/v1/designs",
        json={
            "product_type": "t-shirt",
            "design_data": {"text": "My Design"}
        },
        headers=headers
    )
    assert response.status_code == 201
    design_id = response.json()["id"]
    
    # 5. Get design
    response = await client.get(f"/api/v1/designs/{design_id}", headers=headers)
    assert response.status_code == 200
    
    # 6. List designs
    response = await client.get("/api/v1/designs", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["designs"]) >= 1
```

---

## 🏭 Test Factories
```python
# tests/fixtures/user_factory.py

from app.domain.entities.user import User
from app.infrastructure.database.models.user_model import UserModel
from datetime import datetime
import uuid

class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def create_entity(
        email: str = "test@test.com",
        password_hash: str = "hashed",
        **kwargs
    ) -> User:
        """Create User entity for unit tests."""
        return User(
            id=kwargs.get("id", str(uuid.uuid4())),
            email=email,
            password_hash=password_hash,
            full_name=kwargs.get("full_name", "Test User"),
            is_active=kwargs.get("is_active", True),
            is_verified=kwargs.get("is_verified", False),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow())
        )
    
    @staticmethod
    def create_model(
        email: str = "test@test.com",
        **kwargs
    ) -> UserModel:
        """Create UserModel for integration tests."""
        return UserModel(
            id=kwargs.get("id", str(uuid.uuid4())),
            email=email,
            password_hash="hashed",
            full_name=kwargs.get("full_name", "Test User"),
            is_active=kwargs.get("is_active", True),
            is_verified=kwargs.get("is_verified", False)
        )

# Usage in tests
def test_something():
    user = UserFactory.create_entity(email="custom@test.com")
    assert user.email == "custom@test.com"
```

---

## ✅ Testing Checklist

Antes de PR:
```bash
# 1. All tests pass
pytest -v

# 2. Coverage >80%
pytest --cov=app --cov-report=term

# 3. No warnings
pytest -W error

# 4. Integration tests pass
pytest tests/integration/

# 5. E2E critical paths pass
pytest tests/e2e/
```

---

## 🐛 Debugging Tests
```bash
# Run single test
pytest tests/unit/domain/test_design.py::test_design_create_valid -v

# Print output (no capture)
pytest -s

# Drop into debugger on failure
pytest --pdb

# Stop on first failure
pytest -x

# Run last failed tests only
pytest --lf

# Show local variables on failure
pytest -l
```

---

## 📊 Coverage Report
```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# Open report
open htmlcov/index.html

# Terminal report (missing lines)
pytest --cov=app --cov-report=term-missing

# Fail if coverage <80%
pytest --cov=app --cov-fail-under=80
```

---

## ⚡ Performance Testing
```python
# tests/performance/test_api_performance.py

import pytest
import time

@pytest.mark.asyncio
async def test_design_creation_performance(client, auth_headers):
    """Test design creation latency <200ms."""
    start = time.time()
    
    response = await client.post(
        "/api/v1/designs",
        json={"product_type": "t-shirt", "design_data": {}},
        headers=auth_headers
    )
    
    latency_ms = (time.time() - start) * 1000
    
    assert response.status_code == 201
    assert latency_ms < 200, f"Latency {latency_ms}ms > 200ms"
```

---

## 🚨 Common Testing Issues

| Issue | Solution |
|-------|----------|
| `RuntimeError: Event loop closed` | Add `@pytest.mark.asyncio` decorator |
| Tests modify DB permanently | Use transactions + rollback in fixtures |
| Slow tests (>10s total) | Use mocks for external APIs, factories for data |
| Flaky tests (pass/fail randomly) | Fix async race conditions, use deterministic data |
| Import errors in tests | Add `__init__.py` in test dirs, fix PYTHONPATH |

---

**Próximo documento:** [DEPLOY.md](./DEPLOY.md)