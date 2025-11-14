# Contributing to Customify Core API

First off, thank you for considering contributing to Customify! It's people like you that make Customify such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Architecture Principles](#architecture-principles)
- [Common Tasks](#common-tasks)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at conduct@customify.app.

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.12+ installed
- PostgreSQL 15+ running
- Redis 7+ running
- Git configured
- GitHub account
- Basic understanding of FastAPI and SQLAlchemy

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/01-core-api.git
cd 01-core-api
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/customify-mvp/01-core-api.git
```

### Setup Development Environment
```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment file
cp .env.example .env
# Edit .env with your local settings

# Start infrastructure
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Seed test data
python scripts/seed_dev_data.py

# Run tests
pytest
```

### Verify Setup
```bash
# Start API
uvicorn app.main:app --reload

# In another terminal, test
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}

# Run tests
pytest --cov=app
# Should pass with >70% coverage
```

---

## Development Process

### Branching Strategy

We use **Git Flow** with the following branches:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `fix/*` - Bug fixes
- `refactor/*` - Code improvements
- `docs/*` - Documentation updates

### Creating a Feature Branch
```bash
# Update develop
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/add-pdf-generation

# Make changes, commit
git add .
git commit -m "feat: add PDF generation for orders"

# Push to your fork
git push origin feature/add-pdf-generation
```

### Keeping Your Branch Updated
```bash
# Fetch upstream changes
git fetch upstream

# Rebase on develop
git rebase upstream/develop

# Force push (if already pushed)
git push origin feature/add-pdf-generation --force-with-lease
```

---

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- Max line length: **100 characters** (not 79)
- Use **double quotes** for strings
- Use **trailing commas** in multi-line structures

### Type Hints

**Always use type hints:**
```python
# ✅ Good
def create_user(email: str, password: str) -> User:
    ...

async def get_designs(user_id: str, limit: int = 20) -> list[Design]:
    ...

# ❌ Bad
def create_user(email, password):
    ...
```

### Docstrings

Use **Google-style docstrings:**
```python
def calculate_quota(subscription: Subscription) -> int:
    """
    Calculate remaining design quota for subscription.
    
    Args:
        subscription: User's subscription entity
    
    Returns:
        Number of remaining designs this month
    
    Raises:
        ValueError: If subscription is invalid
    
    Example:
        >>> subscription = Subscription.create(user_id="123", plan=SubscriptionPlan.FREE)
        >>> calculate_quota(subscription)
        10
    """
    return subscription.designs_limit - subscription.designs_this_month
```

### Imports

**Order imports:**
```python
# Standard library
import asyncio
from datetime import datetime
from typing import Optional

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy import select

# Local application
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.database.repositories.user_repo_impl import UserRepositoryImpl
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `UserRepository`, `DesignModel` |
| Functions | snake_case | `create_user`, `get_by_email` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private | Prefix with `_` | `_internal_helper` |
| Async functions | Prefix with `async` | `async def fetch_data()` |

### Code Formatting

**Use Black for formatting:**
```bash
# Format all files
black app/ tests/

# Check formatting
black app/ tests/ --check

# Format specific file
black app/domain/entities/user.py
```

**Configuration (pyproject.toml):**
```toml
[tool.black]
line-length = 100
target-version = ['py312']
include = '\.pyi?$'
```

### Linting

**Use Ruff for linting:**
```bash
# Lint all files
ruff check app/ tests/

# Auto-fix issues
ruff check app/ tests/ --fix

# Specific rules
ruff check app/ --select=E,F,I
```

### Type Checking

**Use mypy for static type checking:**
```bash
# Type check
mypy app/

# Strict mode
mypy app/ --strict
```

---

## Testing Guidelines

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, isolated tests
│   ├── domain/
│   │   ├── test_user_entity.py
│   │   └── test_design_entity.py
│   └── application/
│       └── test_use_cases.py
└── integration/             # Tests with external dependencies
    └── api/
        ├── test_auth_endpoints.py
        └── test_design_endpoints.py
```

### Writing Tests

**Unit Test Example:**
```python
"""Unit tests for User entity."""

import pytest
from datetime import datetime, timezone
from app.domain.entities.user import User


def test_user_create():
    """Test User.create() factory method."""
    user = User.create(
        email="test@example.com",
        password_hash="hashed_password",
        full_name="Test User"
    )
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.is_verified is False


def test_user_mark_login():
    """Test User.mark_login() updates timestamp."""
    user = User.create("test@test.com", "hash", "Test")
    
    assert user.last_login is None
    
    user.mark_login()
    
    assert user.last_login is not None
    assert (datetime.now(timezone.utc) - user.last_login).seconds < 2


def test_user_deactivate():
    """Test User.deactivate() soft deletes user."""
    user = User.create("test@test.com", "hash", "Test")
    
    user.deactivate()
    
    assert user.is_active is False
    assert user.is_deleted is True
```

**Integration Test Example:**
```python
"""Integration tests for auth endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_register_success(client: AsyncClient):
    """Test POST /auth/register creates user."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "SecurePass123!",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert "id" in data
    assert "password_hash" not in data  # Security


@pytest.mark.integration
async def test_register_duplicate_email(client: AsyncClient):
    """Test duplicate email returns 409."""
    # Create first user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@test.com",
            "password": "Pass123!",
            "full_name": "First"
        }
    )
    
    # Try duplicate
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@test.com",
            "password": "Pass123!",
            "full_name": "Second"
        }
    )
    
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()
```

### Test Coverage

**Minimum coverage requirements:**

- **Overall:** 70%
- **Domain layer:** 90%+
- **Application layer:** 80%+
- **Infrastructure:** 70%+
- **Presentation:** 80%+

**Run coverage:**
```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Check if meets minimum
pytest --cov=app --cov-fail-under=70
```

### Testing Best Practices

1. **One assertion per test** (when possible)
2. **Test names describe behavior:** `test_user_deactivate_sets_is_deleted_true`
3. **AAA pattern:** Arrange, Act, Assert
4. **Use fixtures** for common setup
5. **Mock external services** in unit tests
6. **Use real database** in integration tests (test DB)
7. **Clean up after tests** (fixtures with teardown)

---

## Commit Message Guidelines

We follow **Conventional Commits** specification.

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, etc.

### Examples

**Feature:**
```
feat(designs): add PDF generation for orders

Implement PDF generation using ReportLab library.
Includes order details, customer info, and design preview.

Closes #123
```

**Bug fix:**
```
fix(celery): resolve task routing issue

Tasks were not being routed to correct queues due to
misconfigured task_routes in celery_app.py.

Fixed by using explicit task names in routing config.

Fixes #456
```

**Documentation:**
```
docs(api): update authentication endpoints

Add examples for JWT refresh token flow and
clarify token expiration behavior.
```

**Refactor:**
```
refactor(repositories): implement Unit of Work pattern

Improves transaction management by wrapping multiple
repository operations in a single transaction.

Breaking change: Repository constructors now require UoW
```

### Rules

- Use imperative mood: "add" not "added" or "adds"
- Don't capitalize first letter
- No period at the end
- Body is optional but recommended for non-trivial changes
- Reference issues/PRs in footer

---

## Pull Request Process

### Before Submitting PR

**Checklist:**

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Coverage maintained (>70%)
- [ ] No linting errors
- [ ] No type errors (mypy)
- [ ] CHANGELOG.md updated

### Creating PR

1. **Push to your fork:**
```bash
git push origin feature/your-feature
```

2. **Open PR on GitHub:**
   - Base: `develop`
   - Compare: `your-fork:feature/your-feature`

3. **Fill PR template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

## Related Issues
Closes #123
```

### PR Review Process

**Reviewers will check:**

1. **Code Quality**
   - Follows coding standards
   - No code smells
   - Proper error handling

2. **Architecture**
   - Maintains Clean Architecture layers
   - Dependencies point inward
   - No business logic in presentation layer

3. **Tests**
   - Adequate test coverage
   - Tests are meaningful
   - Edge cases covered

4. **Documentation**
   - Code is self-documenting
   - Complex logic has comments
   - Public APIs have docstrings

5. **Security**
   - No security vulnerabilities
   - Input validation
   - Proper authentication/authorization

### Addressing Review Comments
```bash
# Make changes
git add .
git commit -m "refactor: address review comments"

# Push updates
git push origin feature/your-feature
```

### Merging

**After approval:**

- Squash and merge (for feature branches)
- Rebase and merge (for small fixes)
- Create merge commit (for release branches)

---

## Architecture Principles

### Clean Architecture

**Layer responsibilities:**
```
Domain (Core)
  ├── Pure business logic
  ├── No framework dependencies
  └── Entities, Value Objects, Domain Services

Application
  ├── Use cases (orchestration)
  ├── Depends on Domain interfaces
  └── Transaction management

Infrastructure
  ├── Framework-specific code
  ├── Database, external services
  └── Implements Domain interfaces

Presentation
  ├── HTTP API (FastAPI)
  ├── Request/response schemas
  └── Depends on Application layer
```

**Dependency Rule:**

- **Domain** depends on: Nothing
- **Application** depends on: Domain
- **Infrastructure** depends on: Domain, Application
- **Presentation** depends on: Application, Infrastructure (via DI)

### SOLID Principles

**Single Responsibility:**
```python
# ✅ Good - One responsibility
class UserRepository:
    async def create(self, user: User) -> User:
        ...
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        ...

# ❌ Bad - Multiple responsibilities
class UserService:
    async def create_user(self, ...):
        ...
    
    async def send_welcome_email(self, ...):  # Different responsibility
        ...
```

**Open/Closed:**
```python
# ✅ Good - Open for extension, closed for modification
class DesignValidator(Protocol):
    def validate(self, design_data: dict) -> None:
        ...

class TShirtValidator:
    def validate(self, design_data: dict) -> None:
        # T-shirt specific validation
        ...

class MugValidator:
    def validate(self, design_data: dict) -> None:
        # Mug specific validation
        ...
```

**Liskov Substitution:**
```python
# ✅ Good - Subtypes are substitutable
def process_payment(payment_gateway: IPaymentGateway):
    result = payment_gateway.charge(amount)  # Works with any implementation
    return result

# Works with:
stripe_gateway: IPaymentGateway = StripeGateway()
paypal_gateway: IPaymentGateway = PayPalGateway()
```

**Interface Segregation:**
```python
# ✅ Good - Small, focused interfaces
class IUserRepository(ABC):
    async def create(self, user: User) -> User:
        ...

class IEmailRepository(ABC):
    async def send(self, to: str, subject: str, body: str) -> bool:
        ...

# ❌ Bad - Fat interface
class IUserService(ABC):
    async def create_user(self, ...):
        ...
    async def send_email(self, ...):  # Unrelated
        ...
```

**Dependency Inversion:**
```python
# ✅ Good - Depend on abstractions
class CreateUserUseCase:
    def __init__(self, user_repo: IUserRepository):  # Interface
        self.user_repo = user_repo

# ❌ Bad - Depend on concretions
class CreateUserUseCase:
    def __init__(self, user_repo: UserRepositoryImpl):  # Implementation
        self.user_repo = user_repo
```

---

## Common Tasks

### Adding a New Endpoint

1. **Define Pydantic schemas** (`app/presentation/schemas/`)
```python
# app/presentation/schemas/order_schema.py

class OrderCreateRequest(BaseModel):
    design_id: str
    quantity: int = Field(ge=1, le=1000)
    
class OrderResponse(BaseModel):
    id: str
    design_id: str
    status: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
```

2. **Create endpoint** (`app/presentation/api/v1/endpoints/`)
```python
# app/presentation/api/v1/endpoints/orders.py

from fastapi import APIRouter, Depends
from app.presentation.schemas.order_schema import OrderCreateRequest, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    request: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    order_repo: IOrderRepository = Depends(get_order_repository),
):
    """Create new order."""
    # Use case logic
    ...
```

3. **Register router** (`app/presentation/api/v1/router.py`)
```python
from app.presentation.api.v1.endpoints import auth, designs, orders

api_router.include_router(orders.router)
```

4. **Add tests**
```python
# tests/integration/api/test_order_endpoints.py

async def test_create_order_success(authenticated_client):
    client, headers = authenticated_client
    
    response = await client.post(
        "/api/v1/orders",
        headers=headers,
        json={"design_id": "...", "quantity": 1}
    )
    
    assert response.status_code == 201
```

### Adding a New Entity

1. **Create entity** (`app/domain/entities/`)
```python
# app/domain/entities/order.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Order:
    """Order domain entity."""
    id: str
    user_id: str
    design_id: str
    quantity: int
    status: str
    created_at: datetime
    
    @staticmethod
    def create(user_id: str, design_id: str, quantity: int) -> "Order":
        """Factory method to create new order."""
        return Order(
            id=str(uuid4()),
            user_id=user_id,
            design_id=design_id,
            quantity=quantity,
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
```

2. **Create repository interface** (`app/domain/repositories/`)
```python
# app/domain/repositories/order_repository.py

from abc import ABC, abstractmethod

class IOrderRepository(ABC):
    @abstractmethod
    async def create(self, order: Order) -> Order:
        pass
    
    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        pass
```

3. **Create SQLAlchemy model** (`app/infrastructure/database/models/`)

4. **Create repository implementation** (`app/infrastructure/database/repositories/`)

5. **Create converter** (`app/infrastructure/database/converters/`)

6. **Add migration** (`alembic revision --autogenerate -m "add orders table"`)

7. **Add tests**

### Adding a Background Task

1. **Create task** (`app/infrastructure/workers/tasks/`)
```python
# app/infrastructure/workers/tasks/generate_report.py

from app.infrastructure.workers.celery_app import celery_app

@celery_app.task(bind=True, name="generate_report")
def generate_report(self, user_id: str, report_type: str) -> dict:
    """Generate user report."""
    try:
        # Task logic
        ...
        return {"status": "success", "report_url": url}
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise
```

2. **Register in celery_app.py**
```python
celery_app.autodiscover_tasks([
    'app.infrastructure.workers.tasks'
])

# Add routing
celery_app.conf.task_routes = {
    "generate_report": {"queue": "default"},
}
```

3. **Enqueue from use case**
```python
from app.infrastructure.workers.tasks.generate_report import generate_report

# In use case
task = generate_report.delay(user_id, report_type)
```

4. **Add tests**

---

## Questions?

If you have questions:

- Check existing issues and PRs
- Ask in GitHub Discussions
- Join our Discord: https://discord.gg/customify
- Email: dev@customify.app

---

**Thank you for contributing! 🎉**