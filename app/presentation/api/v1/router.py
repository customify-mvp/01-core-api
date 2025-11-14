"""Main API v1 router."""

from fastapi import APIRouter
from app.presentation.api.v1.endpoints import auth, designs

api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(designs.router)
