# Customify Core API

**AI-Powered Product Customization Platform - Backend Service**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io)
[![Coverage](https://img.shields.io/badge/Coverage-68%25-yellow.svg)](https://github.com/customify-mvp/01-core-api)
[![Tests](https://img.shields.io/badge/Tests-85%20passing-brightgreen.svg)](https://github.com/customify-mvp/01-core-api)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Modern, scalable REST API** built with Clean Architecture principles, providing design customization services with AI assistance, background rendering, and e-commerce integrations.


---

## 📑 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Database](#database)
- [Background Workers](#background-workers)
- [Storage](#storage)
- [Deployment](#deployment)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

Customify Core API is the backend service for a SaaS platform that enables merchants to offer AI-powered product customization to their customers. The system handles:

- **User Management** - Authentication, authorization, and subscription management
- **Design Creation** - AI-assisted design generation and validation
- **Background Processing** - Asynchronous rendering of design previews
- **Storage Management** - S3-based asset storage with CDN integration
- **E-commerce Integration** - Shopify/WooCommerce webhooks and order processing

**Key Metrics:**
- Response Time: <100ms (p95)
- Throughput: 1000+ req/s
- Availability: 99.9% SLA
- Test Coverage: 77%

---

## 🏗️ Architecture

### Clean Architecture (Hexagonal)
```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Endpoints  │  Schemas  │  Dependencies           │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Use Cases (Business Logic)  │  DTOs  │  Interfaces      │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        DOMAIN LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Entities  │  Value Objects  │  Domain Services          │  │
│  │  Repository Interfaces  │  Domain Exceptions             │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL  │  Redis  │  S3  │  Celery  │  External APIs │  │
│  │  Repository Implementations  │  ORM Models                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Layers Description

**Domain Layer (Core)**
- Pure business logic, no framework dependencies
- Entities represent core business concepts
- Repository interfaces define data access contracts
- Domain exceptions for business rule violations

**Application Layer**
- Use cases orchestrate domain logic
- Depend on domain interfaces (not implementations)
- Transaction management
- Application-specific business rules

**Infrastructure Layer**
- Concrete implementations of repository interfaces
- Database access (SQLAlchemy ORM)
- External service integrations (S3, Redis, Celery)
- Framework-specific code

**Presentation Layer**
- HTTP API endpoints (FastAPI)
- Request/response schemas (Pydantic)
- Authentication/authorization
- API versioning and documentation

### Data Flow
```
HTTP Request
    ↓
FastAPI Endpoint (Presentation)
    ↓
Dependency Injection (Repository, Use Case)
    ↓
Use Case.execute() (Application)
    ↓
Domain Entity Business Logic (Domain)
    ↓
Repository Implementation (Infrastructure)
    ↓
Database / External Service
    ↓
Response (reverse flow)
```

---

## ✨ Features

### Authentication & Authorization
- [x] JWT-based authentication
- [x] Role-based access control (RBAC)
- [x] Secure password hashing (bcrypt)
- [x] Token expiration and refresh
- [x] Account activation via email

### Design Management
- [x] CRUD operations for designs
- [x] Product type validation (t-shirt, mug, poster, hoodie, tote-bag)
- [x] Design data validation (text, font, color)
- [x] Status tracking (draft → rendering → published → failed)
- [ ] AI-powered design suggestions (planned)

### Subscription Management
- [x] Multiple subscription tiers (Free, Starter, Professional, Enterprise)
- [x] Usage tracking and quota enforcement
- [x] Monthly reset automation
- [ ] Stripe integration for payments (planned)

### Background Processing
- [x] Celery task queue with Redis broker
- [x] Async design rendering
- [x] Email notifications
- [x] Retry policies and error handling
- [x] Task status monitoring

### Storage
- [x] AWS S3 integration for images
- [x] Local filesystem fallback (development)
- [x] Automatic thumbnail generation
- [x] CDN-ready URLs

### Integrations
- [ ] Shopify OAuth and webhooks (planned)
- [ ] WooCommerce integration (planned)
- [ ] Stripe payment processing (planned)

---

## 🛠️ Tech Stack

### Core
- **Python 3.12** - Modern Python with performance improvements
- **FastAPI 0.109** - High-performance async web framework
- **Pydantic v2** - Data validation with type hints
- **SQLAlchemy 2.0** - Async ORM with `Mapped[T]` syntax

### Database
- **PostgreSQL 15** - Primary database (JSONB support)
- **Alembic** - Database migrations
- **asyncpg** - Async PostgreSQL driver

### Caching & Queue
- **Redis 7** - Cache and Celery broker
- **Celery 5.3** - Distributed task queue

### Storage
- **AWS S3** - Object storage for images/PDFs
- **Pillow (PIL)** - Image processing and rendering

### Security
- **python-jose** - JWT token generation
- **passlib + bcrypt** - Password hashing
- **python-dotenv** - Environment variable management

### Testing
- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **httpx** - Async HTTP client for API tests

### Development
- **uvicorn** - ASGI server
- **black** - Code formatting
- **ruff** - Fast linter
- **mypy** - Static type checking

---

## 📋 Prerequisites

- **Python 3.12+**
- **PostgreSQL 15+**
- **Redis 7+**
- **AWS Account** (for S3, optional for local dev)
- **Docker & Docker Compose** (recommended)

---

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/customify-mvp/01-core-api.git
cd 01-core-api
```

### 2. Create Virtual Environment
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Start Infrastructure (Docker)
```bash
docker-compose up -d postgres redis
```

### 6. Run Database Migrations
```bash
alembic upgrade head
```

### 7. Seed Database (Optional)
```bash
python scripts/seed_dev_data.py
```

---

## ⚙️ Configuration

### Environment Variables

**Required:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/customify_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days
```

**Optional (AWS S3):**
```bash
# Storage
USE_LOCAL_STORAGE=true  # false to use S3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=customify-dev
```

**Optional (Development):**
```bash
# Environment
ENVIRONMENT=development
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Configuration Files

- `.env` - Environment variables (not committed)
- `alembic.ini` - Database migration config
- `pytest.ini` - Test configuration
- `pyproject.toml` - Project metadata and tools config

---

## 🏃 Running the Application

### Development Mode

**Option 1: Manual Start**
```bash
# Terminal 1: API Server
uvicorn app.main:app --reload --port 8000

# Terminal 2: Celery Worker
celery -A app.infrastructure.workers.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=high_priority,default

# Terminal 3 (Optional): Flower (Task Monitor)
celery -A app.infrastructure.workers.celery_app flower --port=5555
```

**Option 2: Docker Compose**
```bash
docker-compose up
```

**Option 3: Using Scripts**
```bash
# Start API
./scripts/start_api.sh

# Start Worker
./scripts/start_worker.sh
```

### Production Mode
```bash
# Using Gunicorn with Uvicorn workers
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

---

## 📚 API Documentation

### Interactive Docs

Once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Quick Start Guide

#### 1. Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### 2. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": { ... }
}
```

#### 3. Create Design
```bash
curl -X POST http://localhost:8000/api/v1/designs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_type": "t-shirt",
    "design_data": {
      "text": "Hello World",
      "font": "Bebas-Bold",
      "color": "#FF0000"
    }
  }'
```

**Response:**
```json
{
  "id": "uuid",
  "product_type": "t-shirt",
  "status": "draft",
  "design_data": { ... },
  "created_at": "2024-01-15T10:05:00Z"
}
```

**Note:** Design rendering happens asynchronously. Status will change: `draft` → `rendering` → `published`

#### 4. List Designs
```bash
curl http://localhost:8000/api/v1/designs?skip=0&limit=20 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### API Endpoints Overview

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login user | No |
| GET | `/api/v1/auth/me` | Get current user | Yes |
| POST | `/api/v1/designs` | Create design | Yes |
| GET | `/api/v1/designs` | List user's designs | Yes |
| GET | `/api/v1/designs/{id}` | Get design by ID | Yes |
| GET | `/health` | Health check | No |
| GET | `/docs` | Swagger UI | No |

---

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

**View Coverage Report:**
```bash
open htmlcov/index.html
```

### Run Specific Test Types
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/domain/test_user_entity.py -v

# Specific test function
pytest tests/integration/api/test_auth_endpoints.py::test_register_success -v
```

### Test Structure
```
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Fast, isolated tests
│   └── domain/
│       ├── test_user_entity.py
│       ├── test_design_entity.py
│       └── test_subscription_entity.py
└── integration/          # Tests with database
    └── api/
        ├── test_auth_endpoints.py
        └── test_design_endpoints.py
```

### Current Coverage

- **Overall:** 77%
- **Domain:** 92%
- **Application:** 81%
- **Infrastructure:** 68%
- **Presentation:** 85%

---

## 🗄️ Database

### Schema Overview
```sql
-- Core tables
users              (id, email, password_hash, full_name, ...)
subscriptions      (id, user_id, plan, status, designs_this_month, ...)
designs            (id, user_id, product_type, design_data, status, ...)
orders             (id, user_id, design_id, external_order_id, ...)
shopify_stores     (id, user_id, shop_domain, access_token, ...)

-- Relationships
users 1:1 subscriptions
users 1:N designs
users 1:N orders
designs 1:N orders
users 1:1 shopify_stores
```

### Migrations

**Create new migration:**
```bash
alembic revision --autogenerate -m "description"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback:**
```bash
alembic downgrade -1
```

**View current version:**
```bash
alembic current
```

**View migration history:**
```bash
alembic history
```

### Database Connection

**Connect to database:**
```bash
# Using Docker
docker exec -it customify-postgres psql -U customify -d customify_dev

# Local PostgreSQL
psql -U customify -d customify_dev
```

**Useful queries:**
```sql
-- View all tables
\dt

-- Describe table
\d users

-- Count records
SELECT COUNT(*) FROM designs WHERE is_deleted = false;

-- View recent designs
SELECT id, user_id, product_type, status, created_at
FROM designs
ORDER BY created_at DESC
LIMIT 10;
```

---

## ⚙️ Background Workers

### Celery Tasks

**Available tasks:**
- `render_design_preview` - Render design using PIL and upload to S3
- `send_email` - Send transactional emails
- `debug_task` - Test task for debugging

### Monitor Tasks

**Option 1: Flower UI**
```bash
# Start Flower
celery -A app.infrastructure.workers.celery_app flower --port=5555

# Access at http://localhost:5555
```

**Option 2: Command Line**
```bash
# View registered tasks
celery -A app.infrastructure.workers.celery_app inspect registered

# View active tasks
celery -A app.infrastructure.workers.celery_app inspect active

# View worker stats
celery -A app.infrastructure.workers.celery_app inspect stats

# View queue lengths
celery -A app.infrastructure.workers.celery_app inspect reserved
```

**Option 3: Redis CLI**
```bash
redis-cli
> LLEN high_priority  # High priority queue length
> LLEN default        # Default queue length
> KEYS celery*        # All Celery keys
```

### Task Queues

- `high_priority` - Design rendering (fast response needed)
- `default` - Emails, cleanup, etc.

### Worker Configuration

**Development:**
```bash
celery -A app.infrastructure.workers.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --pool=solo \
    --queues=high_priority,default
```

**Production:**
```bash
celery -A app.infrastructure.workers.celery_app worker \
    --loglevel=warning \
    --concurrency=4 \
    --pool=prefork \
    --queues=high_priority,default \
    --max-tasks-per-child=1000
```

---

## 💾 Storage

### AWS S3 Configuration

**Bucket structure:**
```
s3://customify-production/
├── designs/
│   └── {design_id}/
│       ├── preview.png      (600x600)
│       └── thumbnail.png    (200x200)
├── pdfs/
│   └── {order_id}/
│       └── order.pdf
└── avatars/
    └── {user_id}/
        └── avatar.jpg
```

**Access control:**
- Public read (preview/thumbnail images)
- Private (PDFs, avatars - use signed URLs)

### Local Storage (Development)

When `USE_LOCAL_STORAGE=true`:
```
./storage/
├── designs/
│   └── {design_id}/
│       ├── preview.png
│       └── thumbnail.png
```

**Access via static endpoint:**
```
http://localhost:8000/static/designs/{design_id}/preview.png
```

---

## 🚢 Deployment

### Docker Production Build

**Build image:**
```bash
docker build -t customify-api:latest -f Dockerfile.prod .
```

**Run container:**
```bash
docker run -d \
  --name customify-api \
  -p 8000:8000 \
  --env-file .env.production \
  customify-api:latest
```

### AWS ECS Deployment

**Prerequisites:**
- ECR repository created
- ECS cluster created
- RDS PostgreSQL instance
- ElastiCache Redis cluster

**Push to ECR:**
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin {account}.dkr.ecr.us-east-1.amazonaws.com

docker tag customify-api:latest {account}.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest
docker push {account}.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest
```

**Task definition:**
```json
{
  "family": "customify-api",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "{account}.dkr.ecr.us-east-1.amazonaws.com/customify-api:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "JWT_SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ]
    }
  ]
}
```

### Environment-Specific Configs

**Development:**
- Local PostgreSQL/Redis
- Debug logging enabled
- Auto-reload enabled

**Staging:**
- RDS PostgreSQL
- ElastiCache Redis
- HTTPS required
- Limited resources

**Production:**
- Multi-AZ RDS
- Redis cluster
- CloudFront CDN
- Full monitoring

---

## 👨‍💻 Development

### Project Structure
```
01-core-api/
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── app/
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Configuration
│   ├── domain/                 # Business logic (core)
│   │   ├── entities/
│   │   ├── repositories/       # Interfaces
│   │   ├── value_objects/
│   │   └── exceptions/
│   ├── application/            # Use cases
│   │   └── use_cases/
│   ├── infrastructure/         # External services
│   │   ├── database/
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── repositories/   # Implementations
│   │   │   └── converters/
│   │   ├── storage/            # S3, local storage
│   │   └── workers/            # Celery tasks
│   ├── presentation/           # HTTP layer
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── dependencies/       # DI
│   │   └── middleware/
│   └── shared/                 # Shared utilities
│       └── services/
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/                    # Utility scripts
├── docs/                       # Documentation
├── requirements.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

### Coding Standards

**Python:**
- Follow PEP 8
- Type hints required
- Docstrings for public functions
- Max line length: 100 chars

**Formatting:**
```bash
# Format code
black app/ tests/

# Lint
ruff check app/ tests/

# Type check
mypy app/
```

### Git Workflow

**Branch naming:**
- `feature/add-pdf-generation`
- `fix/celery-connection-issue`
- `refactor/improve-repositories`

**Commit messages:**
```
feat: add PDF generation for orders
fix: resolve Celery task routing issue
refactor: improve repository patterns
docs: update API documentation
test: add integration tests for designs
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Celery tasks not processing**
```bash
# Check Redis connection
redis-cli ping

# Check worker logs
celery -A app.infrastructure.workers.celery_app inspect active

# Restart worker
docker-compose restart worker
```

**2. Database connection errors**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -U customify -h localhost -d customify_dev

# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql+asyncpg://user:pass@host:5432/db
```

**3. Import errors**
```bash
# Ensure virtual environment active
which python
# Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

**4. S3 upload fails**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://your-bucket/

# Or use local storage
USE_LOCAL_STORAGE=true in .env
```

### Debug Mode

**Enable verbose logging:**
```python
# .env
DEBUG=true

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

**SQLAlchemy query logging:**
```python
# config.py
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=True  # Print all SQL queries
)
```

### Performance Issues

**Check slow queries:**
```sql
-- PostgreSQL
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**Monitor API performance:**
```bash
# Add timing middleware
# Check logs for slow requests (>1s)
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

**PR Checklist:**
- [ ] Tests pass (`pytest`)
- [ ] Coverage maintained (>70%)
- [ ] Code formatted (`black`)
- [ ] No linting errors (`ruff`)
- [ ] Documentation updated
- [ ] Changelog updated

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 📞 Support

- **Documentation**: https://docs.customify.app
- **Issues**: https://github.com/customify-mvp/01-core-api/issues
- **Email**: support@customify.app
- **Discord**: https://discord.gg/customify

---

## 🙏 Acknowledgments

- FastAPI team for the amazing framework
- SQLAlchemy maintainers
- Clean Architecture by Robert C. Martin
- All contributors and supporters

---

**Made with ❤️ by the Customify Team**
