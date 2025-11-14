"""Structured logging configuration for production-ready observability."""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variables for request tracing
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    JSON structured formatter for machine-readable logs.
    
    Outputs logs in JSON format compatible with log aggregators
    like CloudWatch, Datadog, ELK stack, etc.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        
        # Base log data
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add context from ContextVars
        request_id = request_id_context.get()
        user_id = user_id_context.get()
        
        if request_id:
            log_data["request_id"] = request_id
        
        if user_id:
            log_data["user_id"] = user_id
        
        # Add extra fields from record
        if hasattr(record, "user_id") and not user_id:
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "request_id") and not request_id:
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        
        if hasattr(record, "method"):
            log_data["method"] = record.method
        
        if hasattr(record, "path"):
            log_data["path"] = record.path
        
        # Add any other custom fields from extra dict
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'user_id', 'request_id',
                          'duration_ms', 'status_code', 'method', 'path']:
                if not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data, default=str)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    
    Outputs colorized, easy-to-read logs for local development.
    """
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Base message
        message = f"{color}[{record.levelname:8}]{reset} {timestamp} - {record.name} - {record.getMessage()}"
        
        # Add context if available
        request_id = request_id_context.get() or getattr(record, 'request_id', None)
        user_id = user_id_context.get() or getattr(record, 'user_id', None)
        
        context_parts = []
        if request_id:
            context_parts.append(f"req={request_id[:8]}")
        if user_id:
            context_parts.append(f"user={user_id[:8]}")
        
        if context_parts:
            message += f" [{', '.join(context_parts)}]"
        
        # Add exception info
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logging(
    app_name: str = "customify-api",
    level: str = "INFO",
    use_json: bool = False
) -> logging.Logger:
    """
    Setup structured logging for the application.
    
    Args:
        app_name: Application name for logger
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: If True, use JSON formatter (for production).
                 If False, use human-readable formatter (for development).
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logging("customify-api", "INFO", use_json=True)
        >>> logger.info("User registered", extra={"user_id": "123", "email": "user@example.com"})
    """
    
    # Get root logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Choose formatter based on environment
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = HumanReadableFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger


# Global logger instance (configured by app at startup)
logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """
    Get the global logger instance.
    
    Returns:
        Logger instance
    
    Raises:
        RuntimeError: If logger not initialized
    """
    global logger
    if logger is None:
        raise RuntimeError("Logger not initialized. Call setup_logging() first.")
    return logger


def init_logger(app_name: str = "customify-api", level: str = "INFO", use_json: bool = False):
    """
    Initialize the global logger.
    
    Should be called once at application startup.
    
    Args:
        app_name: Application name
        level: Logging level
        use_json: Use JSON formatter (True for production)
    """
    global logger
    logger = setup_logging(app_name, level, use_json)
