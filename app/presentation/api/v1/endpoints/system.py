"""System endpoints (health checks, worker status, etc)."""

from fastapi import APIRouter
from app.infrastructure.workers.celery_app import celery_app

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        dict: API health status
    """
    return {
        "status": "ok",
        "message": "Customify Core API is running"
    }


@router.get("/worker-status")
async def worker_status():
    """
    Check Celery worker status.
    
    Returns detailed information about:
    - Active workers and their stats
    - Currently executing tasks
    - Registered task types
    - Broker URL
    
    Returns:
        dict: Worker status information
    """
    try:
        # Get Celery inspect interface
        inspect = celery_app.control.inspect()
        
        # Get worker information
        stats = inspect.stats()
        active = inspect.active()
        registered = inspect.registered()
        scheduled = inspect.scheduled()
        
        # Check if workers are available
        workers_available = bool(stats)
        
        return {
            "workers_available": workers_available,
            "workers": stats or {},
            "active_tasks": active or {},
            "scheduled_tasks": scheduled or {},
            "registered_tasks": registered or {},
            "broker": str(celery_app.conf.broker_url).split("@")[-1],  # Hide credentials
        }
    except Exception as e:
        return {
            "workers_available": False,
            "error": str(e),
            "message": "Failed to connect to Celery workers. Make sure worker service is running."
        }
