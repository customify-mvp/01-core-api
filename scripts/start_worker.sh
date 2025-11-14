#!/bin/bash

# =============================================================================
# Start Celery Worker Script
# =============================================================================
# Purpose: Start Celery worker for local development
# Usage: ./scripts/start_worker.sh
# Prerequisites:
#   - Virtual environment activated (or will activate automatically)
#   - Redis running (localhost:6379 or via docker-compose)
#   - PostgreSQL running (localhost:5432 or via docker-compose)
# =============================================================================

set -e  # Exit on error

echo "========================================="
echo "Starting Celery Worker for Customify API"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Found virtual environment"
    
    # Activate virtual environment
    if [ -f "venv/Scripts/activate" ]; then
        # Windows (Git Bash)
        source venv/Scripts/activate
    elif [ -f "venv/bin/activate" ]; then
        # Unix/Linux/macOS
        source venv/bin/activate
    fi
    
    echo -e "${GREEN}✓${NC} Virtual environment activated"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment not found (venv/)"
    echo "Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

# Check if Redis is accessible
echo ""
echo "Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli -u redis://localhost:6379/0 ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis is running on localhost:6379"
    else
        echo -e "${YELLOW}⚠${NC} Redis not accessible on localhost:6379"
        echo "Make sure Redis is running (docker-compose up redis -d)"
    fi
else
    echo -e "${YELLOW}⚠${NC} redis-cli not installed, skipping Redis check"
fi

# Check if PostgreSQL is accessible (optional check)
echo ""
echo "Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    if PGPASSWORD=customify123 psql -h localhost -U customify -d customify_dev -c '\q' 2>/dev/null; then
        echo -e "${GREEN}✓${NC} PostgreSQL is running"
    else
        echo -e "${YELLOW}⚠${NC} PostgreSQL not accessible on localhost:5432"
        echo "Make sure PostgreSQL is running (docker-compose up postgres -d)"
    fi
else
    echo -e "${YELLOW}⚠${NC} psql not installed, skipping PostgreSQL check"
fi

# Display worker configuration
echo ""
echo "========================================="
echo "Worker Configuration:"
echo "========================================="
echo "  App: customify_workers"
echo "  Broker: redis://localhost:6379/0"
echo "  Result Backend: PostgreSQL (DATABASE_URL)"
echo "  Queues: high_priority, default"
echo "  Concurrency: 2 workers"
echo "  Log Level: info"
echo "========================================="
echo ""

# Start Celery worker
echo -e "${GREEN}Starting Celery worker...${NC}"
echo ""

celery -A app.infrastructure.workers.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=high_priority,default \
    --pool=solo \
    --hostname=worker@%h

# Note: Press Ctrl+C to stop the worker
