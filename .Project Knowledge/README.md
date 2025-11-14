# Core API - Customify

**Versión:** 1.0.0  
**Última actualización:** Noviembre 2025  
**Responsable:** Backend Team  
**Status:** 🟡 In Development

---

## 🎯 Propósito del Componente

El **Core API** es el núcleo del backend de Customify. Es responsable de:

### Responsabilidades Principales:

1. **Autenticación y Autorización**
   - JWT-based authentication (stateless)
   - Role-based access control (RBAC)
   - Session management via Redis
   - Password hashing con bcrypt

2. **CRUD Operations**
   - Designs (create, read, update, delete, duplicate)
   - Users (profile management)
   - Subscriptions (status, usage tracking)
   - Orders (read-only, escritura via webhooks)

3. **Business Logic Core**
   - Quota enforcement (designs/month según plan)
   - Design validation (schema, contenido)
   - Subscription status verification
   - Permission checks

4. **Service Orchestration**
   - Coordinación con AI Services (OpenAI, Pinecone)
   - Upload a Storage Layer (S3)
   - Enqueue background jobs (SQS → Workers)
   - Cache management (Redis)

5. **API Gateway**
   - Rate limiting (100 req/min por IP)
   - CORS configuration
   - Request/Response validation
   - Error handling estandarizado

### Lo que NO hace (fuera de scope):

- ❌ Renderizado de imágenes (→ 05-render-engine)
- ❌ Generación de PDFs (→ 04-background-workers)
- ❌ Procesamiento de webhooks directos (→ 03-integration-layer)
- ❌ Análisis complejos de IA (→ 02-ai-services)

---

## 🏗️ Contexto en Arquitectura Global
```
                    ┌─────────────────┐
                    │  Widget/Dashboard│
                    └────────┬─────────┘
                             │ HTTPS REST
                             ↓
                    ┌─────────────────┐
                    │   Cloudflare    │
                    │   CDN + WAF     │
                    └────────┬─────────┘
                             │
                             ↓
                    ┌─────────────────┐
                    │    AWS ALB      │
                    └────────┬─────────┘
                             │
                             ↓
            ┌────────────────────────────────┐
            │     ⭐ CORE API (Este)         │
            │     FastAPI + Python 3.12      │
            │     Clean Architecture         │
            └────┬────────┬────────┬─────────┘
                 │        │        │
        ┌────────┘        │        └─────────┐
        ↓                 ↓                  ↓
   [PostgreSQL]      [Redis]          [S3/OpenAI/SQS]
   Users/Designs     Cache/Sessions    External Services
```

**Dependencies (Consume):**
- PostgreSQL RDS (critical - 503 si falla)
- Redis ElastiCache (important - degraded sin cache)
- OpenAI API (important - features degradadas)
- Pinecone (optional - feature unavailable)
- S3 (important - uploads fallan)
- SQS (important - jobs no encolan)

**Dependents (Sirve a):**
- Widget Frontend (React)
- Dashboard Frontend (React)
- Background Workers (leen DB, actualizan status)
- Integration Layer (webhooks llaman endpoints)

---

## 🛠️ Stack Tecnológico Core

| Categoría | Tecnología | Versión | Justificación |
|-----------|------------|---------|---------------|
| **Lenguaje** | Python | 3.12 | Type hints mejorados, performance, async nativo |
| **Framework** | FastAPI | 0.109+ | Async-first, auto-docs, Pydantic v2, rápido |
| **ORM** | SQLAlchemy | 2.0+ | Async support, type-safe, industry standard |
| **Migrations** | Alembic | 1.13+ | De facto para SQLAlchemy |
| **Validation** | Pydantic | 2.6+ | Type safety, 5-50x faster que v1 |
| **Auth** | python-jose | 3.3+ | JWT implementation |
| **Password** | passlib[bcrypt] | 1.7+ | Secure hashing, bcrypt algorithm |
| **HTTP Client** | httpx | 0.26+ | Async HTTP, mejor que requests |
| **Testing** | pytest | 7.4+ | Standard Python testing |
| **Async Testing** | pytest-asyncio | 0.23+ | Async test support |
| **Linting** | ruff | 0.1+ | 10-100x faster que flake8 |
| **Formatting** | black | 24.0+ | Opinionated, zero config |
| **Type Checking** | mypy | 1.8+ | Static type checking |

---

## ⚡ Inicio Rápido (5 minutos)

### Prerequisitos:
- Docker 24+ y Docker Compose 2.20+
- Git
- (Opcional) Python 3.12 para desarrollo local

### Comandos:
```bash
# 1. Clonar repositorio
git clone https://github.com/customify/core-api.git
cd core-api

# 2. Copiar variables de entorno
cp .env.example .env
# Editar .env con tus valores (DATABASE_URL, REDIS_URL, etc)

# 3. Levantar stack completo
docker-compose up -d

# 4. Aplicar migrations
docker-compose exec api alembic upgrade head

# 5. Verificar que funciona
curl http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected","redis":"connected"}

# 6. Ver documentación interactiva
open http://localhost:8000/docs  # Swagger UI
open http://localhost:8000/redoc # ReDoc
```

**Eso es todo.** API está corriendo en `http://localhost:8000`

### Acceso rápido:
- **API:** http://localhost:8000
- **Docs (Swagger):** http://localhost:8000/docs
- **Docs (ReDoc):** http://localhost:8000/redoc
- **PostgreSQL:** localhost:5432 (user: postgres, pass: ver .env)
- **Redis:** localhost:6379

---

## 📂 Estructura del Proyecto
```
core-api/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # PR checks: tests, lint, type check
│       ├── cd.yml                 # Deploy a ECS on merge main
│       └── security-scan.yml      # Trivy security scan
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # ⭐ FastAPI app + ASGI lifespan
│   ├── config.py                  # Pydantic Settings (env vars)
│   │
│   ├── domain/                    # ⭐ CORE BUSINESS LOGIC
│   │   ├── __init__.py
│   │   ├── entities/              # Business entities (pure Python)
│   │   │   ├── __init__.py
│   │   │   ├── user.py           # User entity
│   │   │   ├── design.py         # Design entity
│   │   │   ├── subscription.py   # Subscription entity
│   │   │   └── order.py          # Order entity
│   │   │
│   │   ├── value_objects/         # Immutable values
│   │   │   ├── __init__.py
│   │   │   ├── email.py          # Email validation VO
│   │   │   ├── money.py          # Money VO (amount + currency)
│   │   │   └── design_data.py    # Design JSON schema VO
│   │   │
│   │   ├── repositories/          # Interfaces (ABC)
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── design_repository.py
│   │   │   ├── subscription_repository.py
│   │   │   └── order_repository.py
│   │   │
│   │   ├── services/              # Domain services
│   │   │   ├── __init__.py
│   │   │   ├── password_hasher.py
│   │   │   ├── quota_checker.py
│   │   │   ├── design_validator.py
│   │   │   └── permission_checker.py
│   │   │
│   │   └── exceptions.py          # Domain exceptions
│   │
│   ├── application/               # ⭐ USE CASES (Business logic)
│   │   ├── __init__.py
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── auth/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── register_user.py
│   │   │   │   ├── login_user.py
│   │   │   │   ├── refresh_token.py
│   │   │   │   ├── logout_user.py
│   │   │   │   └── reset_password.py
│   │   │   │
│   │   │   ├── designs/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── create_design.py
│   │   │   │   ├── get_design.py
│   │   │   │   ├── list_designs.py
│   │   │   │   ├── update_design.py
│   │   │   │   ├── delete_design.py
│   │   │   │   └── duplicate_design.py
│   │   │   │
│   │   │   ├── users/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── get_profile.py
│   │   │   │   ├── update_profile.py
│   │   │   │   └── delete_account.py
│   │   │   │
│   │   │   └── subscriptions/
│   │   │       ├── __init__.py
│   │   │       ├── get_subscription.py
│   │   │       ├── get_usage.py
│   │   │       └── check_quota.py
│   │   │
│   │   └── dto/                   # Data Transfer Objects
│   │       ├── __init__.py
│   │       ├── user_dto.py
│   │       ├── design_dto.py
│   │       └── subscription_dto.py
│   │
│   ├── infrastructure/            # ⭐ EXTERNAL INTEGRATIONS
│   │   ├── __init__.py
│   │   │
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── models/            # SQLAlchemy models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── user_model.py
│   │   │   │   ├── design_model.py
│   │   │   │   ├── subscription_model.py
│   │   │   │   └── order_model.py
│   │   │   │
│   │   │   ├── repositories/      # Repository implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user_repo_impl.py
│   │   │   │   ├── design_repo_impl.py
│   │   │   │   └── subscription_repo_impl.py
│   │   │   │
│   │   │   ├── session.py         # DB session factory
│   │   │   └── migrations/        # Alembic migrations
│   │   │       ├── env.py
│   │   │       ├── script.py.mako
│   │   │       └── versions/
│   │   │
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   ├── redis_client.py
│   │   │   └── cache_service.py
│   │   │
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   └── s3_client.py
│   │   │
│   │   ├── queue/
│   │   │   ├── __init__.py
│   │   │   └── sqs_client.py
│   │   │
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── openai_client.py
│   │   │   └── pinecone_client.py
│   │   │
│   │   └── integrations/
│   │       ├── __init__.py
│   │       ├── shopify/
│   │       │   └── client.py
│   │       └── stripe/
│   │           └── client.py
│   │
│   ├── presentation/              # ⭐ API LAYER (HTTP)
│   │   ├── __init__.py
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py      # Main router
│   │   │       │
│   │   │       ├── endpoints/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── health.py
│   │   │       │   ├── auth.py
│   │   │       │   ├── designs.py
│   │   │       │   ├── users.py
│   │   │       │   └── subscriptions.py
│   │   │       │
│   │   │       └── dependencies.py  # FastAPI dependencies
│   │   │
│   │   ├── schemas/               # Pydantic request/response
│   │   │   ├── __init__.py
│   │   │   ├── auth_schema.py
│   │   │   ├── design_schema.py
│   │   │   ├── user_schema.py
│   │   │   └── subscription_schema.py
│   │   │
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── auth_middleware.py
│   │       ├── rate_limit.py
│   │       ├── error_handler.py
│   │       ├── cors.py
│   │       └── logging_middleware.py
│   │
│   └── shared/                    # ⭐ SHARED UTILITIES
│       ├── __init__.py
│       ├── exceptions.py          # Custom exceptions
│       ├── constants.py
│       ├── enums.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── logger.py
│       │   ├── security.py
│       │   ├── validators.py
│       │   └── datetime_helpers.py
│       └── types.py               # Custom types
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures globales
│   │
│   ├── unit/                      # Fast, isolated, no external deps
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── test_entities.py
│   │   │   ├── test_value_objects.py
│   │   │   └── test_services.py
│   │   ├── application/
│   │   │   └── test_use_cases.py
│   │   └── shared/
│   │       └── test_utils.py
│   │
│   ├── integration/               # With real DB, Redis (testcontainers)
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── database/
│   │   │   └── test_repositories.py
│   │   ├── cache/
│   │   │   └── test_redis.py
│   │   └── api/
│   │       ├── test_auth_endpoints.py
│   │       └── test_design_endpoints.py
│   │
│   ├── e2e/                       # Full API flows
│   │   ├── __init__.py
│   │   └── test_user_journey.py
│   │
│   └── fixtures/                  # Test data factories
│       ├── __init__.py
│       ├── user_factory.py
│       └── design_factory.py
│
├── scripts/
│   ├── seed_db.py                 # Populate dev DB with test data
│   ├── run_migrations.py          # Helper script for Alembic
│   ├── generate_test_data.py
│   └── check_health.py            # Health check script
│
├── deployment/
│   ├── Dockerfile                 # Production (multi-stage)
│   ├── Dockerfile.dev             # Development (hot reload)
│   ├── docker-compose.yml         # Local dev stack
│   ├── docker-compose.test.yml    # CI testing
│   ├── .dockerignore
│   └── kubernetes/                # K8s manifests (futuro)
│       └── deployment.yaml
│
├── docs/
│   ├── architecture/
│   │   ├── decisions/             # ADRs
│   │   │   ├── 001-fastapi-framework.md
│   │   │   ├── 002-clean-architecture.md
│   │   │   ├── 003-async-by-default.md
│   │   │   └── 004-jwt-authentication.md
│   │   ├── diagrams/
│   │   │   ├── architecture.mmd
│   │   │   └── data-flow.mmd
│   │   └── README.md
│   ├── api/
│   │   └── openapi.yaml           # Auto-generated
│   └── development/
│       ├── setup.md
│       └── contributing.md
│
├── .env.example                   # Template environment vars
├── .gitignore
├── .dockerignore
├── requirements.txt               # Production deps (pinned)
├── requirements-dev.txt           # Dev deps (testing, linting)
├── pyproject.toml                 # Python project config
├── pytest.ini                     # Pytest config
├── alembic.ini                    # Alembic config
├── mypy.ini                       # Mypy type checking config
├── .ruff.toml                     # Ruff linter config
├── README.md                      # Este archivo
└── LICENSE                        # MIT
```

---

## 🎯 Principios Arquitectónicos

### 1. Clean Architecture (Uncle Bob)
```
┌─────────────────────────────────────────┐
│           PRESENTATION                  │ ← FastAPI endpoints
│  (Controllers, Schemas, Middleware)     │
└────────────────┬────────────────────────┘
                 │ depends on
┌────────────────▼────────────────────────┐
│          APPLICATION                     │ ← Use Cases
│     (Business Logic Orchestration)      │
└────────────────┬────────────────────────┘
                 │ depends on
┌────────────────▼────────────────────────┐
│             DOMAIN                       │ ← Entities, Value Objects
│       (Core Business Rules)             │    ← No dependencies externas
└────────────────▲────────────────────────┘
                 │ implemented by
┌────────────────┴────────────────────────┐
│        INFRASTRUCTURE                    │ ← DB, Redis, S3, APIs
│    (External Systems, Frameworks)       │
└──────────────────────────────────────────┘
```

**Regla fundamental:** Las dependencias apuntan HACIA ADENTRO.
- Domain NO conoce Infrastructure
- Application NO conoce Presentation
- Infrastructure implementa interfaces definidas en Domain

### 2. Dependency Inversion
```python
# CORRECTO ✅
# Domain define la interface
class IDesignRepository(ABC):
    @abstractmethod
    async def create(self, design: Design) -> Design:
        pass

# Infrastructure implementa
class DesignRepositoryImpl(IDesignRepository):
    async def create(self, design: Design) -> Design:
        # SQLAlchemy implementation
        pass

# Use Case depende de la abstracción
class CreateDesignUseCase:
    def __init__(self, design_repo: IDesignRepository):
        self.design_repo = design_repo
```

### 3. Single Responsibility

Cada módulo/clase tiene UNA responsabilidad:
- `CreateDesignUseCase`: Solo crear diseño
- `DesignRepository`: Solo persistencia designs
- `DesignValidator`: Solo validar designs

### 4. Async by Default
```python
# CORRECTO ✅
async def create_design(data: dict) -> Design:
    async with get_db_session() as session:
        design = await session.execute(...)
        return design

# INCORRECTO ❌ (bloquea event loop)
def create_design_sync(data: dict) -> Design:
    with get_db_session() as session:  # Blocking!
        design = session.execute(...)
        return design
```

**Regla:** TODO I/O debe ser async (DB, Redis, HTTP, File I/O)

### 5. Fail Fast
```python
# Validar inputs inmediatamente
async def create_design(user_id: str, data: dict):
    # Fail fast checks
    if not user_id:
        raise ValueError("user_id required")
    
    user = await user_repo.get(user_id)
    if not user:
        raise UserNotFoundError(user_id)
    
    if not user.subscription.is_active:
        raise InactiveSubscriptionError()
    
    # Now do the work
    design = await design_repo.create(...)
```

---

## 📚 Documentos Relacionados

**En esta carpeta:**
- [ARQUITECTURA.md](./ARQUITECTURA.md) - Decisiones arquitectónicas detalladas
- [TECNOLOGIAS.md](./TECNOLOGIAS.md) - Stack completo con configuración
- [DESARROLLO.md](./DESARROLLO.md) - Setup, workflow, convenciones
- [TESTING.md](./TESTING.md) - Estrategia testing, fixtures, coverage
- [DEPLOY.md](./DEPLOY.md) - Docker, AWS ECS, CI/CD
- [PROMPTS_IA.md](./PROMPTS_IA.md) - Guías para Claude, Copilot, Cursor
- [DAILY-LOG.md](./DAILY-LOG.md) - Tu tracking diario

**Otras carpetas:**
- [../08-database/](../08-database/) - Schema PostgreSQL, migrations
- [../09-cache-layer/](../09-cache-layer/) - Redis configuration
- [../02-ai-services/](../02-ai-services/) - OpenAI integration

**External:**
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Pydantic V2 Migration](https://docs.pydantic.dev/latest/migration/)
- [Clean Architecture Blog](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## 🚀 Próximos Pasos

### Si eres nuevo en el proyecto:

1. ✅ Lee este README completo
2. 📖 Lee [ARQUITECTURA.md](./ARQUITECTURA.md) para entender diseño
3. 🛠️ Lee [TECNOLOGIAS.md](./TECNOLOGIAS.md) para entender stack
4. 💻 Sigue [DESARROLLO.md](./DESARROLLO.md) para setup
5. 🤖 Configura tu IA con [PROMPTS_IA.md](./PROMPTS_IA.md)
6. ✍️ Empieza tu [DAILY-LOG.md](./DAILY-LOG.md)

### Si ya estás desarrollando:

1. Abre [DAILY-LOG.md](./DAILY-LOG.md) de ayer
2. Resume a tu agente IA donde quedaste
3. Continúa con tus pending tasks

---

## 💬 Soporte

**Dudas técnicas:** alicia@customify.app  
**Issues:** https://github.com/customify/core-api/issues  
**Slack:** #backend-core-api  
**Daily Standup:** 9:00 AM async (Slack)

---

## 📊 Status del Componente

**Última actualización:** [Fecha]

| Feature | Status | Coverage | Notes |
|---------|--------|----------|-------|
| Health Check | ✅ Done | 100% | |
| Authentication | 🔄 In Progress | 85% | Falta refresh token |
| Designs CRUD | ⏳ Pending | 0% | Start semana 2 |
| Subscriptions | ⏳ Pending | 0% | Start semana 2 |
| Rate Limiting | ⏳ Pending | 0% | Start semana 2 |

**Overall Progress:** 15% complete

---

**Construyamos el backend más sólido para Customify.** 🚀