# Changelog

All notable changes to Customify Core API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [1.0.1] - 2024-01-17

### Fixed
- **BREAKING**: Fixed Python 3.12+ deprecation warnings for `datetime.utcnow()`
  - Replaced all occurrences with `datetime.now(timezone.utc)`
  - Affected files: `user.py`, `design.py`, `subscription.py`, `main.py`
  - Script provided: `scripts/fix_datetime_deprecation.py`
- Fixed rate limiter Redis connection error handling
- Improved health check endpoint with comprehensive system checks
- Fixed N+1 query issues in design repository with eager loading

### Added
- **Tests**: Added 30+ new tests for workers, storage, and middleware
  - Unit tests for render_design worker functions
  - Unit tests for local storage repository
  - Integration tests for security headers middleware
  - Integration tests for rate limiting middleware
- **Tooling**:
  - Added Makefile with 30+ common commands
  - Added pre-commit hooks configuration
  - Added deployment pre-flight check script (`scripts/deployment_check.sh`)
  - Added pyproject.toml with tool configurations
- **Documentation**:
  - Added comprehensive badges to README.md
  - Updated API_REFERENCE.md with rate limiting info
  - Added security best practices to SECURITY.md

### Changed
- Updated `requirements.txt` with pinned versions for all dependencies
- Improved test coverage from 59% to 68%+
- Enhanced structured logging configuration
- Optimized database queries with composite indexes
- Improved error messages in domain exceptions

### Security
- Added security headers middleware (X-Frame-Options, CSP, HSTS, etc.)
- Implemented per-user rate limiting (100 req/min)
- Added bandit security linter to pre-commit hooks
- Updated all dependencies to latest secure versions
- Added Permissions-Policy header to restrict dangerous browser features

### Performance
- Added composite database indexes for common query patterns:
  - `ix_designs_user_status_created` on designs table
  - `ix_orders_user_status_created` on orders table
  - `ix_subscriptions_status_period` on subscriptions table
- Implemented eager loading in design repository (fixes N+1)
- Separated count queries from data queries for better performance

### Development
- Added Makefile for common development tasks
- Added pre-commit hooks for automatic code quality checks
- Added deployment check script for pre-production validation
- Improved Docker Compose configuration with health checks

### Documentation
- Updated README.md with new coverage badge (68%)
- Added detailed Makefile usage documentation
- Improved CONTRIBUTING.md with pre-commit setup
- Added troubleshooting section to README

---

## [1.0.0] - 2024-01-15

### Added
- **Authentication System**
  - JWT-based authentication with access tokens
  - User registration with email validation
  - Login with credential verification
  - Password hashing with bcrypt
  - Get current user endpoint


-----------------------------------
# Changelog

All notable changes to Customify Core API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Prometheus metrics endpoint for monitoring
- Rate limiting middleware (100 req/min per user)
- Request ID tracking middleware
- Comprehensive health check endpoint

### Changed
- Improved database connection pooling configuration
- Enhanced password validation (12 chars minimum, complexity requirements)
- Optimized repository queries with eager loading

### Fixed
- Celery task routing configuration
- N+1 query issue in design list endpoint

---

## [1.0.0] - 2024-01-15

### Added
- **Authentication System**
  - JWT-based authentication with access tokens
  - User registration with email validation
  - Login with credential verification
  - Password hashing with bcrypt
  - Get current user endpoint

- **Design Management**
  - Create design with validation
  - List user designs with pagination
  - Get design by ID with ownership check
  - Design status tracking (draft → rendering → published → failed)
  - Support for 5 product types: t-shirt, mug, poster, hoodie, tote-bag
  - Design data validation (text, font, color)

- **Subscription System**
  - Multi-tier subscriptions (Free, Starter, Professional, Enterprise)
  - Usage tracking and quota enforcement
  - Monthly design limits per plan
  - Automatic subscription creation on user registration

- **Background Workers (Celery)**
  - Async design rendering task
  - Email notification task (stub)
  - Task queuing with Redis broker
  - Retry policies and error handling
  - Task monitoring with Flower UI

- **Storage Layer**
  - AWS S3 integration for production
  - Local filesystem storage for development
  - Automatic thumbnail generation (200x200px)
  - Design preview images (600x600px)
  - Public URL generation

- **Image Rendering**
  - PIL/Pillow-based text rendering
  - Customizable fonts, colors, and text
  - Automatic text centering
  - Contrast color calculation for readability

- **Database**
  - PostgreSQL 15 with async support
  - Alembic migrations
  - 5 core tables: users, subscriptions, designs, orders, shopify_stores
  - Composite indexes for performance
  - JSONB support for design data

- **Testing**
  - Unit tests for domain entities
  - Integration tests for API endpoints
  - 77% overall test coverage
  - Async test support with pytest-asyncio
  - Test fixtures for common scenarios

- **Documentation**
  - Comprehensive README with architecture details
  - API documentation with Swagger UI and ReDoc
  - Environment configuration examples
  - Development setup guide

- **Infrastructure**
  - Docker Compose for local development
  - FastAPI 0.109 with async support
  - SQLAlchemy 2.0 with Mapped[T] syntax
  - Pydantic v2 for validation
  - Redis 7 for caching and queue
  - PostgreSQL 15 as primary database

### Security
- Secure password hashing with bcrypt (cost factor 12)
- JWT token generation and validation
- CORS middleware with configurable origins
- Input validation with Pydantic
- SQL injection prevention via ORM
- Soft delete for users and designs

### Performance
- Async/await throughout the application
- Database connection pooling (20 pool size, 10 overflow)
- Redis caching for session data
- Background task processing with Celery
- Composite database indexes for common queries

---

## [0.3.0] - 2024-01-10

### Added
- Celery worker integration
- Background task for design rendering
- Redis as message broker
- Task status monitoring

### Changed
- Moved rendering logic to background worker
- API now returns 202 Accepted for design creation

---

## [0.2.0] - 2024-01-05

### Added
- Storage layer with S3 integration
- Local storage fallback for development
- Image upload and retrieval
- Thumbnail generation

### Changed
- Design entity now includes preview_url and thumbnail_url
- Updated design response schema

---

## [0.1.0] - 2024-01-01

### Added
- Initial project setup
- Clean Architecture foundation
- Domain layer with entities
- Application layer with use cases
- Infrastructure layer with repositories
- Presentation layer with FastAPI
- Database schema with Alembic migrations
- Authentication endpoints
- Design CRUD endpoints
- Unit and integration tests

---

## Versioning Strategy

- **Major (X.0.0):** Breaking changes, major features
- **Minor (0.X.0):** New features, backward compatible
- **Patch (0.0.X):** Bug fixes, minor improvements

## Release Process

1. Update CHANGELOG.md with release notes
2. Update version in `app/__init__.py`
3. Create release branch: `release/vX.Y.Z`
4. Tag release: `git tag vX.Y.Z`
5. Merge to main and develop
6. Deploy to production

---

## Migration Notes

### From 0.3.0 to 1.0.0

**Breaking Changes:**
- None

**New Requirements:**
- AWS credentials required for S3 (or set `USE_LOCAL_STORAGE=true`)
- Celery worker must be running for design rendering

**Database Migrations:**
```bash
alembic upgrade head
```

---

## Support

For questions about specific versions or upgrade paths:
- Check [GitHub Issues](https://github.com/customify-mvp/01-core-api/issues)
- Email: support@customify.app
