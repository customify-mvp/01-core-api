"""
Customify Core API - Main application entry point.

FastAPI application with Clean Architecture.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.presentation.api.v1.router import api_router
from app.presentation.middleware.exception_handler import domain_exception_handler
from app.infrastructure.database.session import close_db

# Import all domain exceptions for handler registration
from app.domain.exceptions.auth_exceptions import (
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    UserNotFoundError,
    InactiveUserError,
)
from app.domain.exceptions.subscription_exceptions import (
    QuotaExceededError,
    InactiveSubscriptionError,
)
from app.domain.exceptions.design_exceptions import (
    DesignNotFoundError,
    UnauthorizedDesignAccessError,
)


# ============================================================
# Lifespan context manager
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager (startup/shutdown)."""
    # Startup
    print("=" * 60)
    print("🚀 Customify Core API starting...")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   Database: Connected")
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
    lifespan=lifespan
)

# ============================================================
# CORS Middleware
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Register exception handlers
# ============================================================
exception_types = [
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    UserNotFoundError,
    InactiveUserError,
    QuotaExceededError,
    InactiveSubscriptionError,
    DesignNotFoundError,
    UnauthorizedDesignAccessError,
    ValueError,
]

for exc_type in exception_types:
    app.add_exception_handler(exc_type, domain_exception_handler)

# ============================================================
# Include API router
# ============================================================
app.include_router(api_router)

# ============================================================
# Health check endpoint
# ============================================================
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and version.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "customify-core-api",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
        },
        status_code=200,
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
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

