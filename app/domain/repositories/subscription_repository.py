"""
Subscription repository interface (Domain layer).

Defines contract for subscription persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.subscription import Subscription


class ISubscriptionRepository(ABC):
    """
    Subscription repository interface.
    
    Handles subscription CRUD and query operations.
    """
    
    @abstractmethod
    async def create(self, subscription: Subscription) -> Subscription:
        """
        Create new subscription.
        
        Args:
            subscription: Subscription entity to persist
            
        Returns:
            Created subscription entity
            
        Raises:
            Exception: If user already has a subscription
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """
        Get subscription by ID.
        
        Args:
            subscription_id: Subscription unique identifier
            
        Returns:
            Subscription entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: str) -> Optional[Subscription]:
        """
        Get user's active subscription.
        
        Args:
            user_id: User unique identifier
            
        Returns:
            User's subscription if exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Optional[Subscription]:
        """
        Get subscription by Stripe subscription ID.
        
        Useful for webhook processing.
        
        Args:
            stripe_subscription_id: Stripe subscription identifier
            
        Returns:
            Subscription entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, subscription: Subscription) -> Subscription:
        """
        Update existing subscription.
        
        Args:
            subscription: Subscription entity with updated fields
            
        Returns:
            Updated subscription entity
            
        Raises:
            Exception: If subscription not found
        """
        pass
    
    @abstractmethod
    async def delete(self, subscription_id: str) -> bool:
        """
        Delete subscription (hard delete).
        
        Args:
            subscription_id: Subscription unique identifier
            
        Returns:
            True if subscription was deleted, False if not found
        """
        pass
