"""Global exception handler middleware."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

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


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Convert domain exceptions to HTTP responses.
    
    This middleware catches domain exceptions and converts them
    to appropriate HTTP status codes.
    
    Args:
        request: FastAPI request object
        exc: Exception raised
    
    Returns:
        JSONResponse with appropriate status code and error detail
    """
    
    # Authentication errors → 401
    if isinstance(exc, (InvalidCredentialsError, UserNotFoundError)):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)}
        )
    
    # Already exists → 409
    if isinstance(exc, EmailAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)}
        )
    
    # Inactive user → 403
    if isinstance(exc, (InactiveUserError, InactiveSubscriptionError)):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)}
        )
    
    # Quota exceeded → 402 Payment Required
    if isinstance(exc, QuotaExceededError):
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={"detail": str(exc)}
        )
    
    # Not found → 404
    if isinstance(exc, DesignNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)}
        )
    
    # Unauthorized access → 403
    if isinstance(exc, UnauthorizedDesignAccessError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)}
        )
    
    # Validation errors → 400
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)}
        )
    
    # Unknown error → 500
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
