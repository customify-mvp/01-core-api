"""
Customify Core API - Main application entry point.

FastAPI application with Clean Architecture.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

# ============================================================
# Create FastAPI app
# ============================================================
app = FastAPI(
    title="Customify Core API",
    description="Backend API for Customify - Custom Product Design Platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
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
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
    }

# ============================================================
# Startup event
# ============================================================
@app.on_event("startup")
async def startup_event():
    """
    Execute on application startup.
    """
    print("=" * 60)
    print("🚀 Customify Core API starting...")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   Database: Connected")
    print("=" * 60)

# ============================================================
# Shutdown event
# ============================================================
@app.on_event("shutdown")
async def shutdown_event():
    """
    Execute on application shutdown.
    """
    print("\n" + "=" * 60)
    print("🛑 Customify Core API shutting down...")
    print("=" * 60)

# ============================================================
# Future: Register routers here
# ============================================================
# from app.presentation.api.v1.endpoints import auth, designs, orders
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
# app.include_router(designs.router, prefix="/api/v1/designs", tags=["Designs"])
# app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
