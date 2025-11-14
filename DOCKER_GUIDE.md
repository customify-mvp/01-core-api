# 🐳 Docker Quick Start Guide

## Prerrequisitos

- Docker Desktop instalado
- Docker Compose v2+

## 🚀 Inicio Rápido

### 1. Construir y levantar servicios

```powershell
# PowerShell (Windows)
docker-compose up -d --build

# O usando el script helper
.\docker.ps1 up
```

### 2. Ver logs

```powershell
# Todos los servicios
docker-compose logs -f

# Solo API
docker-compose logs -f api
```

### 3. Ejecutar migraciones

```powershell
docker-compose exec api alembic upgrade head

# O usando el script
.\docker.ps1 migrate
```

### 4. Seed data (primera vez)

```powershell
docker-compose exec api python scripts/seed_dev_data.py

# O usando el script
.\docker.ps1 seed
```

### 5. Acceder a la API

- **Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📦 Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `api` | 8000 | FastAPI Core API |
| `postgres` | 5432 | PostgreSQL 15 |
| `redis` | 6379 | Redis Cache |

## 🛠️ Comandos Útiles

### PowerShell (Windows)

```powershell
# Ver servicios corriendo
docker-compose ps

# Detener servicios
docker-compose down

# Reconstruir
docker-compose down
docker-compose up -d --build

# Shell en contenedor API
docker-compose exec api /bin/bash

# Shell PostgreSQL
docker-compose exec postgres psql -U customify -d customify_dev

# Redis CLI
docker-compose exec redis redis-cli

# Ver logs
docker-compose logs -f api

# Ejecutar tests
docker-compose exec api pytest -v
```

### Usando script helper (`docker.ps1`)

```powershell
.\docker.ps1 up          # Levantar servicios
.\docker.ps1 down        # Detener servicios
.\docker.ps1 rebuild     # Reconstruir
.\docker.ps1 logs        # Ver logs
.\docker.ps1 logs-api    # Logs solo API
.\docker.ps1 migrate     # Ejecutar migraciones
.\docker.ps1 seed        # Seed data
.\docker.ps1 shell       # Bash en API
.\docker.ps1 db-shell    # PostgreSQL shell
.\docker.ps1 test        # Ejecutar tests
.\docker.ps1 ps          # Ver servicios
```

## 🔧 Troubleshooting

### Error: "port already allocated"

```powershell
# Detener servicios que usen el puerto
docker-compose down

# Ver qué está usando el puerto
netstat -ano | findstr :8000
```

### Error: "connection refused"

```powershell
# Verificar que los servicios estén corriendo
docker-compose ps

# Ver logs de errores
docker-compose logs api
docker-compose logs postgres
```

### Reiniciar desde cero

```powershell
# CUIDADO: Elimina todos los datos
docker-compose down -v
docker-compose up -d --build
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/seed_dev_data.py
```

## 📝 Desarrollo

### Hot Reload

El código se monta como volumen, por lo que los cambios se reflejan automáticamente:

```yaml
volumes:
  - .:/app  # Tu código se monta aquí
```

FastAPI en modo development (`--reload`) detecta cambios automáticamente.

### Instalar dependencias

```powershell
# 1. Agregar a requirements.txt
# 2. Reconstruir imagen
docker-compose down
docker-compose build --no-cache api
docker-compose up -d
```

## 🔐 Credenciales por Defecto

### PostgreSQL
- Usuario: `customify`
- Password: `customify123`
- Base de datos: `customify_dev`

### Test User (después de seed)
- Email: `test@customify.app`
- Password: `Test1234`

## 🗄️ Base de Datos

### Conectar desde herramienta externa (DBeaver, pgAdmin)

```
Host: localhost
Port: 5432
Database: customify_dev
Username: customify
Password: customify123
```

### Backup manual

```powershell
docker-compose exec postgres pg_dump -U customify customify_dev > backup.sql
```

### Restore

```powershell
Get-Content backup.sql | docker-compose exec -T postgres psql -U customify -d customify_dev
```

## 📊 Migraciones

### Crear nueva migración

```powershell
docker-compose exec api alembic revision --autogenerate -m "descripción"
```

### Aplicar migraciones

```powershell
docker-compose exec api alembic upgrade head
```

### Revertir migración

```powershell
docker-compose exec api alembic downgrade -1
```

## ✅ Verificación Post-Instalación

```powershell
# 1. Servicios corriendo
docker-compose ps
# ✅ Todos en estado "Up"

# 2. Health check
curl http://localhost:8000/health
# ✅ {"status":"healthy",...}

# 3. Base de datos
docker-compose exec postgres psql -U customify -d customify_dev -c "\dt"
# ✅ Lista de tablas: users, subscriptions, designs, orders, shopify_stores

# 4. Swagger Docs
# Abre: http://localhost:8000/docs
# ✅ Documentación interactiva visible
```

## 🎯 Siguiente Paso

Una vez validado que todo funciona:

1. **Implementar endpoints**: Crear rutas en `app/presentation/api/v1/endpoints/`
2. **Implementar use cases**: Lógica de negocio en `app/application/use_cases/`
3. **Implementar repositories**: Acceso a datos en `app/infrastructure/database/repositories/`

Ver `ARQUITECTURA.md` para entender la estructura Clean Architecture.
