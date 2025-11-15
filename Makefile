.PHONY: help install test coverage lint format clean dev worker migrate seed docker-up docker-down docker-logs docker-exec docker-shell all ci

# Default target
.DEFAULT_GOAL := help

# Detect if we're running in Docker
DOCKER_COMPOSE := $(shell command -v docker-compose 2> /dev/null || echo "docker compose")
DOCKER_EXEC := $(DOCKER_COMPOSE) exec api
DOCKER_EXEC_WORKER := $(DOCKER_COMPOSE) exec worker
PYTHON := python
PIP := pip

help: ## Show this help message
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║       Customify Core API - Docker Commands                ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "💡 All commands run inside Docker containers"
	@echo "💡 Use 'make local-<command>' for local execution"

# ============================================================================
# DOCKER COMMANDS (Primary - Run in containers)
# ============================================================================

docker-up: ## Start all Docker services
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services started. API: http://localhost:8000"

docker-down: ## Stop all Docker services
	$(DOCKER_COMPOSE) down

docker-restart: docker-down docker-up ## Restart Docker services

docker-logs: ## Show Docker logs (all services)
	$(DOCKER_COMPOSE) logs -f

docker-logs-api: ## Show API logs only
	$(DOCKER_COMPOSE) logs -f api

docker-logs-worker: ## Show worker logs only
	$(DOCKER_COMPOSE) logs -f worker

docker-ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

docker-clean: ## Remove containers and volumes (⚠️ DESTRUCTIVE)
	@echo "⚠️  This will delete all data. Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	$(DOCKER_COMPOSE) down -v
	@echo "✅ Containers and volumes removed"

docker-rebuild: ## Rebuild Docker images
	$(DOCKER_COMPOSE) build --no-cache

# ============================================================================
# DEVELOPMENT (Inside Docker)
# ============================================================================

dev: docker-up ## Start development environment
	@echo "🚀 Development environment running"
	@echo "   API: http://localhost:8000"
	@echo "   Docs: http://localhost:8000/docs"
	@echo "   Flower: http://localhost:5555"

shell: ## Open Python shell in API container
	$(DOCKER_EXEC) python -i -c "from app.main import app; from app.config import settings; print('✅ App context loaded')"

bash: ## Open bash shell in API container
	$(DOCKER_EXEC) bash

worker-bash: ## Open bash shell in worker container
	$(DOCKER_EXEC_WORKER) bash

# ============================================================================
# TESTING (Inside Docker)
# ============================================================================

test: ## Run all tests in Docker
	$(DOCKER_EXEC) pytest -v

test-unit: ## Run unit tests only
	$(DOCKER_EXEC) pytest tests/unit/ -v

test-integration: ## Run integration tests only
	$(DOCKER_EXEC) pytest tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests
	$(DOCKER_EXEC) pytest tests/e2e/ -v

coverage: ## Run tests with coverage report
	$(DOCKER_EXEC) pytest --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=60
	@echo ""
	@echo "📊 Coverage report: htmlcov/index.html"

coverage-open: coverage ## Generate and open coverage report
	@echo "Opening coverage report..."
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || start htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html manually"

# ============================================================================
# CODE QUALITY (Inside Docker)
# ============================================================================

lint: ## Lint code with ruff
	$(DOCKER_EXEC) ruff check app/ tests/

lint-fix: ## Lint and auto-fix issues
	$(DOCKER_EXEC) ruff check app/ tests/ --fix

format: ## Format code with black
	$(DOCKER_EXEC) black app/ tests/ scripts/

format-check: ## Check formatting without changes
	$(DOCKER_EXEC) black app/ tests/ scripts/ --check

typecheck: ## Type check with mypy
	$(DOCKER_EXEC) mypy app/ --ignore-missing-imports

quality: format lint typecheck ## Run all quality checks

# ============================================================================
# DATABASE (Inside Docker)
# ============================================================================

migrate: ## Run database migrations
	$(DOCKER_EXEC) alembic upgrade head

migrate-down: ## Rollback last migration
	$(DOCKER_EXEC) alembic downgrade -1

migrate-create: ## Create new migration (use: make migrate-create msg="description")
	$(DOCKER_EXEC) alembic revision --autogenerate -m "$(msg)"

migrate-history: ## Show migration history
	$(DOCKER_EXEC) alembic history

seed: ## Seed database with test data
	$(DOCKER_EXEC) python scripts/seed_dev_data.py

db-reset: ## Reset database (⚠️ DESTRUCTIVE)
	@echo "⚠️  This will delete all data. Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	$(DOCKER_EXEC) alembic downgrade base
	$(DOCKER_EXEC) alembic upgrade head
	$(DOCKER_EXEC) python scripts/seed_dev_data.py
	@echo "✅ Database reset complete"

# ============================================================================
# UTILITIES (Inside Docker)
# ============================================================================

fix-datetime: ## Fix datetime deprecation warnings
	$(DOCKER_EXEC) python scripts/fix_datetime_deprecation.py

deployment-check: ## Run pre-deployment checks
	$(DOCKER_EXEC) bash scripts/deployment_check.sh

routes: ## Show all API routes
	$(DOCKER_EXEC) python -c "from app.main import app; from fastapi.routing import APIRoute; routes = [r for r in app.routes if isinstance(r, APIRoute)]; [print(f'{list(r.methods)[0]:6} {r.path}') for r in sorted(routes, key=lambda x: x.path)]"

install: ## Install dependencies in container (rebuild recommended instead)
	$(DOCKER_EXEC) pip install -r requirements.txt

# ============================================================================
# COMBINED TARGETS
# ============================================================================

all: format lint typecheck test ## Run all checks

ci: lint typecheck coverage ## Run CI pipeline

# ============================================================================
# LOCAL COMMANDS (Run on host machine, not in Docker)
# ============================================================================

local-install: ## Install dependencies locally
	pip install -r requirements.txt

local-install-dev: local-install ## Install dev dependencies locally
	pip install pre-commit safety bandit
	pre-commit install

local-test: ## Run tests locally (not in Docker)
	pytest -v

local-format: ## Format code locally
	black app/ tests/ scripts/

local-lint: ## Lint code locally
	ruff check app/ tests/

local-hooks-install: ## Install pre-commit hooks locally
	pip install pre-commit
	pre-commit install

local-hooks-run: ## Run pre-commit hooks locally
	pre-commit run --all-files

# ============================================================================
# MONITORING
# ============================================================================

flower: ## Start Flower (Celery monitoring)
	@echo "🌸 Flower UI: http://localhost:5555"
	$(DOCKER_COMPOSE) up -d flower

health: ## Check API health
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API not responding"

# ============================================================================
# INFO
# ============================================================================

info: ## Show project information
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║              Customify Core API - Info                    ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🐳 Docker Status:"
	@$(DOCKER_COMPOSE) ps || echo "   Docker not running"
	@echo ""
	@echo "📦 Containers:"
	@echo "   API:      http://localhost:8000"
	@echo "   Docs:     http://localhost:8000/docs"
	@echo "   ReDoc:    http://localhost:8000/redoc"
	@echo "   Flower:   http://localhost:5555"
	@echo ""
	@echo "💾 Databases:"
	@echo "   Postgres: localhost:5432"
	@echo "   Redis:    localhost:6379"
	@echo ""
	@echo "📝 Logs:"
	@echo "   All:      make docker-logs"
	@echo "   API:      make docker-logs-api"
	@echo "   Worker:   make docker-logs-worker"

# ============================================================================
# QUICK SETUP
# ============================================================================

setup: docker-up migrate seed ## Quick setup: Start Docker, migrate, seed
	@echo ""
	@echo "✅ Setup complete!"
	@echo "   API: http://localhost:8000"
	@echo "   Docs: http://localhost:8000/docs"

init: setup ## Alias for setup

# ============================================================================
# DEBUGGING
# ============================================================================

debug-api: ## Attach to API container for debugging
	$(DOCKER_COMPOSE) exec api bash

debug-db: ## Connect to PostgreSQL
	$(DOCKER_COMPOSE) exec postgres psql -U customify -d customify_dev

debug-redis: ## Connect to Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

# ============================================================================
# PRODUCTION
# ============================================================================

prod-check: deployment-check ## Alias for deployment check

prod-build: ## Build production Docker image
	docker build -t customify-api:latest -f Dockerfile.prod .

prod-tag: ## Tag image for production (use: make prod-tag version=1.0.1)
	docker tag customify-api:latest customify-api:$(version)
	docker tag customify-api:latest customify-api:production
