# ============================================================
# Customify Core API - Docker Management Scripts (PowerShell)
# ============================================================

param(
    [Parameter(Position=0)]
    [string]$Command
)

function Show-Help {
    Write-Host "Customify Core API - Docker Commands" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\docker.ps1 <command>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  up              - Build and start all services"
    Write-Host "  down            - Stop all services"
    Write-Host "  rebuild         - Rebuild and restart services"
    Write-Host "  logs            - View all logs"
    Write-Host "  logs-api        - View API logs only"
    Write-Host "  migrate         - Run database migrations"
    Write-Host "  seed            - Seed development data"
    Write-Host "  shell           - Open bash in API container"
    Write-Host "  db-shell        - Open PostgreSQL shell"
    Write-Host "  test            - Run tests"
    Write-Host "  ps              - View running containers"
    Write-Host ""
}

switch ($Command) {
    "up" {
        Write-Host "🚀 Starting services..." -ForegroundColor Green
        docker-compose up -d
    }
    "down" {
        Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
        docker-compose down
    }
    "rebuild" {
        Write-Host "🔄 Rebuilding services..." -ForegroundColor Cyan
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
    }
    "logs" {
        docker-compose logs -f
    }
    "logs-api" {
        docker-compose logs -f api
    }
    "migrate" {
        Write-Host "🔄 Running migrations..." -ForegroundColor Cyan
        docker-compose exec api alembic upgrade head
    }
    "seed" {
        Write-Host "🌱 Seeding data..." -ForegroundColor Green
        docker-compose exec api python scripts/seed_dev_data.py
    }
    "shell" {
        docker-compose exec api /bin/bash
    }
    "db-shell" {
        docker-compose exec postgres psql -U customify -d customify_dev
    }
    "test" {
        Write-Host "🧪 Running tests..." -ForegroundColor Cyan
        docker-compose exec api pytest -v
    }
    "ps" {
        docker-compose ps
    }
    default {
        Show-Help
    }
}
