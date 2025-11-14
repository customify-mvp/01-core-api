# ============================================================
# Customify Core API - Docker Management Scripts
# ============================================================

# Build and start all services
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
down-volumes:
	docker-compose down -v

# Rebuild and restart
rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# View logs
logs:
	docker-compose logs -f

# View API logs only
logs-api:
	docker-compose logs -f api

# Run migrations
migrate:
	docker-compose exec api alembic upgrade head

# Create new migration
migration:
	@read -p "Enter migration message: " msg; \
	docker-compose exec api alembic revision --autogenerate -m "$$msg"

# Seed development data
seed:
	docker-compose exec api python scripts/seed_dev_data.py

# Open bash in API container
shell:
	docker-compose exec api /bin/bash

# Open Python shell with app context
python:
	docker-compose exec api python

# Run tests
test:
	docker-compose exec api pytest -v

# Run tests with coverage
test-cov:
	docker-compose exec api pytest --cov=app --cov-report=html

# Check database connection
db-check:
	docker-compose exec postgres psql -U customify -d customify_dev -c "SELECT version();"

# Open PostgreSQL shell
db-shell:
	docker-compose exec postgres psql -U customify -d customify_dev

# Open Redis CLI
redis-cli:
	docker-compose exec redis redis-cli

# View running containers
ps:
	docker-compose ps

# Clean up (stop containers and remove images)
clean:
	docker-compose down
	docker system prune -f

# Full reset (CAUTION: removes everything)
reset: down-volumes
	docker system prune -af
	@echo "✅ Full reset complete. Run 'make up' to start fresh."

.PHONY: up down down-volumes rebuild logs logs-api migrate migration seed shell python test test-cov db-check db-shell redis-cli ps clean reset
