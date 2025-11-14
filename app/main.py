"""
Customify Core API - Main application entry point.

FastAPI application with Clean Architecture.
"""

from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.presentation.api.v1.router import api_router
from app.infrastructure.database.session import close_db, get_db_session

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
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Exception Handlers
# ============================================================

@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    """Handle invalid credentials error."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)}
    )

@app.exception_handler(EmailAlreadyExistsError)
async def email_exists_handler(request: Request, exc: EmailAlreadyExistsError):
    """Handle email already exists error."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )

@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    """Handle user not found error."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

@app.exception_handler(InactiveUserError)
async def inactive_user_handler(request: Request, exc: InactiveUserError):
    """Handle inactive user error."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)}
    )

@app.exception_handler(QuotaExceededError)
async def quota_exceeded_handler(request: Request, exc: QuotaExceededError):
    """Handle quota exceeded error."""
    return JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={"detail": str(exc)}
    )

@app.exception_handler(InactiveSubscriptionError)
async def inactive_subscription_handler(request: Request, exc: InactiveSubscriptionError):
    """Handle inactive subscription error."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)}
    )

@app.exception_handler(DesignNotFoundError)
async def design_not_found_handler(request: Request, exc: DesignNotFoundError):
    """Handle design not found error."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

@app.exception_handler(UnauthorizedDesignAccessError)
async def unauthorized_design_handler(request: Request, exc: UnauthorizedDesignAccessError):
    """Handle unauthorized design access error."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value error."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    # TODO: Add proper logging
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
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
    Health check endpoint.
    
    Checks:
    - API is running
    - Database connection
    
    Returns:
        dict: Service status, version, and database health
    """
    # Check database connection
    db_status = "healthy"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"
    
    overall_status = "healthy" if db_status == "healthy" else "degraded"
    
    return JSONResponse(
        content={
            "status": overall_status,
            "service": "customify-core-api",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "database": db_status,
        },
        status_code=200 if overall_status == "healthy" else 503,
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

