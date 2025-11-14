"""
Subscription repository implementation (Infrastructure layer).

Implements ISubscriptionRepository using SQLAlchemy 2.0 async.
"""

from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.subscription import Subscription
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.infrastructure.database.models.subscription_model import SubscriptionModel
from app.infrastructure.database.converters import subscription_converter


class SubscriptionRepositoryImpl(ISubscriptionRepository):
    """
    Subscription repository implementation using SQLAlchemy.
    
    Handles subscription persistence and queries.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create(self, subscription: Subscription) -> Subscription:
        """
        Create new subscription.
        
        Args:
            subscription: Subscription entity to persist
            
        Returns:
            Created subscription entity
            
        Raises:
            IntegrityError: If user already has a subscription (unique constraint)
        """
        model = subscription_converter.to_model(subscription)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return subscription_converter.to_entity(model)
    
    async def get_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """
        Get subscription by ID.
        
        Args:
            subscription_id: Subscription unique identifier
            
        Returns:
            Subscription entity if found, None otherwise
        """
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.id == subscription_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return subscription_converter.to_entity(model) if model else None
    
    async def get_by_user(self, user_id: str) -> Optional[Subscription]:
        """
        Get user's active subscription.
        
        Args:
            user_id: User unique identifier
            
        Returns:
            User's subscription if exists, None otherwise
        """
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return subscription_converter.to_entity(model) if model else None
    
    async def get_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Optional[Subscription]:
        """
        Get subscription by Stripe subscription ID.
        
        Useful for processing Stripe webhooks.
        
        Args:
            stripe_subscription_id: Stripe subscription identifier
            
        Returns:
            Subscription entity if found, None otherwise
        """
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.stripe_subscription_id == stripe_subscription_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return subscription_converter.to_entity(model) if model else None
    
    async def update(self, subscription: Subscription) -> Subscription:
        """
        Update existing subscription.
        
        Args:
            subscription: Subscription entity with updated fields
            
        Returns:
            Updated subscription entity
            
        Raises:
            ValueError: If subscription not found
        """
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.id == subscription.id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            raise ValueError(f"Subscription with id {subscription.id} not found")
        
        # Update model with entity data
        model = subscription_converter.to_model(subscription, model)
        await self.session.flush()
        await self.session.refresh(model)
        
        return subscription_converter.to_entity(model)
    
    async def delete(self, subscription_id: str) -> bool:
        """
        Delete subscription (hard delete).
        
        Args:
            subscription_id: Subscription unique identifier
            
        Returns:
            True if subscription was deleted, False if not found
        """
        stmt = delete(SubscriptionModel).where(
            SubscriptionModel.id == subscription_id
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
