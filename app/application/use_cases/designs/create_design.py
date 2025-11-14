"""Use case: Create design."""

from typing import Optional
from app.domain.entities.design import Design
from app.domain.entities.subscription import Subscription
from app.domain.repositories.design_repository import IDesignRepository
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.domain.exceptions.subscription_exceptions import (
    QuotaExceededError,
    InactiveSubscriptionError,
    SubscriptionNotFoundError,
)


class CreateDesignUseCase:
    """
    Use case: Create design.
    
    Business Rules:
    1. Check user has active subscription
    2. Check user hasn't exceeded quota
    3. Create design entity
    4. Increment subscription usage counter
    5. Queue render job (TODO: implement later)
    """
    
    def __init__(
        self,
        design_repo: IDesignRepository,
        subscription_repo: ISubscriptionRepository,
    ):
        self.design_repo = design_repo
        self.subscription_repo = subscription_repo
    
    async def execute(
        self,
        user_id: str,
        product_type: str,
        design_data: dict,
        use_ai_suggestions: bool = False,
    ) -> Design:
        """
        Create new design.
        
        Args:
            user_id: User ID
            product_type: Product type (t-shirt, mug, etc)
            design_data: Design data (text, font, color, etc)
            use_ai_suggestions: Whether to use AI suggestions
        
        Returns:
            Created design entity
        
        Raises:
            SubscriptionNotFoundError: User has no subscription
            InactiveSubscriptionError: Subscription is not active
            QuotaExceededError: User exceeded design quota
        """
        # 1. Get user subscription
        subscription = await self.subscription_repo.get_by_user(user_id)
        if subscription is None:
            raise SubscriptionNotFoundError(f"User {user_id} has no subscription")
        
        # 2. Check subscription is active
        if not subscription.is_active():
            raise InactiveSubscriptionError("Subscription is not active")
        
        # 3. Check quota available
        if not subscription.has_quota():
            raise QuotaExceededError(
                f"Design quota exceeded ({subscription.designs_this_month}/{subscription.designs_limit})"
            )
        
        # 4. Create design entity
        design = Design.create(
            user_id=user_id,
            product_type=product_type,
            design_data=design_data
        )
        
        # 5. Validate design data
        design.validate()
        
        # 6. Persist design
        created_design = await self.design_repo.create(design)
        
        # 7. Increment subscription usage
        subscription.increment_usage()
        await self.subscription_repo.update(subscription)
        
        # TODO: Queue render job (Celery task)
        # from app.infrastructure.workers.tasks.render_design import render_design_preview
        # render_design_preview.delay(created_design.id)
        
        return created_design
