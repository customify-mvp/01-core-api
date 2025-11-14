"""
Subscription converter - Convert between SubscriptionModel and Subscription entity.

Handles conversion including enum types (PlanType, SubscriptionStatus).
"""

from app.domain.entities.subscription import Subscription, PlanType, SubscriptionStatus
from app.infrastructure.database.models.subscription_model import SubscriptionModel


def to_entity(model: SubscriptionModel) -> Subscription:
    """
    Convert SubscriptionModel (SQLAlchemy) to Subscription entity (Domain).
    
    Args:
        model: SQLAlchemy SubscriptionModel instance
        
    Returns:
        Domain Subscription entity
    """
    return Subscription(
        id=model.id,
        user_id=model.user_id,
        plan=PlanType(model.plan),  # Convert string to enum
        status=SubscriptionStatus(model.status),  # Convert string to enum
        stripe_customer_id=model.stripe_customer_id,
        stripe_subscription_id=model.stripe_subscription_id,
        current_period_start=model.current_period_start,
        current_period_end=model.current_period_end,
        designs_this_month=model.designs_this_month,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_model(entity: Subscription, model: SubscriptionModel = None) -> SubscriptionModel:
    """
    Convert Subscription entity (Domain) to SubscriptionModel (SQLAlchemy).
    
    Args:
        entity: Domain Subscription entity
        model: Existing SubscriptionModel to update (optional)
        
    Returns:
        SQLAlchemy SubscriptionModel instance
    """
    if model is None:
        model = SubscriptionModel()
    
    model.id = entity.id
    model.user_id = entity.user_id
    model.plan = entity.plan.value  # Convert enum to string
    model.status = entity.status.value  # Convert enum to string
    model.stripe_customer_id = entity.stripe_customer_id
    model.stripe_subscription_id = entity.stripe_subscription_id
    model.current_period_start = entity.current_period_start
    model.current_period_end = entity.current_period_end
    model.designs_this_month = entity.designs_this_month
    model.created_at = entity.created_at
    model.updated_at = entity.updated_at
    
    return model
