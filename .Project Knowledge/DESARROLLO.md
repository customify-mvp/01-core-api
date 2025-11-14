# Guía de Desarrollo - Core API

**IMPORTANTE:** Todo desarrollo se hace en Docker, NO localmente.

---

## 🐳 Prerequisitos ÚNICOS
```bash
# Solo necesitas:
✅ Docker Desktop 24+ (incluye Docker Compose)
✅ Git
✅ IDE (VS Code recomendado)

# NO necesitas:
❌ Python instalado localmente
❌ PostgreSQL local
❌ Redis local
❌ Ninguna dependency local
```

---

## ⚡ Setup Inicial (5 min)

### 1. Clone proyecto
```bash
git clone https://github.com/customify/core-api
cd core-api
```

### 2. Variables de entorno
```bash
cp .env.example .env
# Editar .env si necesario (defaults funcionan para desarrollo)
```

### 3. Levantar TODO en Docker
```bash
# Levanta: API + PostgreSQL + Redis
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Espera hasta ver: "Application startup complete"
```

### 4. Aplicar migrations
```bash
# Ejecutar dentro del container
docker-compose exec api alembic upgrade head
```

### 5. Verificar funcionamiento
```bash
# Health check
curl http://localhost:8000/health

# Docs interactivas
open http://localhost:8000/docs
```

**¡Listo!** API corriendo en Docker en `localhost:8000`

---

## 📁 Estructura Archivos Docker
```
core-api/
├── Dockerfile                 # Production image (multi-stage)
├── Dockerfile.dev             # Development image (hot reload)
├── docker-compose.yml         # Development stack
├── docker-compose.prod.yml    # Production stack (opcional)
├── .dockerignore              # Exclude files from image
├── .env.example               # Template env vars
└── .env                       # Tu config local (git-ignored)
```

---

## 🔨 Dockerfile.dev (Development con Hot Reload)
```dockerfile
# Dockerfile.dev

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy application code
# NOTE: En desarrollo usamos volume mount (ver docker-compose.yml)
# Por eso este COPY es para tener algo inicial, luego se sobrescribe
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Development server with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## 🐳 docker-compose.yml (Development)
```yaml
# docker-compose.yml

version: '3.9'

services:
  # ==========================================
  # API Service (FastAPI)
  # ==========================================
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: customify-api-dev
    ports:
      - "8000:8000"
    environment:
      # Database
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/customify_dev
      
      # Redis
      REDIS_URL: redis://redis:6379/0
      
      # App
      DEBUG: "true"
      ENVIRONMENT: development
      
      # JWT (development only - cambiar en prod)
      JWT_SECRET_KEY: dev-secret-key-change-in-production-min-32-chars
      
      # AWS (mock en desarrollo)
      AWS_REGION: us-east-1
      AWS_ACCESS_KEY_ID: test
      AWS_SECRET_ACCESS_KEY: test
      
      # OpenAI (usa tu key real o mock)
      OPENAI_API_KEY: ${OPENAI_API_KEY:-sk-test-key}
      
    volumes:
      # HOT RELOAD: Monta código local → container
      # Cualquier cambio en local → auto-reload en container
      - ./app:/app/app:ro                    # Read-only (seguridad)
      - ./tests:/app/tests:ro
      - ./alembic:/app/alembic:ro
      - ./alembic.ini:/app/alembic.ini:ro
      
      # Python cache (no montar - mejor performance)
      - /app/app/__pycache__
      
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    
    networks:
      - customify-network
    
    # Restart policy
    restart: unless-stopped
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 40s

  # ==========================================
  # PostgreSQL Database
  # ==========================================
  postgres:
    image: postgres:15-alpine
    container_name: customify-postgres-dev
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: customify_dev
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.utf8"
    volumes:
      # Persistent data
      - postgres_data:/var/lib/postgresql/data
      
      # Init scripts (opcional)
      # - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
      
    networks:
      - customify-network
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==========================================
  # Redis Cache
  # ==========================================
  redis:
    image: redis:7-alpine
    container_name: customify-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    
    networks:
      - customify-network
    
    restart: unless-stopped
    
    # Redis persistence
    command: redis-server --appendonly yes
    
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # ==========================================
  # pgAdmin (opcional - UI para PostgreSQL)
  # ==========================================
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: customify-pgadmin-dev
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@customify.local
      PGADMIN_DEFAULT_PASSWORD: admin
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      - customify-network
    restart: unless-stopped
    profiles:
      - tools  # Solo se levanta con: docker-compose --profile tools up

  # ==========================================
  # Redis Commander (opcional - UI para Redis)
  # ==========================================
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: customify-redis-commander-dev
    ports:
      - "8081:8081"
    environment:
      REDIS_HOSTS: local:redis:6379
    networks:
      - customify-network
    restart: unless-stopped
    profiles:
      - tools

networks:
  customify-network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  pgadmin_data:
    driver: local
```

---

## 🚀 Comandos Docker (Cheat Sheet)

### Inicio/Parada
```bash
# Levantar TODO
docker-compose up -d

# Levantar solo API (sin tools)
docker-compose up -d api postgres redis

# Levantar con tools (pgAdmin, Redis Commander)
docker-compose --profile tools up -d

# Ver logs en tiempo real
docker-compose logs -f api

# Parar todo
docker-compose down

# Parar y BORRAR datos (⚠️ cuidado)
docker-compose down -v
```

### Desarrollo Diario
```bash
# Ver status
docker-compose ps

# Restart API (si cambias Dockerfile o .env)
docker-compose restart api

# Rebuild si cambias dependencies
docker-compose up -d --build api

# Entrar al container (shell interactivo)
docker-compose exec api bash

# Ver logs específicos
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Database
```bash
# Migrations
docker-compose exec api alembic revision --autogenerate -m "description"
docker-compose exec api alembic upgrade head
docker-compose exec api alembic downgrade -1

# psql (PostgreSQL CLI)
docker-compose exec postgres psql -U postgres -d customify_dev

# Backup DB
docker-compose exec postgres pg_dump -U postgres customify_dev > backup.sql

# Restore DB
docker-compose exec -T postgres psql -U postgres customify_dev < backup.sql

# Reset DB (⚠️ borra todo)
docker-compose exec postgres psql -U postgres -c "DROP DATABASE customify_dev;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE customify_dev;"
docker-compose exec api alembic upgrade head
```

### Testing
```bash
# Run tests en container
docker-compose exec api pytest -v

# Run con coverage
docker-compose exec api pytest --cov=app --cov-report=html

# Run test específico
docker-compose exec api pytest tests/unit/domain/test_design.py

# Watch mode (re-run on change)
docker-compose exec api ptw
```

### Linting & Formatting
```bash
# Lint
docker-compose exec api ruff check .

# Format
docker-compose exec api black .

# Type check
docker-compose exec api mypy app

# Fix all
docker-compose exec api bash -c "black . && ruff check . --fix"
```

---

## 🔥 Hot Reload Funcionando

**Cómo funciona:**

1. **Cambias código en tu IDE local** (VS Code, PyCharm, etc)
2. **Volume mount sincroniza** automáticamente con container
3. **Uvicorn detecta cambio** (gracias a `--reload`)
4. **API se reinicia** automáticamente (2-3 segundos)
5. **Refresh browser** y ves cambios

**Ejemplo:**
```bash
# Terminal 1: Logs en tiempo real
docker-compose logs -f api

# Terminal 2: Editas archivo
echo "# test change" >> app/main.py

# Terminal 1: Verás
# INFO:     Waiting for changes...
# INFO:     Changes detected. Reloading...
# INFO:     Application startup complete.
```

---

## 🐛 Debugging en Docker

### VS Code (Remote Container)

**1. Instalar extensión:** "Dev Containers" (ms-vscode-remote.remote-containers)

**2. Configurar `.vscode/launch.json`:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI (Docker)",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/app"
                }
            ]
        }
    ]
}
```

**3. Modificar `docker-compose.yml` (para debugging):**
```yaml
api:
  command: ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
  ports:
    - "8000:8000"
    - "5678:5678"  # Debug port
```

**4. Start debugging:**
- Levantar: `docker-compose up -d`
- VS Code: F5 (Start Debugging)
- Set breakpoints
- Make request
- Profit!

### Logs Estructurados
```python
# En código, usar logger (NO print)
import logging
logger = logging.getLogger(__name__)

logger.debug("Variable x: %s", x)
logger.info("User logged in: %s", user_id)
logger.warning("Cache miss for key: %s", key)
logger.error("Failed to save: %s", error)

# Ver en terminal
docker-compose logs -f api | grep ERROR
docker-compose logs -f api | grep WARNING
```

---

## 📊 Monitoreo Local

### Endpoints Útiles
```bash
# Health check
curl http://localhost:8000/health

# Docs interactivas (Swagger UI)
open http://localhost:8000/docs

# ReDoc
open http://localhost:8000/redoc

# Metrics (si implementado)
curl http://localhost:8000/metrics

# OpenAPI JSON
curl http://localhost:8000/openapi.json
```

### Tools UI (opcional)
```bash
# Levantar tools
docker-compose --profile tools up -d

# pgAdmin (PostgreSQL UI)
open http://localhost:5050
# Login: admin@customify.local / admin
# Add server:
#   Host: postgres
#   Port: 5432
#   User: postgres
#   Password: postgres

# Redis Commander
open http://localhost:8081
```

---

## 🧹 Limpieza Docker
```bash
# Parar containers
docker-compose down

# Borrar volumes (⚠️ borra DB)
docker-compose down -v

# Borrar images
docker-compose down --rmi all

# Limpieza completa Docker system
docker system prune -a --volumes

# Ver espacio usado
docker system df
```

---

## 🔧 Troubleshooting Docker

### Port already in use
```bash
# Error: port 8000 already in use

# Opción 1: Cambiar puerto en docker-compose.yml
ports:
  - "8001:8000"  # Local:Container

# Opción 2: Matar proceso en puerto
lsof -ti:8000 | xargs kill -9
```

### Container no inicia
```bash
# Ver logs
docker-compose logs api

# Errores comunes:
# 1. Dependency no instalada → Rebuild: docker-compose build api
# 2. .env mal configurado → Verificar .env
# 3. Puerto ocupado → Ver arriba
# 4. Volume permission → chown -R 1000:1000 .
```

### Hot reload no funciona
```bash
# Verificar volumes en docker-compose.yml
docker-compose config | grep volumes

# Si no ves tu código en volumes → Agregar:
volumes:
  - ./app:/app/app:ro

# Restart container
docker-compose restart api
```

### Performance lento en MacOS
```bash
# MacOS: Use :cached flag para mejor performance
volumes:
  - ./app:/app/app:cached  # cached en vez de :ro

# O usar docker-sync (más complejo pero más rápido)
```

---

## ✅ Checklist Daily Workflow

**Al iniciar día:**
```bash
# 1. Check si containers corriendo
docker-compose ps

# 2. Si no → Levantar
docker-compose up -d

# 3. Ver logs
docker-compose logs -f api

# 4. Pull latest code
git pull

# 5. Rebuild si cambió dependencies
docker-compose up -d --build api

# 6. Migrations si cambió schema
docker-compose exec api alembic upgrade head
```

**Durante desarrollo:**
```bash
# Editas código en IDE local → Auto-reload
# Si necesitas shell:
docker-compose exec api bash

# Run tests:
docker-compose exec api pytest
```

**Al finalizar día:**
```bash
# Parar containers (opcional - o dejar corriendo)
docker-compose down

# Push cambios
git add .
git commit -m "feat: descripción"
git push

# Actualizar DAILY-LOG.md
```

---

## 🎯 Ventajas Docker Development

✅ **Consistency:** Mismo environment en todos lados
✅ **Isolation:** No contamina tu máquina local  
✅ **Onboarding:** Solo `docker-compose up` y listo  
✅ **Matching Production:** Dev = Prod environment  
✅ **Easy Reset:** `docker-compose down -v` y empiezas limpio  
✅ **Multi-project:** Varios proyectos, no conflicts  

---

**IMPORTANTE:** Todo este documento asume desarrollo en Docker. NO instales nada localmente excepto Docker Desktop.