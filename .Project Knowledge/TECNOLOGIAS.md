# Stack Tecnológico - Core API

**Propósito:** Referencia rápida del stack técnico para agentes IA (especialmente Copilot con memoria corta)

---

## 🎯 Stack Principal

| Categoría | Tecnología | Versión | Por Qué |
|-----------|------------|---------|---------|
| **Lenguaje** | Python | 3.12 | Type hints mejorados, async nativo, 10-15% faster |
| **Framework** | FastAPI | 0.109+ | Async-first, auto-docs, Pydantic v2 integrado |
| **ORM** | SQLAlchemy | 2.0+ | Async support, type-safe con `Mapped[T]` |
| **Migrations** | Alembic | 1.13+ | Standard para SQLAlchemy |
| **Validation** | Pydantic | 2.6+ | Type safety, 5-50x faster que v1 (Rust core) |
| **Auth** | python-jose | 3.3+ | JWT tokens |
| **Password** | passlib[bcrypt] | 1.7+ | Bcrypt hashing |
| **HTTP Client** | httpx | 0.26+ | Async (NO usar `requests` - es sync) |
| **Testing** | pytest + pytest-asyncio | 7.4+ / 0.23+ | Async test support |
| **Linting** | ruff | 0.1+ | 10-100x faster que flake8 |
| **Formatting** | black | 24.0+ | Opinionated, zero config |

---

## ⚡ Setup Rápido
```bash
# Virtual env
python3.12 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload

# Tests
pytest -v --cov=app
```

---

## 🚨 RESTRICCIONES CRÍTICAS (para IAs)

### 1. SIEMPRE async/await
```python
# ✅ CORRECTO
async def get_user(user_id: str):
    async with get_db_session() as session:
        result = await session.execute(...)

# ❌ INCORRECTO (bloquea event loop)
def get_user_sync(user_id: str):
    with get_db_session() as session:  # NUNCA SYNC I/O
        result = session.execute(...)
```

### 2. Pydantic V2 (NO V1)
```python
# ✅ V2 syntax
class Config:
    from_attributes = True  # V2

# ❌ V1 syntax (deprecated)
class Config:
    orm_mode = True  # V1 - NO USAR
```

### 3. SQLAlchemy 2.0 style
```python
# ✅ V2 style con Mapped[T]
class User(Base):
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255))

# ❌ V1 style (no usar)
class User(Base):
    id = Column(String(36), primary_key=True)  # Old style
```

### 4. Clean Architecture - Dependency Inversion
```python
# ✅ Domain define interface
class IUserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User: ...

# ✅ Infrastructure implementa
class UserRepositoryImpl(IUserRepository):
    async def create(self, user: User) -> User:
        # SQLAlchemy implementation

# ✅ Use Case depende de abstracción (NO de implementación)
class CreateUserUseCase:
    def __init__(self, user_repo: IUserRepository):  # Interface, not Impl
        self.repo = user_repo
```

### 5. NO mezclar capas
```python
# ❌ NUNCA hacer esto en Domain
from sqlalchemy import Column  # Domain NO conoce SQLAlchemy

# ❌ NUNCA hacer esto en Use Case
from fastapi import HTTPException  # Application NO conoce HTTP

# ❌ NUNCA hacer business logic en Presentation
@router.post("/designs")
async def create_design(request: Request):
    # Business logic HERE = WRONG
    if user.designs_count > limit:  # NO - esto va en Use Case
```

---

## 📦 Instalación Detallada

### Production Dependencies (requirements.txt)
```
fastapi[all]==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.6.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.26.0
redis==5.0.1
boto3==1.34.0
python-multipart==0.0.6
email-validator==2.1.0
```

### Development Dependencies (requirements-dev.txt)
```
pytest==7.4.0
pytest-asyncio==0.23.0
pytest-cov==4.1.0
ruff==0.1.0
black==24.0.0
mypy==1.8.0
```

---

## 🔧 Configuración Archivos

### pyproject.toml (mínimo necesario)
```toml
[tool.black]
line-length = 88
target-version = ['py312']

[tool.ruff]
line-length = 88
target-version = "py312"
select = ["E", "W", "F", "I", "B", "UP"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### .env.example
```bash
# App
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/customify

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT (generate: openssl rand -hex 32)
JWT_SECRET_KEY=your-secret-key-min-32-chars

# AWS
AWS_REGION=us-east-1
S3_BUCKET_NAME=customify-production

# OpenAI
OPENAI_API_KEY=sk-proj-xxx

# Stripe
STRIPE_SECRET_KEY=sk_xxx
```

---

## 🎨 Naming Conventions
```python
# Files
user_repository.py           # snake_case
create_design_use_case.py

# Classes
class CreateDesignUseCase    # PascalCase
class DesignRepository

# Functions/methods
async def create_design()    # snake_case
async def get_user_by_id()

# Constants
MAX_DESIGNS_PER_MONTH = 100  # UPPER_SNAKE_CASE

# Variables
user_id = "123"              # snake_case
design_data = {...}
```

---

## 📚 Referencias Esenciales

**Documentación oficial:**
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/) - ORM
- [Pydantic V2](https://docs.pydantic.dev/latest/) - Validation
- [Alembic](https://alembic.sqlalchemy.org/) - Migrations

**Arquitectura:**
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)

---

## ⚠️ Errores Comunes a Evitar

| Error | Por qué está mal | Solución |
|-------|------------------|----------|
| `requests.get()` | Sync I/O, bloquea event loop | Usar `httpx` async |
| `time.sleep()` | Bloquea event loop | Usar `asyncio.sleep()` |
| Pydantic V1 syntax | Deprecated, slower | Actualizar a V2 syntax |
| SQLAlchemy 1.4 style | Old API | Usar 2.0 style con `Mapped[T]` |
| Domain importa SQLAlchemy | Rompe Clean Architecture | Solo interfaces en Domain |
| Use Case retorna HTTPException | Mezcla layers | Retornar domain exceptions |

---
