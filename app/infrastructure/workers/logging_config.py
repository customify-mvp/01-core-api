"""Logging configuration for Celery workers."""

import logging
from app.config import settings


def setup_worker_logging():
    """
    Configure logging for Celery workers.
    
    Sets up:
    - INFO level for DEBUG mode, WARNING for production
    - Formatted timestamps and log levels
    - Suppresses noisy Celery/Kombu logs
    
    Returns:
        logging.Logger: Configured logger for worker tasks
    """
    # Set log level based on environment
    log_level = logging.INFO if settings.DEBUG else logging.WARNING
    
    # Configure basic logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Suppress noisy loggers
    logging.getLogger('celery').setLevel(logging.WARNING)
    logging.getLogger('kombu').setLevel(logging.WARNING)
    logging.getLogger('amqp').setLevel(logging.WARNING)
    
    # Return logger for worker tasks
    return logging.getLogger('customify.workers')


# Global logger instance
logger = setup_worker_logging()
