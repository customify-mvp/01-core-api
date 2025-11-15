#!/bin/bash

# Deployment Pre-flight Check Script (Docker-Compatible)
# Detects if running in Docker and adjusts checks accordingly
#
# Usage:
#   ./scripts/deployment_check.sh              # Auto-detect
#   DOCKER_MODE=1 ./scripts/deployment_check.sh # Force Docker mode
#   DOCKER_MODE=0 ./scripts/deployment_check.sh # Force local mode

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED=0
WARNINGS=0

# Detect Docker environment
if [ -f "/.dockerenv" ] || [ -n "$DOCKER_MODE" ]; then
    IN_DOCKER=1
    ENV_TYPE="Docker Container"
else
    IN_DOCKER=0
    ENV_TYPE="Local Machine"
fi

# Helper functions
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    FAILED=1
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

check_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Header
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🚀 Customify Deployment Check (${ENV_TYPE})${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Python Version
echo "1️⃣  Checking Python version..."
if command -v python &> /dev/null; then
    python_version=$(python --version 2>&1 | awk '{print $2}')
    major=$(echo $python_version | cut -d. -f1)
    minor=$(echo $python_version | cut -d. -f2)

    if [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; then
        check_pass "Python version: $python_version"
    else
        check_fail "Python version $python_version (required: 3.12+)"
    fi
else
    check_fail "Python not found"
fi
echo ""

# 2. Dependencies Check
echo "2️⃣  Checking dependencies..."
if python -m pip check > /dev/null 2>&1; then
    check_pass "Dependencies are consistent"
else
    check_fail "Dependency conflicts detected"
fi
echo ""

# 3. Code Quality (skip in Docker unless explicitly run)
echo "3️⃣  Code quality checks..."

if command -v ruff &> /dev/null; then
    if ruff check app/ tests/ --quiet 2>/dev/null; then
        check_pass "Ruff linting passed"
    else
        check_warn "Ruff linting issues found"
    fi
else
    check_warn "Ruff not installed"
fi

if command -v black &> /dev/null; then
    if black app/ tests/ --check --quiet 2>/dev/null; then
        check_pass "Black formatting passed"
    else
        check_warn "Code needs formatting"
    fi
else
    check_warn "Black not installed"
fi
echo ""

# 4. Tests
echo "4️⃣  Running tests..."
if command -v pytest &> /dev/null; then
    if pytest --cov=app --cov-fail-under=60 -q --tb=no 2>/dev/null; then
        check_pass "Tests passed (coverage ≥60%)"
    else
        check_fail "Tests failed or coverage low"
    fi
else
    check_fail "Pytest not installed"
fi
echo ""

# 5. Database (Docker-specific checks)
echo "5️⃣  Database checks..."

if [ "$IN_DOCKER" -eq 1 ]; then
    # In Docker, check if database is accessible
    if python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('$DATABASE_URL'))" 2>/dev/null; then
        check_pass "Database connection successful"
    else
        check_warn "Cannot connect to database"
    fi
else
    # Local, check if postgres container is running
    if docker-compose ps postgres 2>/dev/null | grep -q "Up"; then
        check_pass "PostgreSQL container running"
    else
        check_warn "PostgreSQL container not running"
    fi
fi

# Check migrations
if command -v alembic &> /dev/null; then
    if alembic check > /dev/null 2>&1; then
        check_pass "Migrations up to date"
    else
        check_warn "Pending migrations"
    fi
fi
echo ""

# 6. Redis
echo "6️⃣  Redis checks..."

if [ "$IN_DOCKER" -eq 1 ]; then
    if python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping()" 2>/dev/null; then
        check_pass "Redis connection successful"
    else
        check_warn "Cannot connect to Redis"
    fi
else
    if docker-compose ps redis 2>/dev/null | grep -q "Up"; then
        check_pass "Redis container running"
    else
        check_warn "Redis container not running"
    fi
fi
echo ""

# 7. Environment Variables
echo "7️⃣  Environment configuration..."

required_vars=(
    "DATABASE_URL"
    "REDIS_URL"
    "JWT_SECRET_KEY"
    "ENVIRONMENT"
)

for var in "${required_vars[@]}"; do
    if [ -n "${!var}" ]; then
        check_pass "$var is set"
    else
        check_fail "$var is not set"
    fi
done

# Check JWT secret length
if [ -n "$JWT_SECRET_KEY" ]; then
    if [ ${#JWT_SECRET_KEY} -ge 32 ]; then
        check_pass "JWT_SECRET_KEY is secure (${#JWT_SECRET_KEY} chars)"
    else
        check_fail "JWT_SECRET_KEY too short (${#JWT_SECRET_KEY} chars)"
    fi
fi
echo ""

# 8. Security
echo "8️⃣  Security checks..."

# Check for hardcoded secrets
if grep -rE "(password|secret|key)\s*=\s*['\"][^'\$]" app/ 2>/dev/null | grep -v "example" | grep -v "test" > /dev/null; then
    check_fail "Hardcoded secrets detected!"
else
    check_pass "No hardcoded secrets"
fi

# Check TODO/FIXME
todo_count=$(grep -r "TODO\|FIXME\|XXX" app/ 2>/dev/null | wc -l)
if [ "$todo_count" -gt 0 ]; then
    check_warn "$todo_count TODO/FIXME comments"
else
    check_pass "No TODO/FIXME comments"
fi
echo ""

# 9. Documentation
echo "9️⃣  Documentation..."
required_docs=("README.md" "CONTRIBUTING.md" "CHANGELOG.md" "LICENSE" "SECURITY.md")

for doc in "${required_docs[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "$doc exists"
    else
        check_warn "$doc not found"
    fi
done
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
        echo -e "${GREEN}   Ready for deployment 🚀${NC}"
    else
        echo -e "${YELLOW}⚠️  PASSED WITH $WARNINGS WARNING(S)${NC}"
        echo -e "${YELLOW}   Review warnings before deploying${NC}"
    fi
    echo ""
    exit 0
else
    echo -e "${RED}❌ DEPLOYMENT CHECKS FAILED!${NC}"
    echo -e "${RED}   Fix critical issues before deploying${NC}"
    echo ""
    exit 1
fi
