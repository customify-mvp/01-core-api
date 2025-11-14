"""Celery application configuration."""

from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "customify_workers",
    broker=str(settings.REDIS_URL),  # Development: Redis, Production: SQS
    backend=f"db+{str(settings.DATABASE_URL).replace('+asyncpg', '')}",  # PostgreSQL
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
    
    # Task routing (queues)
    task_routes={
        "app.infrastructure.workers.tasks.render_design.*": {"queue": "high_priority"},
        "app.infrastructure.workers.tasks.send_email.*": {"queue": "default"},
    },
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Take 1 task at a time (better for long tasks)
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
    
    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3, "countdown": 5},  # Retry 3 times, wait 5s between
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # Max 10 minutes backoff
    task_retry_jitter=True,  # Add random jitter to prevent thundering herd
)

# Task annotations (per-task config overrides)
celery_app.conf.task_annotations = {
    "app.infrastructure.workers.tasks.render_design.render_design_preview": {
        "rate_limit": "10/m",  # Max 10 renders per minute
    },
    "app.infrastructure.workers.tasks.send_email.send_email": {
        "rate_limit": "50/m",  # Max 50 emails per minute
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f"Request: {self.request!r}")
    return {"status": "ok", "message": "Celery is working!"}
