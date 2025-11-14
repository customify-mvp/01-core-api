"""Rate limiting middleware using Redis."""

from fastapi import Request, HTTPException, status
from redis import Redis
from app.config import settings
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.redis = Redis.from_url(
                str(settings.REDIS_URL),
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis.ping()
            logger.info("Rate limiter initialized with Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {e}")
            self.redis = None
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int = 100,
        window: int = 60
    ) -> None:
        """
        Check rate limit using sliding window.
        
        Args:
            key: Unique identifier (user_id or IP)
            limit: Max requests per window
            window: Time window in seconds
        
        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # If Redis is unavailable, log but don't block
        if not self.redis:
            logger.warning("Rate limiter unavailable - allowing request")
            return
        
        current = int(time.time())
        window_key = f"rate_limit:{key}:{current // window}"
        
        try:
            # Increment counter
            count = self.redis.incr(window_key)
            
            # Set expiry on first request
            if count == 1:
                self.redis.expire(window_key, window * 2)  # 2x window for safety
            
            # Check limit
            if count > limit:
                retry_after = window - (current % window)
                logger.warning(
                    f"Rate limit exceeded for {key}: {count}/{limit}",
                    extra={"key": key, "count": count, "limit": limit}
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
            
            # Log if approaching limit (>80%)
            if count > limit * 0.8:
                logger.info(
                    f"Rate limit warning for {key}: {count}/{limit}",
                    extra={"key": key, "count": count, "limit": limit}
                )
                
        except HTTPException:
            # Re-raise rate limit exceptions
            raise
        except Exception as e:
            # Log error but don't block request if Redis operation fails
            logger.error(f"Rate limiter error: {e}", exc_info=True)


# Global instance
rate_limiter = RateLimiter()


async def rate_limit_dependency(
    request: Request,
    limit: int = 100,
    window: int = 60
):
    """
    Rate limit dependency for endpoints.
    
    Args:
        request: FastAPI request object
        limit: Max requests per window
        window: Time window in seconds
    
    Usage:
        @router.post("/designs", dependencies=[Depends(rate_limit_dependency)])
    """
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    
    if user:
        key = f"user:{user.id}"
    else:
        # Use IP for unauthenticated requests
        client_host = request.client.host if request.client else "unknown"
        key = f"ip:{client_host}"
    
    await rate_limiter.check_rate_limit(key, limit=limit, window=window)


def create_rate_limit_dependency(limit: int = 100, window: int = 60):
    """
    Factory for creating rate limit dependencies with custom limits.
    
    Args:
        limit: Max requests per window
        window: Time window in seconds
    
    Returns:
        Dependency function
    
    Usage:
        # Strict limit for expensive operations
        @router.post("/ai-generate", dependencies=[Depends(create_rate_limit_dependency(10, 60))])
        
        # Standard limit for regular endpoints
        @router.get("/designs", dependencies=[Depends(create_rate_limit_dependency(100, 60))])
    """
    async def rate_limit_func(request: Request):
        await rate_limit_dependency(request, limit=limit, window=window)
    
    return rate_limit_func
