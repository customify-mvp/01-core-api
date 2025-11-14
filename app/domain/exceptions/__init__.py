"""Domain exceptions package."""

from app.domain.exceptions.auth_exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    UserNotFoundError,
    InactiveUserError,
    InvalidTokenError,
)
from app.domain.exceptions.design_exceptions import (
    DesignError,
    DesignNotFoundError,
    UnauthorizedDesignAccessError,
    InvalidDesignDataError,
)
from app.domain.exceptions.subscription_exceptions import (
    SubscriptionError,
    QuotaExceededError,
    InactiveSubscriptionError,
    SubscriptionNotFoundError,
)

__all__ = [
    # Auth exceptions
    "AuthenticationError",
    "InvalidCredentialsError",
    "EmailAlreadyExistsError",
    "UserNotFoundError",
    "InactiveUserError",
    "InvalidTokenError",
    # Design exceptions
    "DesignError",
    "DesignNotFoundError",
    "UnauthorizedDesignAccessError",
    "InvalidDesignDataError",
    # Subscription exceptions
    "SubscriptionError",
    "QuotaExceededError",
    "InactiveSubscriptionError",
    "SubscriptionNotFoundError",
]
