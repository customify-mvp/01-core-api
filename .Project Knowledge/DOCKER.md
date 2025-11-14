# Docker Guide - Core API

**Propósito:** Referencia completa Docker para este componente

---

## 📋 Archivos Docker

### 1. Dockerfile (Production)
```dockerfile
# Dockerfile

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages to /install
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Production ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 2. Dockerfile.dev (Development)
```dockerfile
# Dockerfile.dev

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install all dependencies (including dev)
RUN pip install --no-cache-dir \
    -r requirements.txt \
    -r requirements-dev.txt

# Install debugpy for VS Code debugging
RUN pip install debugpy

# Copy code (will be overridden by volume mount)
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000
EXPOSE 5678

# Development server with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 3. .dockerignore
```
# .dockerignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Git
.git/
.gitignore

# Docker
Dockerfile*
docker-compose*.yml
.dockerignore

# Docs
docs/
*.md
README*

# Environment
.env
.env.local
.env.*.local

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temp
tmp/
temp/
```

---

## 🔧 docker-compose Profiles

### Basic (solo API)
```bash
docker-compose up -d
# Levanta: api, postgres, redis
```

### With Tools
```bash
docker-compose --profile tools up -d
# Levanta: api, postgres, redis, pgadmin, redis-commander
```

### Production-like
```bash
docker-compose -f docker-compose.prod.yml up -d
# Usa Dockerfile (no Dockerfile.dev)
# Sin hot reload
# Multiple workers
```

---

## 🎯 Build Strategies

### Development (Fast iteration)
```bash
# Build dev image
docker-compose build api

# Build sin cache (si hay issues)
docker-compose build --no-cache api

# Build con progress
docker-compose build --progress=plain api
```

### Production (Optimized)
```bash
# Build production image
docker build -t customify-api:1.0.0 -f Dockerfile .

# Multi-platform (ARM + AMD)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t customify-api:1.0.0 \
  -f Dockerfile .

# With build args
docker build \
  --build-arg PYTHON_VERSION=3.12 \
  -t customify-api:1.0.0 \
  -f Dockerfile .
```

---

## 📊 Image Size Optimization

### Current Size
```bash
# Check image size
docker images customify-api

# Expected:
# Development: ~1.2GB (con dev deps)
# Production: ~200MB (multi-stage, sin dev deps)
```

### Optimization Techniques

**1. Multi-stage build** ✅
```dockerfile
FROM python:3.12-slim AS builder  # Build stage
FROM python:3.12-slim             # Runtime stage (smaller)
```

**2. Slim base image** ✅
```dockerfile
python:3.12-slim  # 50MB vs python:3.12 (1GB)
```

**3. Layer caching**
```dockerfile
# Copy requirements first (changes menos frecuentes)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code last (changes frecuentes)
COPY app/ ./app/
```

**4. Cleanup apt cache** ✅
```dockerfile
RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*  # ← Cleanup
```

---

## 🔐 Security Best Practices

### ✅ Implementadas
```dockerfile
# 1. Non-root user
USER appuser

# 2. Specific Python version (no 'latest')
FROM python:3.12-slim

# 3. Read-only volumes where possible
volumes:
  - ./app:/app/app:ro  # ← read-only

# 4. Health checks
HEALTHCHECK CMD curl -f http://localhost:8000/health

# 5. Minimal attack surface (slim image)
```

### 🔍 Security Scan
```bash
# Scan con Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image customify-api:latest

# Scan con Snyk
snyk container test customify-api:latest
```

---

## 🌐 Networking

### Default Network
```yaml
networks:
  customify-network:
    driver: bridge
```

**DNS interno:**
- `api` → Container API
- `postgres` → Container PostgreSQL
- `redis` → Container Redis

**Ejemplo:**
```python
# En código, usar nombres de servicio:
DATABASE_URL = "postgresql+asyncpg://user:pass@postgres:5432/db"
#                                              ^^^^^^^^
#                                              Nombre del servicio
```

### Port Mapping
```yaml
ports:
  - "8000:8000"  # Host:Container
  #  ^^^^  ^^^^
  #  Local  Container
```

**Acceso:**
- Desde local: `http://localhost:8000`
- Entre containers: `http://api:8000`

---

## 💾 Volumes

### Types

**1. Named volumes (persistent data)**
```yaml
volumes:
  postgres_data:  # ← Named volume
    driver: local

services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

**2. Bind mounts (development)**
```yaml
services:
  api:
    volumes:
      - ./app:/app/app:ro  # ← Bind mount
```

**3. Anonymous volumes (temp data)**
```yaml
services:
  api:
    volumes:
      - /app/__pycache__  # ← Anonymous (no persistir cache)
```

### Volume Management
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect core-api_postgres_data

# Backup volume
docker run --rm \
  -v core-api_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volume
docker run --rm \
  -v core-api_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /

# Delete volume (⚠️)
docker volume rm core-api_postgres_data
```

---

## 🚀 Performance Optimization

### MacOS Specific
```yaml
# Use :cached for better performance on MacOS
volumes:
  - ./app:/app/app:cached

# Or use docker-sync (más complejo)
```

### Memory Limits
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Build Cache
```bash
# Use BuildKit (faster builds)
export DOCKER_BUILDKIT=1
docker-compose build

# Enable BuildKit permanently
# ~/.docker/config.json
{
  "experimental": "enabled",
  "features": {
    "buildkit": true
  }
}
```

---

## 📋 Common Commands Reference
```bash
# ==================== BUILD ====================
docker-compose build                    # Build all services
docker-compose build api                # Build specific service
docker-compose build --no-cache         # Build from scratch

# ==================== UP/DOWN ====================
docker-compose up -d                    # Start detached
docker-compose up -d --build            # Rebuild and start
docker-compose down                     # Stop and remove
docker-compose down -v                  # Stop and remove volumes

# ==================== LOGS ====================
docker-compose logs -f api              # Follow logs
docker-compose logs --tail=100 api      # Last 100 lines
docker-compose logs --since 10m         # Last 10 minutes

# ==================== EXEC ====================
docker-compose exec api bash            # Interactive shell
docker-compose exec api python          # Python REPL
docker-compose exec api pytest          # Run tests
docker-compose exec postgres psql -U postgres  # psql

# ==================== RESTART ====================
docker-compose restart api              # Restart service
docker-compose restart                  # Restart all

# ==================== STATUS ====================
docker-compose ps                       # List containers
docker-compose top                      # Process list
docker stats                           # Resource usage

# ==================== CLEANUP ====================
docker-compose down --rmi all          # Remove images too
docker system prune -a --volumes       # Clean everything
docker volume prune                    # Remove unused volumes
```

---

## 🐛 Troubleshooting

### Issue: Container keeps restarting
```bash
# Check logs
docker-compose logs api

# Common causes:
# 1. Application crash → Fix code error
# 2. Port conflict → Change port in docker-compose.yml
# 3. Missing env var → Check .env file
# 4. DB not ready → Add depends_on with health check
```

### Issue: Cannot connect to DB
```bash
# Check DB is running
docker-compose ps postgres

# Check DB logs
docker-compose logs postgres

# Test connection from API container
docker-compose exec api bash
apt-get update && apt-get install -y postgresql-client
psql -h postgres -U postgres -d customify_dev

# Common fixes:
# 1. Wrong DATABASE_URL → Check .env
# 2. DB not healthy yet → Wait or check depends_on
# 3. Network issue → docker-compose down && up -d
```

### Issue: Hot reload not working
```bash
# Check volumes are mounted
docker-compose exec api ls -la /app/app

# Should see your files. If not:
# 1. Check docker-compose.yml volumes section
# 2. Restart containers: docker-compose restart api
# 3. On MacOS: try :cached flag
```

### Issue: Out of disk space
```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a --volumes

# Remove specific items
docker volume rm $(docker volume ls -q -f dangling=true)
docker image prune -a
```

---

## 📚 Resources

**Docker:**
- [Best practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Compose file reference](https://docs.docker.com/compose/compose-file/)

**FastAPI + Docker:**
- [Official guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Production deployment](https://fastapi.tiangolo.com/deployment/)

**Security:**
- [Docker security](https://docs.docker.com/engine/security/)
- [Snyk container scan](https://snyk.io/product/container-vulnerability-management/)