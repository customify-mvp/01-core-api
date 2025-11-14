# ============================================================
# Multi-stage Dockerfile for Customify Core API
# Python 3.12 + FastAPI + SQLAlchemy 2.0
# ============================================================

# Stage 1: Base image with Python dependencies
FROM python:3.12-slim as base

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Stage 2: Development image
# ============================================================
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest==7.4.0 \
    pytest-asyncio==0.23.0 \
    pytest-cov==4.1.0 \
    ruff==0.1.0 \
    black==24.10.0 \
    mypy==1.8.0

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================
# Stage 3: Production image (optimized)
# ============================================================
FROM base as production

# Copy only application code (no dev dependencies)
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Production command (no reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
