#!/bin/bash
# Entrypoint script for Core API container
# Waits for database, runs migrations, then starts the app

set -e

echo "🚀 Starting Customify Core API..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DATABASE_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "   PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
until redis-cli -h "$REDIS_HOST" ping 2>/dev/null; do
  echo "   Redis is unavailable - sleeping"
  sleep 2
done
echo "✅ Redis is ready!"

# Run database migrations
echo "🔄 Running Alembic migrations..."
alembic upgrade head
echo "✅ Migrations applied!"

# Seed data if SEED_DATA=true
if [ "$SEED_DATA" = "true" ]; then
  echo "🌱 Seeding development data..."
  python scripts/seed_dev_data.py
  echo "✅ Seed data loaded!"
fi

# Start the application
echo "🎉 Starting FastAPI server..."
exec "$@"
