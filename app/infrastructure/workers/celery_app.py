"""Celery application configuration."""

from celery import Celery
from app.config import settings

# Create Celery app with explicit task includes
celery_app = Celery(
    "customify_workers",
    broker=str(settings.REDIS_URL),  # Development: Redis, Production: SQS
    backend=settings.celery_database_url,  # PostgreSQL sync driver
    include=[
        "app.infrastructure.workers.tasks.render_design",
        "app.infrastructure.workers.tasks.send_email",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit (warning)
    
    # Result backend
    result_expires=86400,  # Results expire after 24 hours
    result_extended=True,
    
    # Broker connection
    broker_connection_retry_on_startup=True,  # Fix deprecation warning
    
    # Task routing - USE EXACT TASK NAMES, NOT MODULE PATHS
    task_routes={
        "render_design_preview": {"queue": "high_priority"},
        "send_email": {"queue": "default"},
        "debug_task": {"queue": "default"},
    },
    
    # Default queue for tasks without specific routing
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Take 1 task at a time (better for long tasks)
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
    
    # Task acknowledgment - CRITICAL for reliability
    task_acks_late=True,  # Acknowledge after task completes (not when received)
    task_reject_on_worker_lost=True,  # Reject task if worker crashes
    
    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3, "countdown": 5},  # Retry 3 times, wait 5s between
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # Max 10 minutes backoff
    task_retry_jitter=True,  # Add random jitter to prevent thundering herd
)

# Task annotations (per-task config overrides)
celery_app.conf.task_annotations = {
    "render_design_preview": {
        "rate_limit": "10/m",  # Max 10 renders per minute
    },
    "send_email": {
        "rate_limit": "50/m",  # Max 50 emails per minute
    },
}


@celery_app.task(bind=True, name="debug_task")
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f"🔍 Debug task running! Request: {self.request!r}")
    return {"status": "ok", "message": "Celery is working!"}
