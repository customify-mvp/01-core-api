"""Domain repositories - Abstract interfaces."""

from .user_repository import IUserRepository
from .subscription_repository import ISubscriptionRepository
from .design_repository import IDesignRepository

__all__ = [
    "IUserRepository",
    "ISubscriptionRepository",
    "IDesignRepository",
]
