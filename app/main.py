"""
Customify Core API - Main application entry point.

FastAPI application with Clean Architecture.
"""

import os
from contextlib import asynccontextmanager
from datetime import UTC

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

# Import all domain exceptions for handler registration
from app.domain.exceptions.auth_exceptions import (
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.domain.exceptions.design_exceptions import (
    DesignNotFoundError,
    UnauthorizedDesignAccessError,
)
from app.domain.exceptions.subscription_exceptions import (
    InactiveSubscriptionError,
    QuotaExceededError,
)
from app.infrastructure.database.session import close_db, get_db_session
from app.infrastructure.logging.structured_logger import get_logger, init_logger
from app.presentation.api.v1.router import api_router
from app.presentation.middleware import SecurityHeadersMiddleware


# ============================================================
# Lifespan context manager
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager (startup/shutdown)."""
    # Initialize structured logging
    init_logger(
        app_name="customify-api",
        level="DEBUG" if settings.DEBUG else "INFO",
        use_json=settings.ENVIRONMENT == "production",
    )
    logger = get_logger()

    # Startup
    logger.info(
        "Customify Core API starting",
        extra={
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "storage": "Local" if settings.USE_LOCAL_STORAGE else "S3",
        },
    )
    print("=" * 60)
    print("🚀 Customify Core API starting...")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug: {settings.DEBUG}")
    print("   Database: Connected")

    # Create storage directory if using local storage
    if settings.USE_LOCAL_STORAGE:
        storage_dir = "./storage"
        os.makedirs(storage_dir, exist_ok=True)
        print(f"   Storage: Local ({storage_dir})")
    else:
        print(f"   Storage: S3 ({settings.S3_BUCKET_NAME})")

    print("   API Docs: http://localhost:8000/docs")
    print("=" * 60)

    yield

    # Shutdown
    print("\n" + "=" * 60)
    print("🛑 Customify Core API shutting down...")
    await close_db()
    print("=" * 60)


# ============================================================
# Create FastAPI app
# ============================================================
app = FastAPI(
    title="Customify Core API",
    description="Backend API for Customify - AI-powered product customization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ============================================================
# CORS Middleware (Security-hardened)
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods only
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "X-Request-ID",
        "Accept-Language",
    ],  # Specific headers only
    expose_headers=["X-Request-ID"],  # Headers clients can access
    max_age=3600,  # Cache preflight requests for 1 hour
)

# ============================================================
# Security Headers Middleware
# ============================================================
app.add_middleware(SecurityHeadersMiddleware)

# ============================================================
# Static Files (for local development)
# ============================================================
if settings.USE_LOCAL_STORAGE:
    # Mount static files directory for serving design previews
    # Only used when USE_LOCAL_STORAGE=true (development mode)
    app.mount("/static", StaticFiles(directory="./storage"), name="static")

# ============================================================
# Exception Handlers
# ============================================================


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    """Handle invalid credentials error."""
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)})


@app.exception_handler(EmailAlreadyExistsError)
async def email_exists_handler(request: Request, exc: EmailAlreadyExistsError):
    """Handle email already exists error."""
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    """Handle user not found error."""
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(InactiveUserError)
async def inactive_user_handler(request: Request, exc: InactiveUserError):
    """Handle inactive user error."""
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})


@app.exception_handler(QuotaExceededError)
async def quota_exceeded_handler(request: Request, exc: QuotaExceededError):
    """Handle quota exceeded error."""
    return JSONResponse(status_code=status.HTTP_402_PAYMENT_REQUIRED, content={"detail": str(exc)})


@app.exception_handler(InactiveSubscriptionError)
async def inactive_subscription_handler(request: Request, exc: InactiveSubscriptionError):
    """Handle inactive subscription error."""
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})


@app.exception_handler(DesignNotFoundError)
async def design_not_found_handler(request: Request, exc: DesignNotFoundError):
    """Handle design not found error."""
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedDesignAccessError)
async def unauthorized_design_handler(request: Request, exc: UnauthorizedDesignAccessError):
    """Handle unauthorized design access error."""
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value error."""
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    # TODO: Add proper logging
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ============================================================
# Include API router
# ============================================================
app.include_router(api_router)


# ============================================================
# Health check endpoint
# ============================================================
@app.get("/health", tags=["Health"])
async def health_check(session: AsyncSession = Depends(get_db_session)):
    """
    Comprehensive health check endpoint.

    Checks:
    - API is running
    - Database connection
    - Redis connection
    - Celery workers
    - S3 (if configured)

    Returns:
        200: All systems healthy
        503: At least one system degraded
    """
    from datetime import datetime

    from redis import Redis

    # Try to get logger, but don't fail if not initialized (tests)
    try:
        logger = get_logger()
    except RuntimeError:
        logger = None

    health = {
        "status": "healthy",
        "service": "customify-core-api",
        "version": "1.0.0",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "environment": settings.ENVIRONMENT,
        "checks": {},
    }

    # Database check
    try:
        await session.execute(text("SELECT 1"))
        health["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        if logger:
            logger.error("Database health check failed", exc_info=True)
        health["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"

    # Redis check
    try:
        redis_client = Redis.from_url(str(settings.REDIS_URL), socket_timeout=2)
        redis_client.ping()
        redis_client.close()
        health["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        if logger:
            logger.error("Redis health check failed", exc_info=True)
        health["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"

    # Celery worker check
    try:
        from app.infrastructure.workers.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=2.0)
        stats = inspect.stats()

        if stats:
            worker_count = len(stats)
            health["checks"]["celery"] = {"status": "healthy", "workers": worker_count}
        else:
            health["checks"]["celery"] = {"status": "unhealthy", "error": "No workers available"}
            health["status"] = "degraded"
    except Exception as e:
        if logger:
            logger.error("Celery health check failed", exc_info=True)
        health["checks"]["celery"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"

    # S3 check (only if not using local storage)
    if not settings.USE_LOCAL_STORAGE:
        try:
            from app.infrastructure.storage.s3_client import s3_client

            # Simple head_bucket check
            s3_client.s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            health["checks"]["s3"] = {"status": "healthy"}
        except Exception as e:
            if logger:
                logger.error("S3 health check failed", exc_info=True)
            health["checks"]["s3"] = {"status": "unhealthy", "error": str(e)}
            health["status"] = "degraded"

    # Determine status code
    status_code = 200 if health["status"] == "healthy" else 503

    return JSONResponse(
        content=health,
        status_code=status_code,
    )


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to Customify Core API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }


# ============================================================
# Run with uvicorn
# ============================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
